# Create a file: backend/test_calendar_access.py
from google_calendar import calendar_manager

calendar_manager.authenticate()

print(f"\n🔍 Testing Calendar ID: {calendar_manager.calendar_id}\n")

try:
    # Try to get calendar details
    calendar = calendar_manager.service.calendars().get(
        calendarId=calendar_manager.calendar_id
    ).execute()
    
    print(f"✅ Calendar found!")
    print(f"   Summary: {calendar.get('summary')}")
    print(f"   Timezone: {calendar.get('timeZone')}")
    print(f"   Description: {calendar.get('description', 'None')}")
    
    # Try to list events
    print("\n📋 Testing event listing...")
    events = calendar_manager.get_upcoming_events(days=7)
    print(f"✅ Successfully retrieved {len(events)} events")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Suggestions:")
    print("   1. Try setting GOOGLE_CALENDAR_ID=primary in .env")
    print("   2. Make sure you're authenticated with the correct Google account")
    print("   3. Delete token.json and re-authenticate: python google_calendar.py")