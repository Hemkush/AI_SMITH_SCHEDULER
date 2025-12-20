// import logo from './logo.svg';
// import './App.css';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;

import React, { useState } from 'react';
import { Calendar, MessageSquare, PlusCircle, BarChart3, Users } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';
import EventForm from './components/EventForm';
import CalendarView from './components/Calendar';
import './App.css';
import logoUMD from './testudo-96e4c17d.png';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'chatbot', label: 'AI Assistant', icon: MessageSquare },
    { id: 'create-event', label: 'Create Event', icon: PlusCircle },
    { id: 'calendar', label: 'Calendar', icon: Calendar },
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1><img src={logoUMD} className="UMD-logo" alt="logo" style={{ height: '1.5em', verticalAlign: 'middle' }} /> Smith Scheduler</h1>
          <p style={{ paddingLeft: '2em' }}>Intelligent scheduling powered by AI</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="app-nav">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`nav-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={20} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Main Content */}
      <main className="app-content">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'chatbot' && <Chatbot />}
        {activeTab === 'create-event' && <EventForm />}
        {activeTab === 'calendar' && <CalendarView />}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        {/* <p>Google Calendar:</p> */}

<a style={{ color: 'White' }} href="https://calendar.google.com/calendar/u/0/r" target="_blank">Smith Google Calendar</a>
      </footer>
    </div>
  );
}

export default App;
