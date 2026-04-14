/**
 * ============================================================
 *  MessageBubble Component
 * ============================================================
 *  Renders a single chat message — user or bot — complete with
 *  Markdown rendering, syntax highlighting, and timestamp.
 * ============================================================
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function MessageBubble({ message }) {
  const { text, sender, timestamp, responseTime } = message;

  return (
    <div className={`message-wrapper ${sender}`}>
      <div className="message-bubble">
        {sender === 'bot' ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    children={String(children).replace(/\n$/, '')}
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  />
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {text}
          </ReactMarkdown>
        ) : (
          text
        )}
      </div>
      <div className="message-time">
        {timestamp}
        {responseTime && (
          <span style={{ marginLeft: '8px', opacity: 0.7 }}>
            ⚡ {responseTime}s
          </span>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
