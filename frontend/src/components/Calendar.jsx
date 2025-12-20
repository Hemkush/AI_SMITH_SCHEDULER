import React, { useState, useEffect } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { Clock, MapPin, Users, Trash2, ExternalLink } from 'lucide-react';
import { eventsAPI, calendarAPI } from '../utils/api';

function CalendarView() {
  const [date, setDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [selectedDateEvents, setSelectedDateEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    filterEventsByDate(date);
  }, [date, events]);

  const loadEvents = async () => {
    try {
      const response = await eventsAPI.getAll();
      setEvents(response.data.events);
      setLoading(false);
    } catch (error) {
      console.error('Error loading events:', error);
      setLoading(false);
    }
  };

  const filterEventsByDate = (selectedDate) => {
    const dateStr = selectedDate.toISOString().split('T')[0];
    const filtered = events.filter((event) => {
      const eventDate = new Date(event.event_date).toISOString().split('T')[0];
      return eventDate === dateStr;
    });
    setSelectedDateEvents(filtered);
  };

  const handleDateChange = (newDate) => {
    setDate(newDate);
  };

  const tileContent = ({ date, view }) => {
    if (view === 'month') {
      const dateStr = date.toISOString().split('T')[0];
      const dayEvents = events.filter((event) => {
        const eventDate = new Date(event.event_date).toISOString().split('T')[0];
        return eventDate === dateStr;
      });

      // if (dayEvents.length > 0) {
      //   return (
      //     <div className="calendar-event-dot">
      //       <span className="dot">{dayEvents.length}</span>
      //     </div>
      //   );
      // }
    }
    return null;
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event?')) {
      return;
    }

    try {
      await eventsAPI.delete(eventId);
      alert('Event deleted successfully');
      loadEvents();
    } catch (error) {
      console.error('Error deleting event:', error);
      alert('Error deleting event');
    }
  };

  const syncCalendar = async () => {
    setSyncing(true);
    try {
      const response = await calendarAPI.sync();
      alert(response.data.message);
      loadEvents();
    } catch (error) {
      console.error('Error syncing calendar:', error);
      alert('Error syncing calendar');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading calendar...</p>
      </div>
    );
  }

  return (
    <div className="calendar-view">
      <div className="calendar-header">
        <h2>Event Calendar</h2>
        <button
          className="sync-button"
          onClick={syncCalendar}
          disabled={syncing}
        >
          <ExternalLink size={18} />
          {syncing ? 'Syncing...' : 'Sync with Google Calendar'}
        </button>
      </div>

      {/* Calendar Widget on Top - FULL WIDTH, NO PADDING */}
      <div className="calendar-widget" style={{ boxShadow: 'none', borderRadius: '8px', background: 'white', padding: '0', marginBottom: '2.5rem', border: 'none', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'stretch', justifyContent: 'center' }}>
        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Calendar
            onChange={handleDateChange}
            value={date}
            tileContent={tileContent}
            className="custom-calendar"
            style={{ width: '90%', height: 'auto' }}
            tileClassName={({ date: tileDate }) => {
              const today = new Date();
              const isToday = tileDate.toDateString() === today.toDateString();
              const isSelected = tileDate.toDateString() === date.toDateString();
              if (isSelected) return 'calendar-selected';
              if (isToday) return 'calendar-today';
              return null;
            }}
          />
        </div>
        <div className="calendar-legend" style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.15rem' }}>
          <span className="legend-item" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="dot" style={{ background: '#E21833', color: 'white', borderRadius: '50%', width: '22px', height: '22px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', boxShadow: '0 0 8px #E2183388', fontSize: '1.2rem' }}>•</span> Events on this date
          </span>
        </div>
      </div>

      {/* Events List for Selected Day Below Calendar */}
      <div className="events-panel">
        <h3>
          Events on {date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </h3>
        {selectedDateEvents.length === 0 ? (
          <div className="no-events">
            <p>No events scheduled for this date.</p>
          </div>
        ) : (
          <div className="events-list-calendar">
            {selectedDateEvents.map((event) => (
              <div key={event.event_id} className="calendar-event-card">
                <div className="event-header">
                  <h4>{event.event_name}</h4>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(event.event_id)}
                    title="Delete event"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <div className="event-details">
                  <div className="detail-row">
                    <Clock size={16} />
                    <span>
                      {event.start_time} - {event.end_time}
                    </span>
                  </div>
                  {event.location && (
                    <div className="detail-row">
                      <MapPin size={16} />
                      <span>{event.location}</span>
                    </div>
                  )}
                  <div className="detail-row">
                    <Users size={16} />
                    <span>{event.attendance_count} registered</span>
                  </div>
                </div>
                {event.description && (
                  <p className="event-description">{event.description}</p>
                )}
                {event.target_programs && event.target_programs.length > 0 && (
                  <div className="event-programs">
                    {event.target_programs.map((program) => (
                      <span key={program} className="program-badge">
                        {program}
                      </span>
                    ))}
                  </div>
                )}
                {event.google_calendar_id && (
                  <a
                    href={`https://calendar.google.com/calendar/event?eid=${event.google_calendar_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="google-calendar-link"
                  >
                    <ExternalLink size={14} />
                    View in Google Calendar
                  </a>
                )}
                {event.registration_link && event.registration_link !== '' && (
                  <a
                    href={event.registration_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="registration-link"
                  >
                    <ExternalLink size={14} />
                    Registeration Link
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* All Upcoming Events */}
      <div className="upcoming-events-section">
        <h3>All Upcoming Events</h3>
        <div className="upcoming-events-grid">
          {events
            .filter((event) => new Date(event.event_date) >= new Date())
            .slice(0, 12)
            .map((event) => {
              // Increase event date by 1 day
              const eventDateObj = new Date(event.event_date);
              eventDateObj.setDate(eventDateObj.getDate() + 1);
              return (
                <div key={event.event_id} className="upcoming-event-card">
                  <div className="event-date-badge">
                    {eventDateObj.getDate()}
                    <span className="month">
                      {eventDateObj.toLocaleDateString('en-US', {
                        month: 'short',
                      })}
                    </span>
                  </div>
                  <div className="event-info">
                    <h4>{event.event_name}</h4>
                    <p className="time">
                      {event.start_time} - {event.end_time}
                    </p>
                    {event.location && <p className="location">{event.location}</p>}
                    {event.registration_link && event.registration_link !== '' && (
                      <a
                        href={event.registration_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="registration-link"
                      >
                        <ExternalLink size={14} />
                        Register for this event
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}

export default CalendarView;