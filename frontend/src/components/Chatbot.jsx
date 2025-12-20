// Helper to render markdown-like formatting for chatbot messages

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, RefreshCw, Sparkles } from 'lucide-react';
import logoUMD from '../testudo-96e4c17d.png';
import { aiAPI } from '../utils/api';

function renderFormattedMessage(content) {
  // Replace **bold**
  let formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Replace * list items
  formatted = formatted.replace(/\n\*\s+/g, '<br />&bull; ');
  // Replace numbered lists
  formatted = formatted.replace(/\n\d+\.\s+/g, '<br />');
  // Replace double line breaks with paragraph
  formatted = formatted.replace(/\n\n/g, '<br /><br />');
  // Replace single line breaks
  formatted = formatted.replace(/\n/g, '<br />');
  return <span dangerouslySetInnerHTML={{ __html: formatted }} />;
}

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your AI scheduling assistant. I can help you:\n\n• Find the best time for events\n• Check student availability\n• Analyze past event attendance\n• Suggest optimal scheduling\n• Summarize event feedback\n\nWhat would you like to know?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedPrograms, setSelectedPrograms] = useState([]);
  const messagesEndRef = useRef(null);

  const programs = ['MBA', 'MSIS', 'MSBA', 'Undergraduate', 'Graduate'];

  const quickQuestions = [
    "When is the best time to schedule an event this week?",
    "What's the availability for MBA students on Monday at 2 PM?",
    "Show me the last event's attendance",
    "Which day has the most free time?",
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await aiAPI.chat(
        input,
        selectedPrograms.length > 0 ? selectedPrograms : null
      );

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ Sorry, I encountered an error: ${error.message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = (question) => {
    setInput(question);
  };

  const handleReset = async () => {
    try {
      await aiAPI.reset();
      setMessages([
        {
          role: 'assistant',
          content: "Conversation reset! How can I help you?",
        },
      ]);
      setSelectedPrograms([]);
    } catch (error) {
      console.error('Error resetting conversation:', error);
    }
  };

  const toggleProgram = (program) => {
    setSelectedPrograms((prev) =>
      prev.includes(program)
        ? prev.filter((p) => p !== program)
        : [...prev, program]
    );
  };

  return (
    <div className="chatbot">
      <div className="chatbot-header">
        <div className="header-title">
          <Sparkles size={24} />
          <h2>AI Scheduling Assistant</h2>
        </div>
        <button className="reset-button" onClick={handleReset} title="Reset conversation">
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Program Filters */}
      <div className="program-filters">
        <span className="filter-label">Filter by program:</span>
        <div className="filter-buttons">
          {programs.map((program) => (
            <button
              key={program}
              className={`filter-btn ${
                selectedPrograms.includes(program) ? 'active' : ''
              }`}
              onClick={() => toggleProgram(program)}
            >
              {program}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Questions */}
      {messages.length === 1 && (
        <div className="quick-questions">
          <p className="quick-label">Quick questions:</p>
          <div className="quick-grid">
            {quickQuestions.map((question, index) => (
              <button
                key={index}
                className="quick-question"
                onClick={() => handleQuickQuestion(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="chatbot-messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-icon">
              {message.role === 'user' ? (
                <User size={20} />
              ) : (
                <img src={logoUMD} alt="UMD Logo" style={{ height: 20, width: 20, borderRadius: '50%' }} />
              )}
            </div>
            <div className="message-content">
              {renderFormattedMessage(message.content)}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant-message">
            <div className="message-icon">
              <img src={logoUMD} alt="UMD Logo" style={{ height: 20, width: 20, borderRadius: '50%' }} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chatbot-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about scheduling, availability, or events..."
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="send-button"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}

export default Chatbot;