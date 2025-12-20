import os
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from database import db
from google_calendar import calendar_manager

class SchedulingAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.conversation_history = []
    
    def get_context(self, query_type='general'):
        """Build context from database and calendar"""
        context = {
            'timestamp': datetime.now().isoformat(),
            'query_type': query_type
        }
        # Get student feedback by event_name
        feedback_by_event_query = """
            SELECT e.event_name, a.student_id, a.student_feedback, a.check_in_time
            FROM Attendance a
            JOIN Events e ON a.event_id = e.event_id
            WHERE a.student_feedback IS NOT NULL AND a.student_feedback != ''
            ORDER BY a.check_in_time DESC
            LIMIT 20
        """
        feedback_by_event_rows = db.execute_query(feedback_by_event_query)
        context['feedback_by_event_name'] = [
            {
                'event_name': row['event_name'],
                'student_id': row['student_id'],
                'feedback': row['student_feedback'],
                'check_in_time': str(row['check_in_time'])
            }
            for row in feedback_by_event_rows
        ]
        
        # Get all students
        students = db.get_all_students()
        context['total_students'] = len(students)
        context['students_by_program'] = {}
        print("Jimmy's students: ", students)
        
        # for student in students:
        #     program = student['program']
        #     if program not in context['students_by_program']:
        #         context['students_by_program'][program] = 0
        #         print("Jimmy's new program added: ", program)
        #     context['students_by_program'][program] += 1
            
        
        # Get weekly schedule
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        context['weekly_schedule'] = {}
        
        for day in days:
            schedule = db.get_schedule_by_day(day)
            context['weekly_schedule'][day] = [
                {
                    'course': s['course_name'],
                    'program': s['program'],
                    'start': str(s['start_time']),
                    'end': str(s['end_time']),
                    'students': s['no_students']
                }
                for s in schedule
            ]
        
        # Get recent events
        recent_events_query = """
            SELECT * FROM Events 
            WHERE event_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND DATE_ADD(CURDATE(), INTERVAL 1 MONTH)
            ORDER BY event_date ASC, start_time ASC 
        """
        recent_events = db.execute_query(recent_events_query)
        context['recent_events'] = []
        
        for event in recent_events:
            attendance = db.get_event_attendance(event['event_id'])
            context['recent_events'].append({
                'name': event['event_name'],
                'date': event['event_date'].strftime('%Y-%m-%d'),
                'time': f"{event['start_time']}-{event['end_time']}",
                'attendance': len(attendance),
                'programs': json.loads(event.get('target_programs', '[]'))
            })
        
        # Get calendar events
        try:
            calendar_events = calendar_manager.get_upcoming_events(days=14)
            context['upcoming_calendar_events'] = [
                {
                    'name': e['summary'],
                    'start': e['start'].get('dateTime', e['start'].get('date')),
                    'end': e['end'].get('dateTime', e['end'].get('date'))
                }
                for e in calendar_events[:10]
            ]
        except:
            context['upcoming_calendar_events'] = []
        
        # Get recent student feedback from Attendance table
        feedback_query = """
            SELECT student_id, event_id, student_feedback, check_in_time
            FROM Attendance
            WHERE student_feedback IS NOT NULL AND student_feedback != ''
            ORDER BY check_in_time DESC
            LIMIT 20
        """
        feedback_rows = db.execute_query(feedback_query)
        context['recent_feedback'] = [
            {
                'student_id': row['student_id'],
                'event_id': row['event_id'],
                'feedback': row['student_feedback'],
                'check_in_time': str(row['check_in_time'])
            }
            for row in feedback_rows
        ]
        return context
    
    def find_optimal_time_slots(self, programs=None, duration_hours=2):
        """Find time slots with maximum student availability"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        time_slots = []
        #print("Finding optimal time slots...", programs, duration_hours)
        # Check time slots from 8 AM to 10 PM
        for day in days:
            for hour in range(8, 22):
                start_time = f"{hour:02d}:00:00"
                end_time = f"{hour + duration_hours:02d}:00:00"
                
                if hour + duration_hours > 22:
                    continue
                
                availability = db.get_available_students_count(
                    # day, start_time, end_time, programs[0] if programs else None
                    day, start_time, end_time, programs if programs else None

                )
                
                time_slots.append({
                    'day': day,
                    'start_time': start_time,
                    'end_time': end_time,
                    'availability': availability
                })
        
        # Sort by availability percentage
        time_slots.sort(key=lambda x: x['availability']['availability_percentage'], reverse=True)
        print(time_slots, "time slots")
        return time_slots[:5]  # Return top 5 slots
    
    def analyze_availability(self, day, start_time, end_time, programs=None):
        """Analyze student availability for a specific time slot"""
        program_filter = programs[0] if programs else None
        availability = db.get_available_students_count(day, start_time, end_time, program_filter)
        
        # Get conflicting classes
        conflicts = db.get_schedule_conflicts(start_time, end_time, day)
        
        return {
            'availability': availability,
            'conflicts': [
                {
                    'course': c['course_name'],
                    'program': c['program'],
                    'time': f"{c['start_time']}-{c['end_time']}",
                    'students': c['no_students']
                }
                for c in conflicts
            ]
        }
    
    def process_query(self, user_query, programs=None):
        """Process user query with AI agent"""
    
        # Get context
        context = self.get_context()
        print("Jimmy's programs in process_query: ", programs)
        
        # Build system prompt
        system_prompt = f"""You are an intelligent event scheduling assistant for a university.

Current Context:
{json.dumps(context, indent=2, default=str)}

Your capabilities:
1. Analyze class schedules and find optimal event times except Saturday and Sunday availabilities
2. Calculate student availability percentages
3. Provide insights on past event attendance
4. Suggest best times based on program filters
5. Consider conflicts with existing classes and calendar events

Always provide:
- Specific time slot recommendations
- Availability percentages, calculate percentage for that slot
- Reasoning behind suggestions
- Alternative options if needed

Be concise and data-driven in your responses."""

        # Add user message to conversation
        self.conversation_history.append({
            "role": "user",
            "content": user_query
        })
        
        # Get AI response
        try:
            # Prepare prompt from conversation history
            prompt = system_prompt + "\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
            response = self.model.generate_content(prompt)
            assistant_message = response.text if hasattr(response, 'text') else str(response)
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            # Keep only last 10 messages to manage context
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            return {
                'success': True,
                'response': assistant_message,
                'context': context
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error: {str(e)}"
            }
    
    def suggest_event_time(self, event_name, event_date, programs=None, duration_hours=2):
        """Use AI to suggest optimal event time"""
        # Find optimal slots
        optimal_slots = self.find_optimal_time_slots(programs, duration_hours)
        
        # Build query for AI
        query = f"""I need to schedule an event called "{event_name}" for {event_date} and {duration_hours} hours.
        
Target programs: {', '.join(programs) if programs else 'All students'}

Here are the top 2 to 5 available time slots:

{json.dumps(optimal_slots, indent=2, default=str)}

Please analyze these options and recommend the best time slot, explaining your reasoning based on:
1. Student availability percentage, calculate percentage for that slot
2. Day of the week considerations
3. Time of day preferences
4. Any potential conflicts

Provide your top recommendation and one alternative. It is not necessary that the event be scheduled in the top slot; consider all options except Saturday and Sunday availabilities.

Be concise and data-driven in your responses."""

        return self.process_query(query, programs)
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

# Singleton instance
agent = SchedulingAgent()

# Test function
def test_agent():
    """Test the AI agent"""
    print("🤖 Testing AI Scheduling Agent\n")
    
    # Test 1: Ask about availability
    result = agent.process_query(
        "What percentage of MBA students are available on Monday at 2 PM?"
    )
    print("Query 1:", result['response'])
    print("\n" + "="*50 + "\n")
    
    # Test 2: Suggest event time
    result = agent.suggest_event_time(
        "Leadership Workshop",
        programs=['MBA', 'Graduate'],
        duration_hours=2
    )
    print("Query 2:", result['response'])

if __name__ == '__main__':
    # Connect to database first
    db.connect()
    calendar_manager.authenticate()
    
    test_agent()