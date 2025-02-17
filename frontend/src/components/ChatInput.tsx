import React, { useState, useRef } from 'react';
import { Smile, Paperclip, Send } from 'lucide-react';
import data from '@emoji-mart/data';
import Picker from '@emoji-mart/react';
import { cn } from '../utils'; // Import cn utility - as dummy code uses it

interface ChatInputProps {
  onSend: (message: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend }) => {
  const [message, setMessage] = useState('');
  const [showEmoji, setShowEmoji] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // Added isSubmitting state
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => { // Make handleSubmit async
    console.log("ChatInput.tsx - handleSubmit START - message input:", message);
    e.preventDefault();
    if (message.trim() && !isSubmitting) { // Add isSubmitting check
      setIsSubmitting(true); // Set isSubmitting to true
      console.log("ChatInput.tsx - handleSubmit - BEFORE onSend call - message:", message.trim());
      await onSend(message.trim()); // Await onSend call
      console.log("ChatInput.tsx - handleSubmit - AFTER onSend call - message:", message.trim());
      setMessage('');
      console.log("ChatInput.tsx - handleSubmit - setMessage('') called, message state reset");
      setIsSubmitting(false); // Set isSubmitting back to false
    } else {
      console.log("ChatInput.tsx - handleSubmit - message is empty or whitespace, or submitting, not sending");
    }
    console.log("ChatInput.tsx - handleSubmit END");
  };

  const handleEmojiSelect = (emoji: any) => {
    setMessage((prev) => prev + emoji.native);
    setShowEmoji(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Handle file upload
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setMessage((prev) =>
            prev + `\nUploaded file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`
          );
        }
      };
      reader.readAsText(file);
    }
  };


  return (
    <form
      onSubmit={handleSubmit}
      className="relative flex items-center gap-2 border-t bg-white p-4 animate-fade-in"
    >
      <div className="relative flex flex-1 items-center gap-2 rounded-2xl border border-gray-200 bg-white px-4 py-2 shadow-sm transition-all duration-200 focus-within:border-blue-500 focus-within:shadow-md"> {/* Input area container from dummy code */}
        <button
          type="button"
          onClick={() => setShowEmoji(!showEmoji)}
          className="text-gray-400 transition-colors duration-200 hover:text-gray-600 flex-shrink-0" // Adjusted classes and flex-shrink
        >
          <Smile className="h-5 w-5 transition-transform hover:scale-110" /> {/* Icon size from dummy code */}
        </button>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 text-gray-400 transition-colors duration-200 hover:text-gray-600" // Classes from dummy code and flex-shrink
        >
          <Paperclip className="h-5 w-5 transition-transform hover:scale-110" /> {/* Icon size from dummy code */}
        </button>
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange} // Use handleFileChange from dummy code (and actual code logic)
        />
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 bg-transparent text-gray-700 placeholder-gray-400 outline-none" // Input classes from dummy code - adjusted and simplified, removed rounded-full, border, focus styles as container handles that now
        />
      </div>
      <button
        type="submit"
        disabled={!message.trim() || isSubmitting} // Disable logic from dummy code
        className={cn( // cn utility from dummy code
          'group relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-all duration-200',
          message.trim()
            ? 'bg-blue-500 text-white shadow-md hover:bg-blue-600'
            : 'bg-gray-100 text-gray-400'
        )}
      >
        <Send
          className={cn(
            'h-4 w-4 transition-all duration-200',
            message.trim() && 'group-hover:translate-x-0.5 group-hover:-translate-y-0.5'
          )}
        />
        {isSubmitting && (
          <div className="absolute inset-0 flex items-center justify-center rounded-full bg-blue-500">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          </div>
        )}
      </button>
      {showEmoji && (
        <div className="absolute bottom-full right-0 mb-2 animate-scale-in"> {/* Emoji picker position from actual code */}
          <Picker data={data} onEmojiSelect={handleEmojiSelect} />
        </div>
      )}
    </form>
  );
};