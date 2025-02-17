import React from 'react';
import { format } from 'date-fns';
import { Check, CheckCheck, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Message } from '../types';
import { cn } from '../utils';
import { useChatStore } from '../store';

interface ChatMessageProps {
  message: Message;
}

interface StatusIcons {
  sending: null;
  sent: React.ReactElement | null;
  delivered: React.ReactElement | null;
  read: React.ReactElement | null;
  error: React.ReactElement | null;
}

const statusIcons: StatusIcons = {
  sending: null,
  sent: <Check className="h-4 w-4" />,
  delivered: <CheckCheck className="h-4 w-4" />,
  read: <CheckCheck className="h-4 w-4 text-blue-500" />,
  error: <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4 text-red-500">
           <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-2.067 7.417a.75.75 0 011.068 0L12 10.933l1.068-1.25a.75.75 0 111.068 1.068L13.067 12l1.068 1.25a.75.75 0 11-1.068 1.068L12 13.067l-1.068 1.25a.75.75 0 11-1.068-1.068L10.933 12l-1.068-1.25a.75.75 0 010-1.068z" clipRule="evenodd" />
         </svg>
};

export const ChatMessage: React.FC<ChatMessageProps> = React.memo(({ message }) => {
  const isUser = message.role === 'user';
  const setFeedback = useChatStore((state) => state.setFeedback);

  const handleFeedback = (feedback: 'good' | 'bad') => {
    setFeedback(message.id, message.feedback === feedback ? null : feedback);
  };

  return (
    <div
      className={cn(
        'flex w-full gap-3 p-4 animate-slide-in',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div className="flex max-w-[80%] flex-col gap-2">
        <div
          className={cn(
            'flex items-end gap-2',
            isUser ? 'flex-row-reverse' : 'flex-row'
          )}
        >
          <div
            className={cn(
              'h-8 w-8 rounded-full bg-cover bg-center transition-transform hover:scale-105',
              isUser
                ? 'bg-[url(https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=80&h=80&fit=crop)]'
                : 'bg-[url(https://images.unsplash.com/photo-1563898989-f9cd1aa9ef0f?w=80&h=80&fit=crop)]'
            )}
          />
          <div
            className={cn(
              'rounded-2xl px-4 py-2 transition-all duration-200 hover:shadow-md',
              isUser
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
            )}
          >
            <p className="text-sm whitespace-pre-line">{message.content}</p>
          </div>
        </div>
        <div
          className={cn(
            'flex items-center gap-2 text-xs',
            isUser ? 'flex-row-reverse' : 'flex-row'
          )}
        >
          <span className="text-gray-500">{format(message.timestamp, 'HH:mm')}</span>
          {/* REMOVED THE USER MESSAGE STATUS ICONS HERE */}
          {!isUser && (
            <div className="flex items-center gap-1 animate-fade-in">
              <button
                onClick={() => handleFeedback('good')}
                className={cn(
                  'p-1 rounded-full transition-all duration-200 hover:bg-green-50',
                  message.feedback === 'good'
                    ? 'text-green-500 bg-green-50'
                    : 'text-gray-400 hover:text-green-500'
                )}
              >
                <ThumbsUp className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleFeedback('bad')}
                className={cn(
                  'p-1 rounded-full transition-all duration-200 hover:bg-red-50',
                  message.feedback === 'bad'
                    ? 'text-red-500 bg-red-50'
                    : 'text-gray-400 hover:text-red-500'
                )}
              >
                <ThumbsDown className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});