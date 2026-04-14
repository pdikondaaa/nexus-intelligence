/**
 * ============================================================
 *  App.jsx — Thin Orchestrator Shell
 * ============================================================
 *  This file is now intentionally minimal. It:
 *    1. Manages global state (chat list, active chat)
 *    2. Provides auth integration (MSAL)
 *    3. Composes Sidebar + ChatUI components
 *
 *  All rendering and API logic lives in src/components/ and
 *  src/services/.
 *
 *  Architecture position:
 *    User ↔ Chat UI ↔ Auth Layer ↔ Backend Pipeline
 * ============================================================
 */

import React, { useState, useEffect } from 'react';
import { useMsal, useIsAuthenticated } from '@azure/msal-react';
import { loginRequest } from './authConfig';
import Sidebar from './components/Sidebar';
import ChatUI from './components/ChatUI';

const INITIAL_MESSAGE = {
  id: 1,
  text: "Hello! I'm Nexus intelligence. How can I assist you today? I'm programmed to answer questions, guide you through complex problems, and engage in conversation.",
  sender: 'bot',
  timestamp: new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  }),
};

function App() {
  // ── Auth ────────────────────────────────────────────────────
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  const handleLogin = () => {
    instance.loginPopup(loginRequest).catch((e) => console.error(e));
  };

  const handleLogout = () => {
    instance.logoutPopup().catch((e) => console.error(e));
  };

  /**
   * Acquire an access token silently for the current user.
   * Called by ChatUI before each API request.
   */
  const getAccessToken = async () => {
    if (!isAuthenticated || !accounts[0]) return '';
    try {
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: accounts[0],
      });
      return tokenResponse.accessToken;
    } catch (error) {
      console.warn(
        'Could not silently fetch token, prompt login again if needed.'
      );
      return '';
    }
  };

  // ── Chat State ─────────────────────────────────────────────
  const [chats, setChats] = useState(() => {
    const savedChats = sessionStorage.getItem('nexusChats');
    if (savedChats) {
      return JSON.parse(savedChats);
    }
    return [
      {
        id: Date.now(),
        title: 'New Conversation',
        messages: [INITIAL_MESSAGE],
      },
    ];
  });

  const [activeChatId, setActiveChatId] = useState(() => {
    const savedActiveId = sessionStorage.getItem('nexusActiveChatId');
    if (savedActiveId && savedActiveId !== 'undefined') {
      return JSON.parse(savedActiveId);
    }
    return chats[0]?.id;
  });

  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Sync to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('nexusChats', JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    sessionStorage.setItem(
      'nexusActiveChatId',
      JSON.stringify(activeChatId)
    );
  }, [activeChatId]);

  const activeChat = chats.find((c) => c.id === activeChatId) || chats[0];

  // ── Chat helpers ───────────────────────────────────────────
  const updateChatMessages = (chatId, updaterFunction) => {
    setChats((prevChats) =>
      prevChats.map((chat) => {
        if (chat.id === chatId) {
          const newMessages = updaterFunction(chat.messages);
          let newTitle = chat.title;
          if (
            chat.title === 'New Conversation' &&
            newMessages.length > 1
          ) {
            const firstUserMsg = newMessages.find(
              (m) => m.sender === 'user'
            );
            if (firstUserMsg) {
              newTitle =
                firstUserMsg.text.slice(0, 30) +
                (firstUserMsg.text.length > 30 ? '...' : '');
            }
          }
          return { ...chat, title: newTitle, messages: newMessages };
        }
        return chat;
      })
    );
  };

  const handleNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: 'New Conversation',
      messages: [
        {
          ...INITIAL_MESSAGE,
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        },
      ],
    };
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    if (window.innerWidth <= 768) setIsSidebarOpen(false);
  };

  const handleSelectChat = (id) => {
    setActiveChatId(id);
    if (window.innerWidth <= 768) setIsSidebarOpen(false);
  };

  // ── Render ─────────────────────────────────────────────────
  return (
    <div className="app-container">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        isAuthenticated={isAuthenticated}
        accountName={accounts[0]?.name?.split(' ')[0]}
        isSidebarOpen={isSidebarOpen}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />

      <ChatUI
        activeChat={activeChat}
        isTyping={isTyping}
        setIsTyping={setIsTyping}
        updateChatMessages={updateChatMessages}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        getAccessToken={getAccessToken}
      />
    </div>
  );
}

export default App;
