import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import type { SourceDocument } from '@/stores/chatStore';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
}

interface ChatMessageListProps {
  messages: Message[];
}

export const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4">
      {messages.map((msg, idx) => (
        <ChatMessage key={idx} role={msg.role} content={msg.content} sources={msg.sources} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};
