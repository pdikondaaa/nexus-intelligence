/**
 * ============================================================
 *  Sidebar Component
 * ============================================================
 *  Chat history panel with new-chat creation, auth controls,
 *  and conversation selection.
 * ============================================================
 */

import React from 'react';
import { MessageSquarePlus, MessageSquare, LogIn, LogOut } from 'lucide-react';

function Sidebar({
  chats,
  activeChatId,
  isAuthenticated,
  accountName,
  isSidebarOpen,
  onNewChat,
  onSelectChat,
  onLogin,
  onLogout,
}) {
  return (
    <div className={`sidebar ${isSidebarOpen ? '' : 'closed'}`}>
      <div className="sidebar-inner">
        {/* Header — New Chat + Auth Buttons */}
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={onNewChat}>
            <MessageSquarePlus size={18} />
            <span>New Chat</span>
          </button>

          <div style={{ marginTop: '10px' }}>
            {isAuthenticated ? (
              <button
                className="new-chat-btn"
                onClick={onLogout}
                style={{ background: '#ef4444' }}
              >
                <LogOut size={16} />
                <span>Sign Out ({accountName})</span>
              </button>
            ) : (
              <button
                className="new-chat-btn"
                onClick={onLogin}
                style={{ background: '#0ea5e9' }}
              >
                <LogIn size={16} />
                <span>Sign In with Microsoft</span>
              </button>
            )}
          </div>
        </div>

        {/* Chat List */}
        <div className="chat-list">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={`chat-item ${chat.id === activeChatId ? 'active' : ''}`}
              onClick={() => onSelectChat(chat.id)}
            >
              <MessageSquare size={16} />
              <span
                style={{
                  flex: 1,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {chat.title}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
