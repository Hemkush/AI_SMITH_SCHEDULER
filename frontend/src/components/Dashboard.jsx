import React, { useState, useEffect } from 'react';
import { Users, Calendar, TrendingUp, Award } from 'lucide-react';
import { analyticsAPI, eventsAPI, scheduleAPI } from '../utils/api';

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [events, setEvents] = useState([]);
  const [schedule, setSchedule] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [analyticsRes, eventsRes, scheduleRes] = await Promise.all([
        analyticsAPI.get(),
        eventsAPI.getAll(),
        scheduleAPI.getAll(),
      ]);

      setAnalytics(analyticsRes.data.analytics);
      setEvents(eventsRes.data.events);
      setSchedule(scheduleRes.data.schedule);
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h2>Dashboard Overview</h2>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#3b82f6' }}>
            <Users size={24} />
          </div>
          <div className="stat-content">
            <h3>{analytics?.total_students || 0}</h3>
            <p>Total Students</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#10b981' }}>
            <Calendar size={24} />
          </div>
          <div className="stat-content">
            <h3>{analytics?.total_events || 0}</h3>
            <p>Total Events</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#f59e0b' }}>
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <h3>
              {events.length > 0
                ? (events.reduce((acc, e) => acc + e.attendance_count, 0) / events.length).toFixed(2)
                : '0.00'}
            </h3>
            <p>Avg. Attendance</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#8b5cf6' }}>
            <Award size={24} />
          </div>
          <div className="stat-content">
            <h3>{analytics?.students_by_program?.length || 0}</h3>
            <p>Programs</p>
          </div>
        </div>
      </div>

      {/* Students by Program */}
      <div className="dashboard-section">
        <h3>Students by Program</h3>
        <div className="program-grid">
          {analytics?.students_by_program?.map((item) => (
            <div key={item.program} className="program-card">
              <h4>{item.program}</h4>
              <p className="program-count">{item.count} students</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Events */}
      <div className="dashboard-section">
        <h3>Recent Events</h3>
        <div className="events-list events-list-grid">
          {events.slice(0, 10).map((event) => (
            <div key={event.event_id} className="event-item">
              <div className="event-info">
                <h4>{event.event_name}</h4>
                <p className="event-date">
                  {new Date(event.event_date).toLocaleDateString()} at{' '}
                  {event.start_time}
                </p>
                {event.location && (
                  <p className="event-location">📍 {event.location}</p>
                )}
                {event.registration_link && event.registration_link !== '' && (
                  <a
                    href={event.registration_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="registration-link"
                  >
                    Registration Link
                  </a>
                )}
              </div>
              <div className="event-attendance">
                <span className="attendance-badge">
                  {event.attendance_count} attended
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Weekly Schedule Preview */}
      <div className="dashboard-section">
        <h3>This Week's Schedule</h3>
        <div className="schedule-preview">
          {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].map(day => (
            <div key={day} className="day-schedule">
              <h4>{day}</h4>
              {schedule[day] && schedule[day].length > 0 ? (
                <p className="class-count">{schedule[day].length} Classes</p>
              ) : (
                <p className="class-count">No Class</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;