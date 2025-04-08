import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

function Chatbot() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: "Hello! I'm Elegance, your fashion AI assistant. How can I help you with your style today?"
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const messagesEndRef = useRef(null)

  // Generate a session ID when the component mounts
  useEffect(() => {
    setSessionId(`session_${Date.now()}`)
  }, [])

  // Scroll to bottom of chat whenever messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim()) return
    
    // Add user message to chat
    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post('/api/elegance/chat', {
        message: input,
        session_id: sessionId
      })

      // Add assistant response to chat
      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.response || "I'm sorry, I couldn't process your request."
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message to Elegance:', error)
      
      // Add error message
      const errorMessage = { 
        role: 'assistant', 
        content: "I apologize, but I'm having trouble connecting to my fashion knowledge. Please try again later."
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
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

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          {/* Chat messages area */}
          <div className="h-96 overflow-y-auto p-6 bg-gray-50">
            {messages.map((message, index) => (
              <div 
                key={index}
                className={`mb-4 ${message.role === 'user' ? 'text-right' : ''}`}
              >
                <div 
                  className={`inline-block p-4 rounded-lg max-w-[80%] ${
                    message.role === 'user' 
                      ? 'bg-secondary text-white' 
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="mb-4">
                <div className="inline-block p-4 rounded-lg bg-gray-200 text-gray-800">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="p-4 border-t border-gray-200">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about styles, outfit combinations, fashion advice..."
                className="flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-secondary"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="btn py-2 px-4 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <i className="fas fa-paper-plane"></i>
              </button>
            </form>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Elegance Bot uses advanced AI to provide fashion advice.</p>
          <p className="mt-1">Your conversations are not stored permanently.</p>
        </div>
      </div>
    </div>
  )
}

export default Chatbot 