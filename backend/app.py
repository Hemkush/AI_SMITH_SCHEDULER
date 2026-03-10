from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import logging

from database import db
from google_calendar import calendar_manager
from mcp_server import agent
from qr_generator import qr_generator

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
if cors_origins.strip() == '*':
    CORS(app)
else:
    CORS(app, origins=[origin.strip() for origin in cors_origins.split(',') if origin.strip()])

# CORS(app, resources={
#     r"/api/*": {
#         "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
#         "methods": ["GET", "POST", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type"]
#     }
# })

# Initialize connections on startup
@app.before_request
def before_request():
    if not db.connection:
        db.connect()

# ============================================
# STUDENT ENDPOINTS
# ============================================

@app.route('/api/studentsAll', methods=['GET'])
def get_students():
    """Get all students, optionally filtered by program"""
    program = request.args.get('program')
    students = db.get_all_students(program)
    return jsonify({'success': True, 'students': students})

@app.route('/api/students', methods=['POST'])
def add_student():
    """Add a new student"""
    data = request.json
    
        # ...existing code...
    try:
        query = """
            INSERT INTO Students (name, email, program, term)
            VALUES (%s, %s, %s, %s)
        """
        student_id = db.execute_update(query, (
            data['name'],
    # ...existing code...
            data['email'],
            data['program'],
            data.get('term', 'Fall 2024')
        ))
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'message': 'Student added successfully'
    # ...existing code...
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SCHEDULE ENDPOINTS
# ============================================

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get class schedule"""
    day = request.args.get('day')
    
    def serialize_timedelta(obj):
        if isinstance(obj, timedelta):
            return str(obj)
        return obj

    def convert_timedeltas(data):
        if isinstance(data, dict):
            return {k: convert_timedeltas(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [convert_timedeltas(item) for item in data]
        else:
            return serialize_timedelta(data)

    if day:
        schedule = db.get_schedule_by_day(day)
        schedule = convert_timedeltas(schedule)
        return jsonify({'success': True, 'schedule': schedule})
    else:
        # Get entire week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        schedule = {}
        for d in days:
            schedule[d] = db.get_schedule_by_day(d)
        schedule = convert_timedeltas(schedule)
        return jsonify({'success': True, 'schedule': schedule})

# @app.route('/api/schedule/conflicts', methods=['POST'])
# def check_conflicts():
#     """Check for schedule conflicts"""
#     data = request.json
    
#     conflicts = db.get_schedule_conflicts(
#         data['start_time'],
#         data['end_time'],
#         data['day']
#     )

#     def serialize_timedelta(obj):
#         if isinstance(obj, timedelta):
#             return str(obj)
#         return obj

#     def convert_timedeltas(data):
#         if isinstance(data, dict):
#             return {k: convert_timedeltas(v) for k, v in data.items()}
#         elif isinstance(data, list):
#             return [convert_timedeltas(item) for item in data]
#         else:
#             return serialize_timedelta(data)

#     conflicts = convert_timedeltas(conflicts)
#     return jsonify({'success': True, 'conflicts': conflicts})

@app.route('/api/schedule/conflicts', methods=['POST'])
def check_conflicts():
    """Check for schedule and event conflicts"""
    data = request.json
    
    try:
        conflicts = db.get_schedule_conflicts(
            data['start_time'],
            data['end_time'],
            data['day'],
            data.get('event_date'),  # Optional: date for event conflicts
            data.get('exclude_event_id')  # Optional: exclude specific event
        )

        # Convert timedelta objects to strings
        def serialize_timedelta(obj):
            if isinstance(obj, timedelta):
                return str(obj)
            return obj

        def convert_timedeltas(data):
            if isinstance(data, dict):
                return {k: convert_timedeltas(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_timedeltas(item) for item in data]
            else:
                return serialize_timedelta(data)

        conflicts = convert_timedeltas(conflicts)
        
        # Serialize the results
        serialized_conflicts = {
            'class_conflicts': conflicts['class_conflicts'],
            'event_conflicts': conflicts['event_conflicts'],
            'total_conflicts': conflicts['total_conflicts']
        }
        
        return jsonify({
            'success': True,
            'conflicts': serialized_conflicts
        })
    
    except Exception as e:
        logger.error(f"Error checking conflicts: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/schedule/availability', methods=['POST'])
# def check_availability():
#     """Calculate student availability for a time slot"""
#     data = request.json
    
#     availability = db.get_available_students_count(
#         data['day'],
#         data['start_time'],
#         data['end_time'],
#         data.get('program')
#         #program if data.get('program') else None
#     )

#     conflicts = db.get_schedule_conflicts(
#         data['start_time'],
#         data['end_time'],
#         data['day']
#     )

#     def serialize_timedelta(obj):
#         if isinstance(obj, timedelta):
#             return str(obj)
#         return obj

#     def convert_timedeltas(data):
#         if isinstance(data, dict):
#             return {k: convert_timedeltas(v) for k, v in data.items()}
#         elif isinstance(data, list):
#             return [convert_timedeltas(item) for item in data]
#         else:
#             return serialize_timedelta(data)

#     availability = convert_timedeltas(availability)
#     conflicts = convert_timedeltas(conflicts)

#     return jsonify({
#         'success': True,
#         'availability': availability,
#         'conflicts': conflicts
#     })
@app.route('/api/schedule/availability', methods=['POST'])
def check_availability():
    """Calculate student availability for a time slot"""
    data = request.json
    print(data, "Jimmy's data in app.py")
    try:
        programs = data.get('programs', [])
        if isinstance(programs, str):
            programs = [programs]
        
        # Get availability
        availability = db.get_available_students_count(
            data['day'],
            data['start_time'],
            data['end_time'],
            programs if programs else None
        )
        
        # Get all conflicts (classes + events)
        conflicts = db.get_schedule_conflicts(
            data['start_time'],
            data['end_time'],
            data['day'],
            data.get('event_date')  # Include event date if provided
        )
        
        # Filter class conflicts by programs if specified
        class_conflicts = conflicts['class_conflicts']
        if programs:
            class_conflicts = [c for c in class_conflicts if c['program'] in programs]

        # Serialize timedelta objects
        def serialize_timedelta(obj):
           if isinstance(obj, timedelta):
             return str(obj)
           return obj

        def convert_timedeltas(data):
           if isinstance(data, dict):
            return {k: convert_timedeltas(v) for k, v in data.items()}
           elif isinstance(data, list):
            return [convert_timedeltas(item) for item in data]
           else:
            return serialize_timedelta(data)

        availability = convert_timedeltas(availability)
        class_conflicts = convert_timedeltas(class_conflicts)
        conflicts['event_conflicts'] = convert_timedeltas(conflicts['event_conflicts'])
        
        return jsonify({
            'success': True,
            'availability': availability,
            'class_conflicts': class_conflicts,
            'event_conflicts': conflicts['event_conflicts'],
            'total_conflicts': len(class_conflicts) + len(conflicts['event_conflicts'])
        })
    
    except Exception as e:
        logger.error(f"Error in check_availability: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# EVENT ENDPOINTS
# ============================================

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events"""
    query = """
        SELECT e.*, 
               (SELECT COUNT(*) FROM Attendance a WHERE a.event_id = e.event_id) as attendance_count
        FROM Events e
        WHERE e.event_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND DATE_ADD(CURDATE(), INTERVAL 1 MONTH)
        ORDER BY e.event_date ASC, e.start_time ASC
    """
    
    events = db.execute_query(query)

    # Parse target_programs JSON
    for event in events:
        event['target_programs'] = json.loads(event.get('target_programs', '[]'))
        event['registration_link'] = event.get('registration_link', '')

    def serialize_timedelta(obj):
        if isinstance(obj, timedelta):
            return str(obj)
        return obj

    def convert_timedeltas(data):
        if isinstance(data, dict):
            return {k: convert_timedeltas(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [convert_timedeltas(item) for item in data]
        else:
            return serialize_timedelta(data)

    events = convert_timedeltas(events)
    return jsonify({'success': True, 'events': events})

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get specific event with attendance"""
    query = "SELECT * FROM Events WHERE event_id = %s"
    event = db.execute_query(query, (event_id,))
    
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    event = event[0]
    event['target_programs'] = json.loads(event.get('target_programs', '[]'))
    # Add registration_link to response
    event['registration_link'] = event.get('registration_link', '')

    # Get attendance
    attendance = db.get_event_attendance(event_id)
    event['attendance'] = attendance

    def serialize_timedelta(obj):
        if isinstance(obj, timedelta):
            return str(obj)
        return obj

    def convert_timedeltas(data):
        if isinstance(data, dict):
            return {k: convert_timedeltas(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [convert_timedeltas(item) for item in data]
        else:
            return serialize_timedelta(data)

    event = convert_timedeltas(event)
    return jsonify({'success': True, 'event': event})

@app.route('/api/events', methods=['POST'])
def create_event():
    """Create a new event"""
    data = request.json
    
    try:
        # Add event to database
        event_data = {
            'event_name': data['event_name'],
            'event_date': data['event_date'],
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'location': data.get('location', ''),
            'description': data.get('description', ''),
            'target_programs': json.dumps(data.get('target_programs', []))
        }
        print(event_data, "Jimmy's event_data")
        
        event_id = db.add_event(event_data)
        print(event_id, "Jimmy's event_id")
        
        # Add to Google Calendar
        calendar_event = calendar_manager.format_event_for_calendar(
            data['event_name'],
            data['event_date'],
            data['start_time'],
            data['end_time'],
            data.get('location', ''),
            data.get('description', '')
        )
        print(calendar_event, "Jimmy's calendar_event")
        
        calendar_id = calendar_manager.create_event(calendar_event)
        
        # Update database with calendar ID
        if calendar_id:
            update_query = "UPDATE Events SET google_calendar_id = %s WHERE event_id = %s"
            db.execute_update(update_query, (calendar_id, event_id))
        
        # Generate QR code and registration link
        base_url = request.host_url.rstrip('/')
        registration_url = f"{base_url}/register/{event_id}"
        qr_path = qr_generator.generate_event_qr(event_id, registration_url)

        # Update database with QR path and registration link
        update_query = "UPDATE Events SET qr_code_path = %s, registration_link = %s WHERE event_id = %s"
        db.execute_update(update_query, (qr_path, registration_url, event_id))

        return jsonify({
            'success': True,
            'event_id': event_id,
            'google_calendar_id': calendar_id,
            'qr_code_path': qr_path,
            'registration_link': registration_url,
            'message': 'Event created successfully'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event"""
    try:
        # Get event details
        event = db.execute_query("SELECT * FROM Events WHERE event_id = %s", (event_id,))
        
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        event = event[0]
        
        # Delete from Google Calendar
        if event.get('google_calendar_id'):
            calendar_manager.delete_event(event['google_calendar_id'])
        
        # Delete QR code file
        if event.get('qr_code_path') and os.path.exists(event['qr_code_path']):
            os.remove(event['qr_code_path'])
        
        # Delete from database
        db.execute_update("DELETE FROM Events WHERE event_id = %s", (event_id,))
        
        return jsonify({'success': True, 'message': 'Event deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ATTENDANCE ENDPOINTS
# ============================================

@app.route('/api/attendance/<int:event_id>', methods=['GET'])
def get_attendance(event_id):
    """Get attendance for an event"""
    attendance = db.get_event_attendance(event_id)
    return jsonify({'success': True, 'attendance': attendance})

@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    """Record attendance (used by QR code scan)"""
    data = request.json
    
    try:
        event_id = data['event_id']
        student_id = data['student_id']
        student_feedback = data.get('student_feedback', None)
        db.record_attendance(event_id, student_id, student_feedback)
        return jsonify({
            'success': True,
            'message': 'Attendance recorded successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# QR CODE ENDPOINT
# ============================================

@app.route('/api/qr/<int:event_id>', methods=['GET'])
def get_qr_code(event_id):
    """Get QR code image for an event"""
    query = "SELECT qr_code_path FROM Events WHERE event_id = %s"
    result = db.execute_query(query, (event_id,))
    
    if not result or not result[0]['qr_code_path']:
        return jsonify({'success': False, 'error': 'QR code not found'}), 404
    
    qr_path = result[0]['qr_code_path']
    
    if not os.path.exists(qr_path):
        return jsonify({'success': False, 'error': 'QR code file not found'}), 404
    
    return send_file(qr_path, mimetype='image/png')

# ============================================
# AI AGENT ENDPOINTS
# ============================================

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat with AI scheduling assistant"""
    data = request.json
    user_query = data.get('query', '')
    programs = data.get('programs', None)
    print("Jimmy's programs in app.py: ", programs)
    
    if not user_query:
        return jsonify({'success': False, 'error': 'Query is required'}), 400
    
    try:
        result = agent.process_query(user_query, programs)
        print("Jimmy's result in app.py: ", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': f"I encountered an error: {str(e)}"
        }), 500

@app.route('/api/ai/suggest-time', methods=['POST'])
def ai_suggest_time():
    """Get AI suggestion for optimal event time"""
    data = request.json
    
    try:
        result = agent.suggest_event_time(
            event_name=data.get('event_name', 'Event'),
            programs=data.get('programs'),
            event_date=data.get('event_date'),
            duration_hours=data.get('duration_hours', 2)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/reset', methods=['POST'])
def ai_reset():
    """Reset AI conversation history"""
    agent.reset_conversation()
    return jsonify({'success': True, 'message': 'Conversation reset'})

# ============================================
# CALENDAR SYNC ENDPOINT
# ============================================

@app.route('/api/calendar/sync', methods=['POST'])
def sync_calendar():
    """Sync database events to Google Calendar"""
    try:
        # synced_count = calendar_manager.sync_database_events_to_calendar(db)
        synced_count = calendar_manager.sync_calendar_events_to_database(db)
        return jsonify({
            'success': True,
            'synced_count': synced_count,
            'message': f'Synced {synced_count} events to Google Calendar'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/events', methods=['GET'])
def get_calendar_events():
    """Get events from Google Calendar"""
    days = int(request.args.get('days', 7))
    
    try:
        events = calendar_manager.get_upcoming_events(days)
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# REGISTRATION PAGE (for QR code)
# ============================================

@app.route('/register/<int:event_id>', methods=['GET'])
def registration_page(event_id):
    """Registration landing page (simple HTML)"""
    query = "SELECT * FROM Events WHERE event_id = %s"
    event = db.execute_query(query, (event_id,))
    
    if not event:
        return "<h1>Event not found</h1>", 404
    
    event = event[0]
    registration_link = event.get('registration_link', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Event Registration - {event['event_name']}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; }}
            .info {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            input, select {{ width: 100%; padding: 10px; margin: 10px 0; }}
            button {{ background: #4CAF50; color: white; padding: 15px; border: none; width: 100%; cursor: pointer; }}
            button:hover {{ background: #45a049; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
            .link {{ margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>{event['event_name']}</h1>
        <div class="info">
            <p><strong>Date:</strong> {event['event_date']}</p>
            <p><strong>Time:</strong> {event['start_time']} - {event['end_time']}</p>
            <p><strong>Location:</strong> {event.get('location', 'TBA')}</p>
        </div>
        <div class="link">
            <a href="{registration_link}" target="_blank">Register for this event</a>
        </div>
        <h2>Check In</h2>
        <form id="checkinForm">
            <input type="number" id="student_id" placeholder="Enter your Student ID" required>
            <textarea id="student_feedback" placeholder="Optional feedback (e.g. comments, suggestions)" rows="6" style="min-height:100px;width:100%;"></textarea>
            <button type="submit">Check In</button>
        </form>
        <div id="message"></div>
        <script>
            document.getElementById('checkinForm').onsubmit = async (e) => {{
                e.preventDefault();
                const studentId = document.getElementById('student_id').value;
                const studentFeedback = document.getElementById('student_feedback').value;
                const messageDiv = document.getElementById('message');
                try {{
                    // Record attendance directly using student ID and optional feedback
                    const res = await fetch('/api/attendance', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            event_id: {event_id},
                            student_id: studentId,
                            student_feedback: studentFeedback
                        }})
                    }});
                    const data = await res.json();
                    if (data.success) {{
                        messageDiv.innerHTML = '<p class="success">✅ Check-in successful! Thank you.</p>';
                        document.getElementById('checkinForm').reset();
                    }} else {{
                        messageDiv.innerHTML = '<p class="error">Error: ' + data.error + '</p>';
                    }}
                }} catch (error) {{
                    messageDiv.innerHTML = '<p class="error">Error: ' + error.message + '</p>';
                }}
            }};
        </script>
    </body>
    </html>
    """
    return html

# ============================================
# ANALYTICS ENDPOINT
# ============================================

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get system analytics"""
    try:
        # Total students
        students_result = db.execute_query("SELECT SUM(no_students) as total FROM Schedule")
        total_students = students_result[0]['total'] if students_result and 'total' in students_result[0] else 0

        # Students by program
        students_by_program_result = db.execute_query("""
            SELECT program, SUM(no_students) as total
            FROM Schedule
            GROUP BY program
        """)
        students_by_program = [
            {'program': row['program'], 'count': row['total']} for row in students_by_program_result if 'program' in row and 'total' in row
        ]

        # Total events
        events_result = db.execute_query("SELECT COUNT(*) as count FROM Events")
        total_events = events_result[0]['count'] if events_result and 'count' in events_result[0] else 0

        # Recent events with attendance
        recent_events_result = db.execute_query("""
            SELECT e.event_name, e.event_date, COUNT(a.attendance_id) as attendance
            FROM Events e
            LEFT JOIN Attendance a ON e.event_id = a.event_id
            WHERE e.event_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND DATE_ADD(CURDATE(), INTERVAL 1 MONTH)
            GROUP BY e.event_id, e.event_name, e.event_date
            ORDER BY e.event_date DESC
        """)
        recent_events = [
            {
                'event_name': row['event_name'],
                'event_date': str(row['event_date']),
                'attendance': row['attendance']
            } for row in recent_events_result if 'event_name' in row and 'event_date' in row and 'attendance' in row
        ]

        return jsonify({
            'success': True,
            'analytics': {
                'total_students': total_students,
                'students_by_program': students_by_program,
                'total_events': total_events,
                'recent_events': recent_events
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db.connection else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    print(f"🚀 Starting Flask server on port {port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🤖 AI Agent: Ready")
    print(f"📅 Google Calendar: Configured")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
