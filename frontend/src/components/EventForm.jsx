import React, { useState } from 'react';
import { CheckCircle, AlertCircle, Sparkles, QrCode } from 'lucide-react';
import { eventsAPI, scheduleAPI, aiAPI, qrAPI } from '../utils/api';

// Helper to render markdown-like formatting for AI suggestion
function renderFormattedMessage(content) {
  let formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/\n\*\s+/g, '<br />&bull; ');
  formatted = formatted.replace(/\n\d+\.\s+/g, '<br />');
  formatted = formatted.replace(/\n\n/g, '<br /><br />');
  formatted = formatted.replace(/\n/g, '<br />');
  return <span dangerouslySetInnerHTML={{ __html: formatted }} />;
}

function EventForm() {
  const [formData, setFormData] = useState({
    event_name: '',
    event_date: '',
    start_time: '',
    end_time: '',
    location: '',
    description: '',
    target_programs: [],
  });

  const [availability, setAvailability] = useState(null);
  const [conflicts, setConflicts] = useState([]);
  const [createdEvent, setCreatedEvent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);

  const programs = ['MBA', 'MSIS', 'MSBA', 'Undergraduate', 'Graduate'];
  // const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const toggleProgram = (program) => {
    setFormData((prev) => {
      const updatedPrograms = prev.target_programs.includes(program)
        ? prev.target_programs.filter((p) => p !== program)
        : [...prev.target_programs, program];
      console.log("Jimmy's target programs: ", updatedPrograms);
      return {
        ...prev,
        target_programs: updatedPrograms,
      };
    });
  };

  const checkAvailability = async () => {
    if (!formData.event_date || !formData.start_time || !formData.end_time) {
      alert('Please fill in date and time fields');
      return;
    }

    try {
  const date = new Date(formData.event_date);
  const day = daysOfWeek[date.getDay()]; // Correct mapping for JS getDay()
  console.log('Checking availability for day:', day, date);

      const response = await scheduleAPI.checkAvailability({
        day: day,
        start_time: formData.start_time,
        end_time: formData.end_time,
        // program: formData.target_programs[0] || null,
        program: formData.target_programs || null,
        event_date: formData.event_date,  // Add this
      });
      console.log('Availability response:', response.data);

      setAvailability(response.data.availability);

      // Combine both types of conflicts
      const allConflicts = [
        ...response.data.class_conflicts.map(c => ({...c, type: 'class'})),
        ...response.data.event_conflicts.map(c => ({...c, type: 'event'}))
      ];
      // setConflicts(response.data.conflicts);
      setConflicts(allConflicts);
    } catch (error) {
      console.error('Error checking availability:', error);
      alert('Error checking availability');
    }
  };

  const getAISuggestion = async () => {
    if (!formData.event_name) {
      alert('Please enter an event name first');
      return;
    }

    setLoadingAI(true);
    try {
      const response = await aiAPI.suggestTime(
        formData.event_name,
        formData.event_date,
        formData.target_programs.length > 0 ? formData.target_programs : null,
        2
      );

      setAiSuggestion(response.data.response);
    } catch (error) {
      console.error('Error getting AI suggestion:', error);
      alert('Error getting AI suggestion');
    } finally {
      setLoadingAI(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await eventsAPI.create(formData);

      setCreatedEvent(response.data);
      alert('✅ Event created successfully!');

      // Reset form
      setFormData({
        event_name: '',
        event_date: '',
        start_time: '',
        end_time: '',
        location: '',
        description: '',
        target_programs: [],
      });
      setAvailability(null);
      setConflicts([]);
      setAiSuggestion(null);
    } catch (error) {
      console.error('Error creating event:', error);
      alert('Error creating event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="event-form-container">
      <h2>Create New Event</h2>

      <form onSubmit={handleSubmit} className="event-form">
        {/* Basic Info */}
        <div className="form-section">
          <h3>Basic Information</h3>

          <div className="form-group">
            <label>Event Name *</label>
            <input
              type="text"
              name="event_name"
              value={formData.event_name}
              onChange={handleChange}
              required
              placeholder="e.g., Leadership Workshop"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Date *</label>
              <input
                type="date"
                name="event_date"
                value={formData.event_date}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Start Time *</label>
              <input
                type="time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>End Time *</label>
              <input
                type="time"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Location</label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g., Room 301"
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              placeholder="Event details..."
            />
          </div>
        </div>

        {/* Target Programs */}
        <div className="form-section">
          <h3>Target Programs</h3>
          <div className="program-checkboxes">
            {programs.map((program) => (
              <label key={program} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.target_programs.includes(program)}
                  onChange={() => toggleProgram(program)}
                />
                {program}
              </label>
            ))}
          </div>
        </div>

        {/* AI Suggestion */}
        <div className="form-section ai-section">
          <h3>AI Assistance</h3>
          <button
            type="button"
            className="ai-button"
            onClick={getAISuggestion}
            disabled={loadingAI || !formData.event_name}
          >
            <Sparkles size={18} />
            {loadingAI ? 'Getting suggestion...' : 'Get AI Time Suggestion'}
          </button>

          {aiSuggestion && (
            <div className="ai-suggestion">
              {renderFormattedMessage(aiSuggestion)}
            </div>
          )}

        </div>

        {/* Availability Check */}
        <div className="form-section">
          <h3>Check Availability</h3>
          <button
            type="button"
            className="check-button"
            onClick={checkAvailability}
            disabled={!formData.event_date || !formData.start_time}
          >
            Check Student Availability
          </button>

          {availability && (
            <div className="availability-results">
              <div className="availability-card">
                <h4>Availability Summary</h4>
                <div className="availability-stats">
                  <div className="stat">
                    <span className="stat-value">
                      {availability.availability_percentage}%
                    </span>
                    <span className="stat-label">Available</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">
                      {availability.available_students}
                    </span>
                    <span className="stat-label">Students Free</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{availability.busy_students}</span>
                    <span className="stat-label">In Classes</span>
                  </div>
                </div>
              </div>

              {/* {conflicts.length > 0 && (
                <div className="conflicts-card">
                  <h4>
                    <AlertCircle size={18} /> Schedule Conflicts
                  </h4>
                  <ul className="conflicts-list">
                    {conflicts.map((conflict, index) => (
                      <li key={index}>
                        {conflict.course} ({conflict.program}) - {conflict.time} -{' '}
                        {conflict.students} students
                      </li>
                    ))}
                  </ul>
                </div>
              )} */}

              {conflicts.length > 0 && (
  <div className="conflicts-card">
    <h4>
      <AlertCircle size={18} /> Schedule Conflicts
    </h4>
    <ul className="conflicts-list">
      {conflicts.map((conflict, index) => (
        <li key={index}>
          {conflict.type === 'class' ? (
            <>
              📚 {conflict.course_name} ({conflict.program}) - {conflict.start_time} to {conflict.end_time} - {conflict.no_students} students
            </>
          ) : (
            <>
              📅 Event: {conflict.event_name} - {conflict.start_time} to {conflict.end_time}
              {conflict.location && ` at ${conflict.location}`}
            </>
          )}
        </li>
      ))}
    </ul>
  </div>
)}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button type="submit" className="submit-button" disabled={loading}>
          {loading ? 'Creating Event...' : 'Create Event'}
        </button>
      </form>

      {/* Created Event Success */}
      {createdEvent && (
        <div className="success-modal">
          <div className="success-content">
            <CheckCircle size={48} color="#10b981" />
            <h3>Event Created Successfully!</h3>
            <p>Your event has been added to the database and Google Calendar.</p>

            {createdEvent.qr_code_path && (
              <div className="qr-section">
                <h4>
                  <QrCode size={20} /> QR Code for Registration
                </h4>
                <img
                  src={qrAPI.get(createdEvent.event_id)}
                  alt="QR Code"
                  className="qr-image"
                />
                <p className="qr-info">
                  Students can scan this QR code to check in to the event.
                </p>
              </div>
            )}

            {createdEvent.registration_link && (
              <div className="registration-link-section">
                <h4>Registration Link</h4>
                <a
                  href={createdEvent.registration_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="registration-link"
                >
                  {createdEvent.registration_link}
                </a>
                <p className="link-info">
                  Students can use this link to register for the event and check in for attendance.
                </p>
              </div>
            )}

            <button
              onClick={() => setCreatedEvent(null)}
              className="close-button"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default EventForm;