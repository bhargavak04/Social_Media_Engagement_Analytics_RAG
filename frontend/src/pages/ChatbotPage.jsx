import Navbar from '../components/Navbar';
import ChatInterface from '../components/ChatInterface';

const ChatbotPage = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 sm:px-6 bg-gradient-to-r from-indigo-600 to-purple-500">
            <h3 className="text-lg leading-6 font-medium text-white">
              Social Media Analytics Chatbot
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-indigo-100">
              Ask questions about your social media engagement data
            </p>
          </div>
          <div className="h-[calc(100vh-12rem)]">
            <ChatInterface />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotPage;
