import os
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarManager:
    def sync_calendar_events_to_database(self, db, max_results=100):
        """Fetch events from Google Calendar and add them to Events table, skipping duplicates by name/summary."""
        self.authenticate()
        events = self.get_events(max_results=max_results)
        count = 0
        for event in events:
            start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            end = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
            if not start or not end:
                continue
            if 'T' in start:
                event_date = start[:10]
                start_time = start[11:16]
            else:
                event_date = start
                start_time = ''
            if 'T' in end:
                end_time = end[11:16]
            else:
                end_time = ''
            event_name = event.get('summary', 'Untitled Event')
            # Check for duplicate event name and date in DB
            duplicate_check = db.execute_query(
                "SELECT event_id FROM Events WHERE event_name = %s AND event_date = %s", (event_name, event_date)
            )
            if duplicate_check:
                print(f"⏩ Skipping duplicate event: {event_name} on {event_date}")
                continue
            event_data = {
                'event_name': event_name,
                'event_date': event_date,
                'start_time': start_time,
                'end_time': end_time,
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'target_programs': '[]',
                'google_calendar_id': event.get('id', ''),
                'qr_code_path': ''
            }
            db.add_event(event_data)
            count += 1
        print(f"✅ Synced {count} events from Google Calendar to Events table.")
    def __init__(self):
        self.creds = None
        self.service = None
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        # Token.json stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=self.creds)
        print("✅ Google Calendar authenticated successfully")
    
    def sync_calendar_events_to_database(self, db, max_results=100):
        """Fetch events from Google Calendar and add them to Events table"""
        self.authenticate()
        events = self.get_events(max_results=max_results)
        count = 0
        for event in events:
            start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            end = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
            if not start or not end:
                continue
            if 'T' in start:
                event_date = start[:10]
                start_time = start[11:16]
            else:
                event_date = start
                start_time = ''
            if 'T' in end:
                end_time = end[11:16]
            else:
                end_time = ''
            google_calendar_id = event.get('id', '')
            # Check for duplicate google_calendar_id in DB
            duplicate_check = db.execute_query(
                "SELECT event_id FROM Events WHERE google_calendar_id = %s", (google_calendar_id,)
            )
            if duplicate_check:
                print(f"⏩ Skipping event already in DB (google_calendar_id): {google_calendar_id}")
                continue
            event_data = {
                'event_name': event.get('summary', 'Untitled Event'),
                'event_date': event_date,
                'start_time': start_time,
                'end_time': end_time,
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'target_programs': '[]',
                'google_calendar_id': google_calendar_id,
                'qr_code_path': ''
            }
            db.add_event(event_data)
            count += 1
        print(f"✅ Synced {count} events from Google Calendar to Events table.")
    
    def create_event(self, event_data):
        """
        Create an event in Google Calendar
        Always uses 'primary' calendar and authenticates before creating.
        """
        self.calendar_id = 'primary'
        self.authenticate()
        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_data
            ).execute()
            print(f"✅ Event created: {event.get('htmlLink')}")
            return event.get('id')
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None
    
    def update_event(self, event_id, event_data):
        """Update an existing event"""
        try:
            event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
            
            print(f"✅ Event updated: {event.get('htmlLink')}")
            return True
        
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False
    
    def delete_event(self, event_id):
        """Delete an event"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            print("✅ Event deleted successfully")
            return True
        
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False
    
    def get_events(self, time_min=None, time_max=None, max_results=100):
        """
        Get events from calendar
        
        time_min and time_max should be in RFC3339 format:
        '2024-11-10T00:00:00Z'
        """
        self.calendar_id = 'primary'
        self.authenticate()
        try:
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"✅ Retrieved {len(events)} events")
            return events
        
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return []
    
    def get_upcoming_events(self, days=7):
        """Get events for the next N days"""
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'
        
        return self.get_events(time_min, time_max)
    
    def format_event_for_calendar(self, event_name, event_date, start_time, end_time, 
                                  location='', description=''):
        """
        Format event data for Google Calendar API
        Adds seconds to time fields if missing.
        event_date: 'YYYY-MM-DD'
        start_time: 'HH:MM' or 'HH:MM:SS'
        end_time: 'HH:MM' or 'HH:MM:SS'
        """
        def pad_seconds(t):
            return t if len(t.split(':')) == 3 else t + ':00'
        start_datetime = f"{event_date}T{pad_seconds(start_time)}"
        end_datetime = f"{event_date}T{pad_seconds(end_time)}"
        event = {
            'summary': event_name,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        return event
    
    def sync_database_events_to_calendar(self, db):
        """Sync events from database to Google Calendar"""
        from database import db as database
        
        query = """
            SELECT * FROM Events 
            WHERE google_calendar_id IS NULL OR google_calendar_id = ''
        """
        
        events = database.execute_query(query)
        
        synced_count = 0
        for event in events:
            calendar_event = self.format_event_for_calendar(
                event['event_name'],
                event['event_date'].strftime('%Y-%m-%d'),
                str(event['start_time']),
                str(event['end_time']),
                event.get('location', ''),
                event.get('description', '')
            )
            
            calendar_id = self.create_event(calendar_event)
            
            if calendar_id:
                # Update database with Google Calendar ID
                update_query = """
                    UPDATE Events 
                    SET google_calendar_id = %s 
                    WHERE event_id = %s
                """
                database.execute_update(update_query, (calendar_id, event['event_id']))
                synced_count += 1
        
        print(f"✅ Synced {synced_count} events to Google Calendar")
        return synced_count

# Singleton instance
calendar_manager = GoogleCalendarManager()

# Test function
def test_calendar():
    """Test Google Calendar integration"""
    calendar_manager.authenticate()
    # Get upcoming events
    upcoming = calendar_manager.get_upcoming_events(days=7)
    print(f"\n📅 Upcoming Events ({len(upcoming)}):")
    for event in upcoming:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"  - {event['summary']} at {start}")

if __name__ == '__main__':
    test_calendar()
    create_sample_event()
    calendar_manager.get_events()
    