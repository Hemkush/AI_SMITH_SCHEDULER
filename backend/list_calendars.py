# Create a file: backend/list_calendars.py
from google_calendar import calendar_manager

calendar_manager.authenticate()

try:
    # List all calendars
    calendar_list = calendar_manager.service.calendarList().list().execute()
    
    print("\n📅 Your Available Calendars:\n")
    print("-" * 80)
    
    for calendar in calendar_list.get('items', []):
        print(f"Calendar Name: {calendar['summary']}")
        print(f"Calendar ID:   {calendar['id']}")
        print(f"Primary:       {calendar.get('primary', False)}")
        print(f"Access Role:   {calendar.get('accessRole', 'N/A')}")
        print("-" * 80)
        
except Exception as e:
    print(f"Error: {e}")