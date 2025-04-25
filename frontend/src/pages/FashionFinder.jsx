import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

// Character constants
const PERSONAS = {
  VINCENT: {
    name: "Vincent",
    title: "Fashion Curator",
    icon: "user-tie",
    greeting: "Welcome to our exclusive collection! I'm Vincent, your personal fashion curator. How may I assist you today?",
    description: "Vincent is our senior fashion curator with 15 years of experience in luxury retail. He has an impeccable eye for quality and style."
  },
  SOPHIA: {
    name: "Sophia",
    title: "Style Director",
    icon: "user-graduate",
    greeting: "Hello! I'm Sophia, your style director. Looking for something special in our collection?",
    description: "Sophia is our creative style director who keeps up with the latest trends and can help you find exactly what you're looking for."
  },
  MARCUS: {
    name: "Marcus",
    title: "Personal Shopper",
    icon: "store",
    greeting: "Hey there! I'm Marcus, your personal shopper. Tell me what you're looking for and I'll find it in our collection!",
    description: "Marcus is our energetic personal shopper who specializes in finding unique pieces that match your personal style."
  }
}

// Helper function to format time
const formatTime = (date) => {
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const formattedHours = hours % 12 || 12;
  const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
  return `${formattedHours}:${formattedMinutes} ${ampm}`;
};

function FashionFinder() {
  // State for the selected character
  const [selectedPersona, setSelectedPersona] = useState(PERSONAS.VINCENT);
  
  // State for the chat
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [displayedImage, setDisplayedImage] = useState(null);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(false);
  
  // Refs
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);
  
  // Suggested fashion queries
  const suggestedQueries = [
    {
      id: 1,
      text: "Show me a red summer dress",
      icon: "sun",
      color: "bg-red-500",
    },
    {
      id: 2,
      text: "Do you have any blue denim jackets?",
      icon: "tshirt",
      color: "bg-blue-500",
    },
    {
      id: 3,
      text: "I need a black leather handbag",
      icon: "shopping-bag",
      color: "bg-gray-800",
    },
    {
      id: 4,
      text: "I want an all white outfit for Amr Diab's Concert",
      icon: "shoe-prints",
      color: "bg-purple-500",
    },
    {
      id: 5,
      text: "I'm looking for a formal suit",
      icon: "user-tie",
      color: "bg-gray-700",
    }
  ];

  // Initialize chat with greeting
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: selectedPersona.greeting,
        timestamp: new Date(),
        persona: selectedPersona.name
      }
    ]);
    // Initial scroll is allowed
    setTimeout(() => scrollToBottom(), 100);
  }, [selectedPersona]);

  // Manual scroll to bottom - NEVER automatic
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Only scroll when explicitly requested via the shouldScrollToBottom state
  useEffect(() => {
    if (shouldScrollToBottom) {
      scrollToBottom();
      setShouldScrollToBottom(false);
    }
  }, [shouldScrollToBottom]);

  // Function to handle manual scroll to bottom
  const handleScrollToBottom = () => {
    scrollToBottom();
  };

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Function to handle image downloads
  const handleDownloadImage = (imageUrl, query) => {
    // Create a safe filename from the query
    const safeQuery = query.toLowerCase().replace(/[^a-z0-9]+/g, '-').substring(0, 30);
    const fileName = `fashion-item-${safeQuery}-${Date.now()}.jpg`;
    
    // Create a temporary link element
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Add user message to chat
    const userMessage = { 
      role: 'user', 
      content: input, 
      timestamp: new Date() 
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Store the current query for reference
    const currentQuery = input;
    
    // Clear input and show loading state
    setInput('');
    setLoading(true);
    setError(null);
    setShowSuggestions(false);
    
    // Scroll to bottom when user sends a message
    scrollToBottom();

    try {
      // First, check if the query is valid
      const checkResponse = await axios.post('/api/check-query', {
        query: currentQuery
      });
      
      if (checkResponse.data.is_clothing_related) {
        // Add a processing message
        const processingMessage = {
          role: 'assistant',
          content: `Let me find that for you. One moment please...`,
          timestamp: new Date(),
          persona: selectedPersona.name,
          isProcessing: true
        };
        setMessages(prev => [...prev, processingMessage]);
        
        // No auto-scroll after adding processing message
        
        // Then get the actual image
        const imageResponse = await axios.post('/api/text-search', {
          query: currentQuery
        }, {
          responseType: 'blob' // Important: we need to get a blob for the image
        });
        
        // Create a URL for the image blob
        const imageUrl = URL.createObjectURL(imageResponse.data);
        setDisplayedImage(imageUrl);
        
        // Add the result message
        const successMessage = {
          role: 'assistant',
          content: `I found this item matching your request:`,
          timestamp: new Date(),
          persona: selectedPersona.name,
          image: imageUrl,
          relatedQuery: currentQuery // Store the query that produced this image
        };
        
        // Replace the processing message with the success message
        setMessages(prev => prev.map(msg => 
          msg.isProcessing ? successMessage : msg
        ));
        
        // No auto-scroll after adding success message
      } else {
        // If query is not fashion-related
        const invalidMessage = {
          role: 'assistant',
          content: `I'm sorry, but I can only help with fashion-related requests. Could you please ask about clothing items, accessories, or other fashion items?`,
          timestamp: new Date(),
          persona: selectedPersona.name
        };
        setMessages(prev => [...prev, invalidMessage]);
      }
    } catch (error) {
      console.error('Error processing request:', error);
      
      let errorMessage = "I apologize, but I'm having trouble finding what you're looking for.";
      
      // Get more specific error message if available
      if (error.response) {
        if (error.response.status === 400) {
          errorMessage = "I'm sorry, but I can only help with fashion-related requests. Could you please ask about clothing items, accessories, or other fashion items?";
        } else if (error.response.status === 404) {
          errorMessage = "I'm sorry, but I couldn't find any items matching your description in our collection.";
        } else {
          errorMessage = `I apologize, but there was an issue processing your request. ${error.response.data?.detail || ''}`;
        }
      }
      
      setError(errorMessage);
      
      // Add error message to chat
      const errorMsg = {
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date(),
        persona: selectedPersona.name,
        isError: true
      };
      
      // Replace processing message if it exists, otherwise add new message
      setMessages(prev => {
        const hasProcessing = prev.some(msg => msg.isProcessing);
        if (hasProcessing) {
          return prev.map(msg => msg.isProcessing ? errorMsg : msg);
        } else {
          return [...prev, errorMsg];
        }
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion.text);
    inputRef.current?.focus();
  };

  const changePersona = (persona) => {
    setSelectedPersona(PERSONAS[persona]);
    setShowSuggestions(true);
    setDisplayedImage(null);
  };

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: selectedPersona.greeting,
      timestamp: new Date(),
      persona: selectedPersona.name
    }]);
    setShowSuggestions(true);
    setError(null);
    setDisplayedImage(null);
  };

  return (
    <div className="py-8 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-secondary-600 mb-2">
            Fashion Finder
          </h1>
          <p className="text-lg text-gray-600">
            Describe what you're looking for and our fashion experts will find it in our collection
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar with store assistants & suggestions */}
          <div className="w-full lg:w-80 flex-shrink-0 space-y-8">
            {/* Store assistants */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
              <div className="bg-gradient-to-r from-secondary-700 to-secondary-800 text-white p-4">
                <h3 className="font-medium flex items-center">
                  <i className="fas fa-user-friends mr-2"></i>
                  Select Your Fashion Assistant
                </h3>
              </div>
              
              <div className="divide-y divide-gray-100">
                {Object.entries(PERSONAS).map(([key, persona]) => (
                  <button
                    key={key}
                    onClick={() => changePersona(key)}
                    className={`w-full p-4 flex items-center text-left transition-all duration-300 
                      ${selectedPersona.name === persona.name 
                        ? 'bg-secondary-50 border-l-4 border-secondary-500' 
                        : 'hover:bg-gray-50'}`}
                  >
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center 
                      ${selectedPersona.name === persona.name 
                        ? 'bg-secondary-100 text-secondary-600' 
                        : 'bg-gray-100 text-gray-500'}`}>
                      <i className={`fas fa-${persona.icon} text-xl`}></i>
                    </div>
                    <div className="ml-4">
                      <div className="font-medium">{persona.name}</div>
                      <div className="text-sm text-gray-500">{persona.title}</div>
                    </div>
                    {selectedPersona.name === persona.name && (
                      <div className="ml-auto text-secondary-500">
                        <i className="fas fa-check-circle"></i>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Suggestions */}
            {showSuggestions && (
              <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200 p-4">
                <h3 className="font-medium text-primary-700 mb-4 flex items-center">
                  <i className="fas fa-lightbulb text-yellow-500 mr-2"></i>
                  Popular Searches
                </h3>
                
                <div className="space-y-3">
                  {suggestedQueries.map((suggestion) => (
                    <button
                      key={suggestion.id}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left p-3 transition-all duration-300 border
                        bg-white border-gray-200 hover:bg-gray-50 hover:shadow-md hover:-translate-y-1
                        rounded-lg group overflow-hidden"
                    >
                      <div className="relative z-10 flex items-start">
                        <div className={`${suggestion.color} w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center text-white mr-3`}>
                          <i className={`fas fa-${suggestion.icon}`}></i>
                        </div>
                        <div className="text-sm text-gray-700 font-medium">
                          {suggestion.text}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Current assistant info card */}
            <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-xl shadow-sm overflow-hidden border border-gray-200 p-5">
              <div className="flex items-center mb-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-secondary-100 to-primary-100 flex items-center justify-center text-secondary-600">
                  <i className={`fas fa-${selectedPersona.icon} text-xl`}></i>
                </div>
                <div className="ml-3">
                  <h3 className="font-bold text-secondary-800">{selectedPersona.name}</h3>
                  <p className="text-sm text-secondary-600">{selectedPersona.title}</p>
                </div>
              </div>
              <p className="text-gray-600 text-sm">{selectedPersona.description}</p>
            </div>
          </div>
          
          {/* Chat container */}
          <div className="flex-1 bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200 flex flex-col h-[700px]">
            {/* Chat header */}
            <div className="bg-gradient-to-r from-secondary-700 to-secondary-800 text-white p-4 flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center mr-3">
                  <i className={`fas fa-${selectedPersona.icon}`}></i>
                </div>
                <div>
                  <h3 className="font-medium">{selectedPersona.name}</h3>
                  <div className="text-xs text-secondary-200 flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    Online
                  </div>
                </div>
              </div>
              <button 
                onClick={clearChat}
                className="text-white/80 hover:text-white transition-colors"
                title="Clear chat"
              >
                <i className="fas fa-trash-alt"></i>
              </button>
            </div>
            
            {/* Chat messages */}
            <div 
              ref={chatContainerRef} 
              className="flex-1 overflow-y-auto p-4 bg-pattern-light"
            >
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div 
                    key={index} 
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div 
                      className={`rounded-2xl px-4 py-3 max-w-sm lg:max-w-md 
                        ${message.role === 'user'
                          ? 'bg-primary-500 text-white ml-12'
                          : message.isError
                            ? 'bg-red-50 border border-red-200 text-red-800 mr-12'
                            : message.isProcessing
                              ? 'bg-gray-100 text-gray-800 mr-12 animate-pulse'
                              : 'bg-white border border-gray-200 text-gray-800 mr-12 shadow-sm'
                        }`}
                    >
                      {message.role === 'assistant' && (
                        <div className="flex items-center mb-1">
                          <div className="w-6 h-6 rounded-full flex items-center justify-center bg-secondary-100 text-secondary-600 mr-2">
                            <i className={`fas fa-${selectedPersona.icon} text-xs`}></i>
                          </div>
                          <span className="text-xs font-medium text-gray-500">
                            {message.persona} • {formatTime(new Date(message.timestamp))}
                          </span>
                        </div>
                      )}
                      
                      <div className={`${message.role === 'user' ? 'text-white' : 'text-gray-800'}`}>
                        {message.content}
                      </div>
                      
                      {message.image && (
                        <div className="mt-3 rounded-lg overflow-hidden border shadow-sm relative group">
                          <img 
                            src={message.image} 
                            alt="Fashion item" 
                            className="w-full object-cover"
                          />
                          <div className="absolute bottom-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleDownloadImage(message.image, message.relatedQuery || "fashion-item")}
                              className="bg-white/90 hover:bg-white text-secondary-700 p-2 rounded-full shadow-md transition-all hover:scale-105"
                              title="Download image"
                            >
                              <i className="fas fa-download"></i>
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {message.role === 'user' && (
                        <div className="text-right mt-1">
                          <span className="text-xs text-white/80">
                            {formatTime(new Date(message.timestamp))}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Loading indicator */}
                {loading && !messages.some(m => m.isProcessing) && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 mr-12 shadow-sm">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '200ms' }}></div>
                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '400ms' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </div>
            
            {/* Chat input */}
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-between items-center mb-2">
                <div className="text-xs text-gray-500">
                  <i className="fas fa-info-circle mr-1"></i>
                  Ask about specific clothing items, colors, styles, or occasions
                </div>
                
                {messages.length > 3 && (
                  <button 
                    onClick={handleScrollToBottom}
                    className="text-xs text-secondary-600 hover:text-secondary-800 flex items-center"
                    title="Scroll to bottom"
                  >
                    <i className="fas fa-arrow-down mr-1"></i>
                    Scroll to latest
                  </button>
                )}
              </div>
              
              <form onSubmit={handleSubmit} className="flex items-center space-x-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Describe what you're looking for..."
                    className="w-full pl-4 pr-10 py-3 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    ref={inputRef}
                    disabled={loading}
                  />
                  {input && (
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      onClick={() => setInput('')}
                    >
                      <i className="fas fa-times"></i>
                    </button>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className={`rounded-full w-12 h-12 flex items-center justify-center 
                    ${loading || !input.trim()
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-primary-500 text-white hover:bg-primary-600'
                    } transition-colors`}
                >
                  <i className="fas fa-arrow-right"></i>
                </button>
              </form>
              
              {error && (
                <div className="mt-2 text-xs text-red-600">
                  <i className="fas fa-exclamation-circle mr-1"></i>
                  {error}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FashionFinder; 