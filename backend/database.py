import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', 'Maryland_123#')
        self.database = os.getenv('DB_NAME', 'event_scheduler_new')
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor,
                autocommit=True
            )
            print("✅ Database connected successfully")
            return self.connection
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    # def close(self):
    #     """Close database connection"""
    #     if self.connection:
    #         self.connection.close()
    #         print("Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute SELECT query and return results"""
        try:
            if self.connection is None or not getattr(self.connection, 'open', False):
                print("Reconnecting to database...")
                self.connection = self.connect()
            with self.connection.cursor() as cursor:
                if params is not None:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Query execution error: {e}")
            raise
    
    def execute_update(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            if self.connection is None or not getattr(self.connection, 'open', False):
                print("Reconnecting to database...")
                self.connection = self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.lastrowid
        except Exception as e:
            print(f"Update execution error: {e}")
            raise
    
    # Helper methods for common queries
    def get_all_students(self, program=None):
        """Get all students, optionally filtered by program"""
        query = "SELECT SUM(no_students) as total FROM Schedule"
        params = None
        if program:
            query += " WHERE program = %s"
            params = (program,)
        return self.execute_query(query, params)
    
    def get_schedule_by_day(self, day):
        """Get all classes for a specific day"""
        query = """
            SELECT * FROM Schedule 
            WHERE day_of_week = %s 
            ORDER BY start_time
        """
        return self.execute_query(query, (day,))
    
    # def get_schedule_conflicts(self, start_time, end_time, day):
    #     """Find classes that conflict with given time slot"""
    #     query = """
    #         SELECT * FROM Schedule
    #         WHERE day_of_week = %s
    #         AND (
    #             (start_time <= %s AND end_time > %s)
    #             OR (start_time < %s AND end_time >= %s)
    #             OR (start_time >= %s AND end_time <= %s)
    #         )
    #     """
    #     return self.execute_query(query, (day, start_time, start_time, end_time, end_time, start_time, end_time))

    def get_schedule_conflicts(self, start_time, end_time, day, event_date=None, exclude_event_id=None):
        """
        Find classes and events that conflict with given time slot
    
        Args:
        start_time: Start time (HH:MM:SS)
        end_time: End time (HH:MM:SS)
        day: Day of week (Monday, Tuesday, etc.)
        event_date: Date for event conflicts (YYYY-MM-DD), optional
        exclude_event_id: Event ID to exclude (when updating existing event)
    
        Returns:
        dict with 'class_conflicts' and 'event_conflicts'
        """
    
    # 1. Check Schedule (Class) Conflicts
        schedule_query = """
            SELECT *, 'class' as conflict_type FROM Schedule
            WHERE day_of_week = %s
            AND (
                (start_time <= %s AND end_time > %s)
                OR (start_time < %s AND end_time >= %s)
                OR (start_time >= %s AND end_time <= %s)
            )
        """
        class_conflicts = self.execute_query(
            schedule_query, 
            (day, start_time, start_time, end_time, end_time, start_time, end_time)
        )
    
    # 2. Check Event Conflicts (if event_date provided)
        event_conflicts = []
        if event_date:
            event_query = """
                SELECT *, 'event' as conflict_type FROM Events
                WHERE event_date = %s
                AND (
                    (start_time <= %s AND end_time > %s)
                    OR (start_time < %s AND end_time >= %s)
                    OR (start_time >= %s AND end_time <= %s)
               )
           """
            params = [event_date, start_time, start_time, end_time, end_time, start_time, end_time]
        
        # Exclude specific event (useful when editing)
            if exclude_event_id:
                event_query += " AND event_id != %s"
                params.append(exclude_event_id)
        
            event_conflicts = self.execute_query(event_query, tuple(params))
    
        return {
            'class_conflicts': class_conflicts,
            'event_conflicts': event_conflicts,
            'total_conflicts': len(class_conflicts) + len(event_conflicts)
      }


    def get_all_conflicts_combined(self, start_time, end_time, day, event_date=None):
       """
       Get all conflicts (classes + events) as a single list
     """
       conflicts = self.get_schedule_conflicts(start_time, end_time, day, event_date)
    
    # Combine both types into one list
       all_conflicts = []
    
    # Add class conflicts
       for conflict in conflicts['class_conflicts']:
           all_conflicts.append({
            'type': 'class',
            'name': conflict.get('course_name'),
            'program': conflict.get('program'),
            'start_time': conflict.get('start_time'),
            'end_time': conflict.get('end_time'),
            'students_affected': conflict.get('no_students'),
            'day': conflict.get('day_of_week')
          })
    
    # Add event conflicts
       for conflict in conflicts['event_conflicts']:
           all_conflicts.append({
            'type': 'event',
            'name': conflict.get('event_name'),
            'event_id': conflict.get('event_id'),
            'start_time': conflict.get('start_time'),
            'end_time': conflict.get('end_time'),
            'location': conflict.get('location'),
            'date': conflict.get('event_date')
           })

           print("Jimmy's all conflicts: ", all_conflicts)
    
       return all_conflicts
    
    def get_event_attendance(self, event_id):
        """Get attendance for a specific event"""
        query = """
            SELECT a.*, s.name, s.email, s.program
            FROM Attendance a
            JOIN Students s ON a.student_id = s.student_id
            WHERE a.event_id = %s
            ORDER BY a.check_in_time
        """
        return self.execute_query(query, (event_id,))
    
    def add_event(self, event_data):
        """Add new event to database"""
        query = """
            INSERT INTO Events 
            (event_name, event_date, start_time, end_time, location, 
             description, target_programs, google_calendar_id, qr_code_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            event_data['event_name'],
            event_data['event_date'],
            event_data['start_time'],
            event_data['end_time'],
            event_data.get('location', ''),
            event_data.get('description', ''),
            event_data.get('target_programs', '[]'),
            event_data.get('google_calendar_id', ''),
            event_data.get('qr_code_path', '')
        )
        return self.execute_update(query, params)
    
    def record_attendance(self, event_id, student_id, student_feedback=None):
        """Record student attendance for an event, with optional feedback"""
        if student_feedback is not None and student_feedback != '':
            query = """
                INSERT INTO Attendance (event_id, student_id, student_feedback)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE check_in_time = CURRENT_TIMESTAMP, student_feedback = VALUES(student_feedback)
            """
            return self.execute_update(query, (event_id, student_id, student_feedback))
        else:
            query = """
                INSERT INTO Attendance (event_id, student_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE check_in_time = CURRENT_TIMESTAMP
            """
            return self.execute_update(query, (event_id, student_id))
    
    def get_available_students_count(self, day, start_time, end_time, program=None):
        """Calculate how many students are available during a time slot"""
        # Get total students
        if program:
            # Accepts a list of programs, e.g. ['MSBA', 'MSIS']
            placeholders = ', '.join(['%s'] * len(program))
            
            print("Jimmy's program: ", placeholders)
            total_query = f"SELECT SUM(no_students) as total FROM Schedule WHERE program IN ({placeholders})"
            total_students = self.execute_query(total_query, tuple(program))[0]['total']
            print("Jimmy's total students query: ", total_query)
            print("Jimmy's total students: ", total_students)
        else:
            total_query = "SELECT SUM(no_students) as total FROM Schedule"
            total_students = self.execute_query(total_query)[0]['total']
        
        # Get students in conflicting classes
        busy_query = """
            SELECT COALESCE(SUM(no_students), 0) as busy
            FROM Schedule
            WHERE day_of_week = %s
            AND (
                (start_time <= %s AND end_time > %s)
                OR (start_time < %s AND end_time >= %s)
                OR (start_time >= %s AND end_time <= %s)
            )
        """
        if program:
            busy_query += " AND program IN ({})".format(', '.join(['%s'] * len(program)))
            busy_students = self.execute_query(busy_query, (day, start_time, start_time, end_time, end_time, start_time, end_time, *program))[0]['busy']
        else:
            busy_students = self.execute_query(busy_query, (day, start_time, start_time, end_time, end_time, start_time, end_time))[0]['busy']
        
        available = total_students - busy_students
        percentage = (available / total_students * 100) if total_students > 0 else 0
        
        return {
            'total_students': total_students,
            'available_students': available,
            'busy_students': busy_students,
            'availability_percentage': round(percentage, 2)
        }

# Singleton instance
db = Database()