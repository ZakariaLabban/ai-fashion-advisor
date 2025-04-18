import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

// Simple function to format time in 12-hour format (e.g., "3:45 PM")
const formatTime = (date) => {
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const formattedHours = hours % 12 || 12; // Convert 0 to 12 for 12 AM
  const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
  return `${formattedHours}:${formattedMinutes} ${ampm}`;
};

function Chatbot() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: "Hello! I'm Elegance, your fashion AI assistant. How can I help you with your style today?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(true)
  const [activeSuggestion, setActiveSuggestion] = useState(null)
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null) // New ref for the chat container
  const inputRef = useRef(null)

  const suggestedQuestions = [
    {
      id: 1,
      text: "What colors match well with navy blue?",
      icon: "palette",
      color: "bg-blue-500",
    },
    {
      id: 2,
      text: "How can I style a white button-down shirt?",
      icon: "tshirt",
      color: "bg-indigo-500",
    },
    {
      id: 3,
      text: "What's trending in men's fashion this season?",
      icon: "fire",
      color: "bg-orange-500",
    },
    {
      id: 4,
      text: "How do I dress for a casual business meeting?",
      icon: "briefcase",
      color: "bg-teal-500",
    },
    {
      id: 5,
      text: "What accessories work best with a little black dress?",
      icon: "gem",
      color: "bg-purple-500",
    }
  ]

  // Generate a session ID when the component mounts
  useEffect(() => {
    setSessionId(`session_${Date.now()}`)
    // Scroll to bottom once on initial load
    setTimeout(() => scrollToBottom(), 100)
  }, [])

  // No auto-scrolling with messages changes
  // This useEffect has been removed

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Manual scroll to bottom function
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Function to handle manual scroll to bottom
  const handleScrollToBottom = () => {
    scrollToBottom()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim()) return
    
    // Add user message to chat
    const userMessage = { role: 'user', content: input, timestamp: new Date() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)
    setShowSuggestions(false)
    
    // Scroll to bottom when user sends a message
    scrollToBottom()

    try {
      const response = await axios.post('/api/elegance/chat', {
        message: input,
        session_id: sessionId
      })

      // Add assistant response to chat
      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.response || "I'm sorry, I couldn't process your request.",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      // No auto-scroll after adding response
    } catch (error) {
      console.error('Error sending message to Elegance:', error)
      
      setError('Connection error. Please try again later.')
      
      // Add error message
      const errorMessage = { 
        role: 'assistant', 
        content: "I apologize, but I'm having trouble connecting to my fashion knowledge. Please try again later.",
        timestamp: new Date(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
      // No auto-scroll after adding error message
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion.text)
    setActiveSuggestion(null)
    inputRef.current?.focus()
  }

  const handleSuggestionHover = (id) => {
    setActiveSuggestion(id)
  }

  const clearChat = () => {
    setMessages([{ 
      role: 'assistant', 
      content: "Hello! I'm Elegance, your fashion AI assistant. How can I help you with your style today?",
      timestamp: new Date()
    }])
    setShowSuggestions(true)
    setError(null)
    // Scroll to bottom once after clearing chat
    setTimeout(() => scrollToBottom(), 100)
  }

  return (
    <div className="py-8 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-secondary-600 mb-2">Elegance Bot</h1>
          <p className="text-lg text-gray-600">
            Your personal AI fashion advisor to answer all your style questions
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Suggestions sidebar */}
          <div className="w-full lg:w-72 flex-shrink-0">
            <div className="sticky top-6 bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200 p-4">
              <h3 className="font-medium text-primary-700 mb-4 flex items-center">
                <i className="fas fa-lightbulb text-yellow-500 mr-2"></i>
                Quick Questions
              </h3>
              
              <div className="space-y-3">
                {suggestedQuestions.map((suggestion) => (
                  <div 
                    key={suggestion.id}
                    className="relative"
                    onMouseEnter={() => handleSuggestionHover(suggestion.id)}
                    onMouseLeave={() => handleSuggestionHover(null)}
                  >
                    <button
                      onClick={() => handleSuggestionClick(suggestion)}
                      className={`w-full text-left p-3 transition-all duration-300 border
                        ${activeSuggestion === suggestion.id 
                          ? 'bg-gradient-to-r from-gray-50 to-gray-100 border-gray-300 shadow-md transform -translate-y-1 scale-102'
                          : 'bg-white border-gray-200 hover:bg-gray-50'
                        } rounded-lg group overflow-hidden`}
                    >
                      <div className="absolute -right-8 -bottom-8 opacity-5 text-6xl transform rotate-12 group-hover:rotate-6 transition-transform">
                        <i className={`fas fa-${suggestion.icon}`}></i>
                      </div>
                      <div className="relative z-10 flex items-start">
                        <div className={`${suggestion.color} w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center text-white mr-3`}>
                          <i className={`fas fa-${suggestion.icon}`}></i>
                        </div>
                        <div className="text-sm text-gray-700 font-medium">
                          {suggestion.text}
                        </div>
                      </div>
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-5 p-3 bg-primary-50 rounded-lg border border-primary-100">
                <h4 className="text-sm font-medium text-primary-800 mb-2 flex items-center">
                  <i className="fas fa-star text-primary-500 mr-2"></i>
                  Fashion Tip
                </h4>
                <p className="text-xs text-gray-700">
                  Be specific about your fashion needs. Mention colors, occasions, body types, or style preferences for the most personalized advice.
                </p>
              </div>
            </div>
          </div>

          {/* Main chat area */}
          <div className="flex-grow">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
              {/* Chat header */}
              <div className="bg-gradient-to-r from-primary-600 to-primary-800 text-white p-4 flex justify-between items-center">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-full bg-white bg-opacity-20 backdrop-blur flex items-center justify-center mr-3">
                    <i className="fas fa-tshirt text-white text-xl"></i>
                  </div>
                  <div>
                    <h3 className="font-medium">Elegance Bot</h3>
                    <p className="text-xs opacity-75">Fashion AI Assistant</p>
                  </div>
                </div>
                <div className="flex items-center">
                  {messages.length > 2 && (
                    <button 
                      onClick={handleScrollToBottom}
                      className="text-white/80 hover:text-white mr-4 transition-colors"
                      title="Scroll to bottom"
                    >
                      <i className="fas fa-arrow-down"></i>
                    </button>
                  )}
                  <button 
                    onClick={clearChat}
                    className="text-white/80 hover:text-white transition-colors"
                    title="Clear chat"
                  >
                    <i className="fas fa-trash-alt"></i>
                  </button>
                </div>
              </div>

              {/* Error banner */}
              {error && (
                <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 flex justify-between">
                  <div className="flex items-center">
                    <i className="fas fa-exclamation-circle mr-2"></i>
                    <span>{error}</span>
                  </div>
                  <button 
                    onClick={() => setError(null)}
                    className="text-red-700 hover:text-red-800"
                  >
                    <i className="fas fa-times"></i>
                  </button>
                </div>
              )}

          {/* Chat messages area */}
          <div 
            ref={chatContainerRef}
            className="h-96 overflow-y-auto p-6 bg-gray-50"
          >
            {messages.map((message, index) => (
              <div 
                key={index}
                    className={`mb-6 ${message.role === 'user' ? 'flex flex-row-reverse' : 'flex'}`}
                  >
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center 
                        ${message.role === 'user' 
                          ? 'bg-gradient-to-br from-secondary-500 to-secondary-700 shadow-md ml-3' 
                          : 'bg-gradient-to-br from-primary-500 to-primary-700 shadow-md mr-3'}`}>
                        <i className={`fas ${message.role === 'user' ? 'fa-user' : 'fa-tshirt'} text-white`}></i>
                      </div>
                    </div>

                    {/* Message bubble */}
                    <div className="max-w-[75%]">
                      <div 
                        className={`p-4 shadow-sm ${
                    message.role === 'user' 
                            ? 'bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl rounded-tr-none' 
                            : message.isError 
                              ? 'bg-red-100 text-red-800 rounded-xl rounded-tl-none'
                              : 'bg-white border border-gray-200 text-gray-800 rounded-xl rounded-tl-none'
                  }`}
                >
                  {message.content}
                      </div>
                      <div className={`text-xs text-gray-500 mt-1 
                        ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                        {formatTime(new Date(message.timestamp))}
                      </div>
                </div>
              </div>
            ))}
                
            {loading && (
                  <div className="mb-6 flex">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 shadow-md mr-3 flex items-center justify-center">
                        <i className="fas fa-tshirt text-white"></i>
                      </div>
                    </div>
                    <div className="max-w-[75%]">
                      <div className="p-4 rounded-xl bg-white border border-gray-200 text-gray-800 rounded-tl-none">
                  <div className="flex space-x-2">
                          <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce delay-100"></div>
                          <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce delay-200"></div>
                        </div>
                  </div>
                </div>
              </div>
            )}
                
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
              <div className="p-4 border-t border-gray-200 bg-white">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <input
                    ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about styles, outfit combinations, fashion advice..."
                    className="flex-grow px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                    className="bg-gradient-to-r from-primary-500 to-primary-700 hover:from-primary-600 hover:to-primary-800 text-white py-3 px-5 rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50"
              >
                    {loading ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                <i className="fas fa-paper-plane"></i>
                    )}
              </button>
            </form>
          </div>
        </div>

            <div className="mt-6 text-center text-gray-500 text-sm">
          <p>Elegance Bot uses advanced AI to provide fashion advice.</p>
          <p className="mt-1">Your conversations are not stored permanently.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Chatbot 