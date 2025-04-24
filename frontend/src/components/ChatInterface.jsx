import { useState, useRef, useEffect } from 'react';
import { useUser } from '@clerk/clerk-react';
import { chatService, authService } from '../services/apiService';
import ReactMarkdown from 'react-markdown';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: "Hello! I'm your Social Media Analytics Assistant. How can I help you today? You can ask me about post performance, best times to post, or improvement recommendations.", 
      sender: 'bot' 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const { user, isSignedIn } = useUser();

  // Set up user in local storage for API calls
  useEffect(() => {
    if (isSignedIn && user) {
      authService.setUserId(user.id);
    }
  }, [isSignedIn, user]);

  // Load chat history on mount
  useEffect(() => {
    const loadChatHistory = async () => {
      if (isSignedIn) {
        try {
          const history = await chatService.getChatHistory();
          if (history && history.length > 0) {
            const formattedHistory = history.map((msg, index) => ({
              id: index,
              text: msg.content,
              sender: msg.role === 'assistant' ? 'bot' : 'user'
            }));
            setMessages(formattedHistory);
          }
        } catch (error) {
          console.error('Failed to load chat history:', error);
        }
      }
    };

    loadChatHistory();
  }, [isSignedIn]);

  // Scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage = { id: Date.now(), text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call API to get response
      const response = await chatService.sendMessage(input);
      
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: response, 
        sender: 'bot' 
      }]);
    } catch (error) {
      console.error('Error getting response:', error);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: "I'm having trouble connecting to the analytics service. Please try again.", 
        sender: 'bot' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick suggestion buttons
  const suggestions = [
    "What's the best time to post reels?",
    "How do carousels compare to images?",
    "What can I do to improve engagement?",
    "Which post type performs best?"
  ];

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-xs lg:max-w-md p-3 rounded-lg ${
                message.sender === 'user' 
                  ? 'bg-indigo-600 text-white rounded-br-none' 
                  : 'bg-white shadow-md border border-gray-200 text-gray-800 rounded-bl-none'
                }`}
            >
              <div className={`prose prose-sm max-w-none ${message.sender === 'user' ? 'prose-invert' : ''}`}>
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white shadow-md border border-gray-200 text-gray-800 p-3 rounded-lg rounded-bl-none max-w-xs lg:max-w-md">
              <div className="flex space-x-2">
                <div className="w-2 h-2 rounded-full bg-gray-600 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-gray-600 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 rounded-full bg-gray-600 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Suggestion chips */}
      {messages.length <= 2 && (
        <div className="px-4 py-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm px-3 py-1 rounded-full"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your social media analytics..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-indigo-400"
            disabled={isLoading || !input.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;