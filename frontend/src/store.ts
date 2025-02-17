// store.ts
import { create } from 'zustand';
import { ChatState, Message, Source } from './types';

const API_BASE = '/api'; 

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isTyping: false,
  sources: [], // Initialize sources array in the store
  error: null,
  sendMessage: (message: string) => get().addMessage({ content: message, role: 'user', status: 'sending' as const }),

  addMessage: (message) => {
    let userMessage: Message;

    console.log("addMessage START - message:", message); // LOG START

    userMessage = {
      id: Math.random().toString(36).substring(7),
      ...message,
      timestamp: new Date(),
      feedback: null,
      status: 'sending'
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isTyping: true
    }));

    console.log("API CALL - message.content:", message.content, "Current messages state:", get().messages); // LOG API CALL

    fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message.content,
        history: get().messages
      })
    })
      .then(response => {
        if (!response.ok) throw new Error('API Error');
        return response.json();
      })
      .then(data => {
        console.log("API SUCCESS - response data:", data); // LOG API SUCCESS

        const assistantMessage: Message = {
          id: Math.random().toString(36).substring(7),
          content: data.response, // Use data.response for message content ONLY
          role: 'assistant',
          timestamp: new Date(),
          status: 'read' as const,
          feedback: null,
          sources: data.sources, // Keep sources in the message object for now (might be used in ChatMessage later, or remove if not needed)
        };

        const newMessagesStateSuccess = state => (
          state.messages.map(msg =>
            msg.id === userMessage.id ? { ...msg, status: 'delivered' as const } : msg
          ).concat([assistantMessage])
        );
        console.log("SET STATE (SUCCESS) - new messages state (before set):", newMessagesStateSuccess({messages: get().messages})); // LOG SET STATE (SUCCESS) - before set

        set((state) => ({
          messages: newMessagesStateSuccess(state),
          isTyping: false,
          error: null,
          sources: data.sources, // **UPDATE ZUSTAND SOURCES ARRAY HERE** with data.sources from API response
        }));
      })
      .catch(error => {
        console.error('API Error:', error);
        console.log("API ERROR - error:", error); // LOG API ERROR

        const newMessagesStateError = state => (
          state.messages.map(msg =>
            msg.id === userMessage?.id ? { ...msg, status: 'error' as const } : msg
          )
        );
        console.log("SET STATE (ERROR) - new messages state (before set):", newMessagesStateError({messages: get().messages})); // LOG SET STATE (ERROR) - before set

        set((state) => ({
          messages: newMessagesStateError(state),
          isTyping: false,
          error: error instanceof Error ? error.message : 'Unknown API error'
        }));
      })
      .finally(() => {
        set({ isTyping: false });
        console.log("addMessage END"); // LOG END
      });
  },

  setFeedback: async (messageId, feedback) => {
    try {
      const message = get().messages.find(m => m.id === messageId);
      if (!message || message.role !== 'assistant') {
        console.warn("Feedback can only be given for assistant messages.");
        return;
      }

      let userQuery = "No User Query Found";
      const messageIndex = get().messages.findIndex(m => m.id === messageId);
      for (let i = messageIndex - 1; i >= 0; i--) {
        if (get().messages[i].role === 'user') {
          userQuery = get().messages[i].content;
          break;
        }
      }

      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          response: message.content,
          type: feedback
        })
      });

      set((state) => ({
        messages: state.messages.map(msg =>
          msg.id === messageId ? { ...msg, feedback } : msg
        )
      }));

    } catch (error) {
      console.error('Feedback Error:', error);
    }
  },

  setTyping: (typing) => set({ isTyping: typing })
}));