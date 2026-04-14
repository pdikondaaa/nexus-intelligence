/**
 * ============================================================
 *  ChatUI Component
 * ============================================================
 *  The main chat interface: header, message list, typing indicator,
 *  and input bar. Orchestrates message sending through the API
 *  service layer.
 *
 *  Architecture position:  User ↔ [Chat UI] ↔ Auth Layer (via API)
 * ============================================================
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Menu, X } from 'lucide-react';
import MessageBubble from './MessageBubble';
import { sendChatMessage } from '../services/api';

function ChatUI({
  activeChat,
  isTyping,
  setIsTyping,
  updateChatMessages,
  isSidebarOpen,
  onToggleSidebar,
  getAccessToken,
}) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeChat?.messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const currentChatId = activeChat.id;
    const userText = inputValue.trim();

    const newUserMsg = {
      id: Date.now(),
      text: userText,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    updateChatMessages(currentChatId, (msgs) => [...msgs, newUserMsg]);
    setInputValue('');
    setIsTyping(true);

    // Catch isolated greetings to bypass expensive LLM calls
    if (
      /^(hi|hello|hey|good morning|good afternoon|good evening|howdy|hi there|hello there)$/i.test(
        userText.toLowerCase()
      )
    ) {
      setTimeout(() => {
        const greetingMsg = {
          id: Date.now() + 1,
          text: "Hello! I'm Nexus intelligence. How can I help you today?",
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          responseTime: '0.1',
        };
        setIsTyping(false);
        updateChatMessages(currentChatId, (msgs) => [...msgs, greetingMsg]);
      }, 500);
      return;
    }

    try {
      // Build full conversation history for context
      const fullHistory = [...activeChat.messages, newUserMsg];
      const formattedHistory = fullHistory.map((msg) => ({
        role: msg.sender === 'bot' ? 'assistant' : 'user',
        content: msg.text,
      }));

      const startTime = Date.now();

      // Get access token from auth layer (may be empty)
      const accessToken = await getAccessToken();

      // Send to backend pipeline via API service
      const reader = await sendChatMessage(formattedHistory, accessToken);

      setIsTyping(false);

      const newBotMsgId = Date.now() + 1;

      // Inject empty message block that gets streamed into
      updateChatMessages(currentChatId, (msgs) => [
        ...msgs,
        {
          id: newBotMsgId,
          text: '',
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        },
      ]);

      const decoder = new TextDecoder('utf-8');
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          updateChatMessages(currentChatId, (msgs) =>
            msgs.map((msg) =>
              msg.id === newBotMsgId
                ? { ...msg, text: msg.text + chunk }
                : msg
            )
          );
        }
      }

      const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
      updateChatMessages(currentChatId, (msgs) =>
        msgs.map((msg) =>
          msg.id === newBotMsgId
            ? { ...msg, responseTime: elapsedSeconds }
            : msg
        )
      );
    } catch (error) {
      console.error('Pipeline error:', error);
      const errorMsg = {
        id: Date.now() + 1,
        text: error.message.startsWith('Your message')
          ? `⚠️ ${error.message}`
          : `Error: ${error.message || 'Could not reach the backend. Ensure FastAPI and Ollama are running.'}`,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      };
      setIsTyping(false);
      updateChatMessages(currentChatId, (msgs) => [...msgs, errorMsg]);
    }
  };

  return (
    <div className="main-content">
      {/* Header */}
      <header className="chat-header">
        <button
          className="toggle-sidebar-btn"
          onClick={onToggleSidebar}
          title={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="bot-avatar">
          <Sparkles color="#ffffff" size={18} />
        </div>
        <div className="header-info">
          <h1>Nexus intelligence</h1>
          <p>
            <span style={{ color: '#10b981', fontSize: '10px' }}>●</span>{' '}
            {activeChat?.title || 'Online'}
          </p>
        </div>
      </header>

      {/* Messages Area */}
      <div className="messages-area">
        {activeChat?.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isTyping && activeChat?.messages && (
          <div className="message-wrapper bot">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <form onSubmit={handleSend} className="input-container">
          <input
            type="text"
            className="message-input"
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isTyping}
            autoFocus
          />
          <button
            type="submit"
            className="send-button"
            disabled={!inputValue.trim() || isTyping}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatUI;
