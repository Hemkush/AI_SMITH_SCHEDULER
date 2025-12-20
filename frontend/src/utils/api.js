import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Students API
export const studentsAPI = {
  getAll: (program = null) => {
    const params = program ? { program } : {};
    return api.get('/studentsAll', { params });
  },
  add: (studentData) => api.post('/students', studentData),
};

// Schedule API
export const scheduleAPI = {
  getAll: () => api.get('/schedule'),
  getByDay: (day) => api.get('/schedule', { params: { day } }),
  checkConflicts: (data) => api.post('/schedule/conflicts', data),
  checkAvailability: (data) => api.post('/schedule/availability', data),
};

// Events API
export const eventsAPI = {
  getAll: () => api.get('/events'),
  getById: (eventId) => api.get(`/events/${eventId}`),
  create: (eventData) => api.post('/events', eventData),
  delete: (eventId) => api.delete(`/events/${eventId}`),
};

// Attendance API
export const attendanceAPI = {
  getByEvent: (eventId) => api.get(`/attendance/${eventId}`),
  record: (data) => api.post('/attendance', data),
};

// AI Agent API
export const aiAPI = {
  chat: (query, programs = null) => api.post('/ai/chat', { query, programs }),
  suggestTime: (eventName, eventData, programs = null, durationHours = 2) => 
    api.post('/ai/suggest-time', { 
      event_name: eventName, 
      programs,
      event_date: eventData, 
      duration_hours: durationHours 
    }),
  reset: () => api.post('/ai/reset'),
};

// Calendar API
export const calendarAPI = {
  sync: () => api.post('/calendar/sync'),
  getEvents: (days = 7) => api.get('/calendar/events', { params: { days } }),
};

// Analytics API
export const analyticsAPI = {
  get: () => api.get('/analytics'),
};

// QR Code API
export const qrAPI = {
  get: (eventId) => `${API_BASE_URL}/qr/${eventId}`,
};

// Health Check
export const healthCheck = () => api.get('/health');

export default api;