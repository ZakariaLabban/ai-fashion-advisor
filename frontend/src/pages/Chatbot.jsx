import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { format } from 'date-fns'

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
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const suggestedQuestions = [
    "What colors match well with navy blue?",
    "How can I style a white button-down shirt?",
    "What's trending in men's fashion this season?",
    "How do I dress for a casual business meeting?",
    "What accessories work best with a little black dress?"
  ]

  // Generate a session ID when the component mounts
  useEffect(() => {
    setSessionId(`session_${Date.now()}`)
  }, [])

  // Scroll to bottom of chat whenever messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  const clearChat = () => {
    setMessages([{ 
      role: 'assistant', 
      content: "Hello! I'm Elegance, your fashion AI assistant. How can I help you with your style today?",
      timestamp: new Date()
    }])
    setShowSuggestions(true)
    setError(null)
  }

  return (
    <div className="py-8 bg-gray-50 min-h-screen">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">Elegance Bot</h1>
          <p className="text-lg text-gray-600">
            Your personal AI fashion advisor to answer all your style questions
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
          {/* Chat header */}
          <div className="bg-primary text-white p-4 flex justify-between items-center">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center mr-3">
                <i className="fas fa-tshirt text-primary text-xl"></i>
              </div>
              <div>
                <h3 className="font-medium">Elegance Bot</h3>
                <p className="text-xs opacity-75">Fashion AI Assistant</p>
              </div>
            </div>
            <button 
              onClick={clearChat}
              className="text-white hover:text-gray-200 transition-colors"
              title="Clear chat"
            >
              <i className="fas fa-trash-alt"></i>
            </button>
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
          <div className="h-96 overflow-y-auto p-6 bg-gray-50">
            {messages.map((message, index) => (
              <div 
                key={index}
                className={`mb-6 ${message.role === 'user' ? 'flex flex-row-reverse' : 'flex'}`}
              >
                {/* Avatar */}
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center 
                    ${message.role === 'user' 
                      ? 'bg-secondary ml-3' 
                      : 'bg-primary mr-3'}`}>
                    <i className={`fas ${message.role === 'user' ? 'fa-user' : 'fa-tshirt'} text-white`}></i>
                  </div>
                </div>

                {/* Message bubble */}
                <div className="max-w-[75%]">
                  <div 
                    className={`p-4 rounded-xl ${
                      message.role === 'user' 
                        ? 'bg-secondary text-white rounded-tr-none' 
                        : message.isError 
                          ? 'bg-red-100 text-red-800 rounded-tl-none'
                          : 'bg-gray-200 text-gray-800 rounded-tl-none'
                    }`}
                  >
                    {message.content}
                  </div>
                  <div className={`text-xs text-gray-500 mt-1 
                    ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                    {format(new Date(message.timestamp), 'h:mm a')}
                  </div>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="mb-6 flex">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-primary mr-3 flex items-center justify-center">
                    <i className="fas fa-tshirt text-white"></i>
                  </div>
                </div>
                <div className="max-w-[75%]">
                  <div className="p-4 rounded-xl bg-gray-200 text-gray-800 rounded-tl-none">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Suggested questions (show only at start) */}
            {showSuggestions && messages.length === 1 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Suggested questions:</h4>
                <div className="space-y-2">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(question)}
                      className="block w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm"
                    >
                      {question}
                    </button>
                  ))}
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
                className="flex-grow px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-primary hover:bg-primary-dark text-white py-3 px-5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
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

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Elegance Bot uses advanced AI to provide fashion advice.</p>
          <p className="mt-1">Your conversations are not stored permanently.</p>
          <p className="mt-3 text-xs">
            <i className="fas fa-info-circle mr-1"></i>
            For specific fashion advice, try including details like body type, occasion, or personal style preferences.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Chatbot 