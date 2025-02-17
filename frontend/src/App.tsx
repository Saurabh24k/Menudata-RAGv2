import React, { useEffect, useRef, useState } from 'react';
import { Search, MessageSquarePlus, Menu, X } from 'lucide-react';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { SourceCard } from './components/SourceCard';
import { useChatStore } from './store';

const SUGGESTED_QUESTIONS = [
  'Where can I find vegan pizza?',
  'Where can I find Pad Thai?',
  'How to make Pizza?',
  'Where can I get Pizza with Pineapple?',
];

function App() {
  const { messages, isTyping, addMessage, sources } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [hasMounted, setHasMounted] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
    if (!hasMounted) setHasMounted(true);
  }, [messages, hasMounted]);

  const handleSendMessage = (content: string) => {
    addMessage({
      content,
      role: 'user',
      status: 'sending',
    });
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Mobile Sidebar Toggle */}
      <button
        onClick={toggleSidebar}
        className="fixed bottom-4 right-4 z-50 p-3 bg-blue-500 text-white rounded-full shadow-lg md:hidden transition-transform hover:scale-105"
      >
        {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      <div className="flex flex-1 flex-col w-full">
        <header className="flex items-center justify-between border-b bg-white px-4 py-3 shadow-sm md:px-6 md:py-4">
          <h1 className="text-lg font-semibold text-gray-800 md:text-xl">Menudata Expert</h1>
          <div className="flex items-center gap-2 md:gap-4">
            <button className="hidden md:flex rounded-full bg-gray-100 p-2 text-gray-600 transition-all duration-200 hover:bg-gray-200 hover:shadow-md active:scale-95">
              <Search className="h-5 w-5" />
            </button>
            <button className="hidden md:flex rounded-full bg-gray-100 p-2 text-gray-600 transition-all duration-200 hover:bg-gray-200 hover:shadow-md active:scale-95">
              <MessageSquarePlus className="h-5 w-5" />
            </button>
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          {/* Main Chat Area */}
          <div className="flex-1 overflow-hidden bg-white relative">
            <div className="flex h-full flex-col">
              <div className="flex-1 overflow-y-auto p-2 md:p-4">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {isTyping && (
                  <div className="flex items-center gap-2 p-4 animate-fade-in">
                    <div className="h-8 w-8 animate-pulse rounded-full bg-gray-200" />
                    <div className="flex gap-1">
                      <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
                      <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:0.2s]" />
                      <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:0.4s]" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <ChatInput onSend={handleSendMessage} />
            </div>
          </div>

          {/* Sidebar */}
          <div className={`absolute inset-y-0 right-0 w-full max-w-xs bg-gray-50 shadow-lg transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${
            isSidebarOpen ? 'translate-x-0' : 'translate-x-full'
          } md:translate-x-0 z-40`}>
            <div className="h-full overflow-y-auto p-4">
              <button
                onClick={toggleSidebar}
                className="md:hidden mb-4 text-gray-600 hover:text-gray-800 transition-colors"
              >
                <X size={24} />
              </button>

              <div className="space-y-6">
                <div>
                  <h2 className="mb-3 font-semibold text-gray-800 text-lg">Sources</h2>
                  <div className="grid gap-2">
                    {sources.map((source, index) => (
                      <SourceCard key={index} source={source} />
                    ))}
                  </div>
                </div>

                <div>
                  <h2 className="mb-3 font-semibold text-gray-800 text-lg">Suggested Questions</h2>
                  <div className="grid gap-2">
                    {SUGGESTED_QUESTIONS.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSendMessage(question)}
                        className="w-full text-left p-3 text-sm bg-white rounded-lg shadow-sm transition-all duration-200 hover:bg-gray-50 hover:shadow-md active:scale-[0.98]"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;