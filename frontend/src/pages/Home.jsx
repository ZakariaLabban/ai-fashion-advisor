import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function Home() {
  // Animation states
  const [scrollPosition, setScrollPosition] = useState(0)
  const [isVisible, setIsVisible] = useState({
    feature1: false,
    feature2: false,
    feature3: false,
    feature4: false
  })

  // Handle scroll effects
  useEffect(() => {
    const handleScroll = () => {
      setScrollPosition(window.scrollY)
      
      // Check visibility for animations
      const feature1 = document.getElementById('feature-1')
      const feature2 = document.getElementById('feature-2')
      const feature3 = document.getElementById('feature-3')
      const feature4 = document.getElementById('feature-4')
      
      if (feature1 && window.scrollY > feature1.offsetTop - window.innerHeight * 0.8) {
        setIsVisible(prev => ({ ...prev, feature1: true }))
      }
      if (feature2 && window.scrollY > feature2.offsetTop - window.innerHeight * 0.8) {
        setIsVisible(prev => ({ ...prev, feature2: true }))
      }
      if (feature3 && window.scrollY > feature3.offsetTop - window.innerHeight * 0.8) {
        setIsVisible(prev => ({ ...prev, feature3: true }))
      }
      if (feature4 && window.scrollY > feature4.offsetTop - window.innerHeight * 0.8) {
        setIsVisible(prev => ({ ...prev, feature4: true }))
      }
    }
    
    window.addEventListener('scroll', handleScroll)
    // Initial check
    handleScroll()
    
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div>
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center">
        {/* Background Image */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <div 
            className="absolute inset-0 bg-gradient-diagonal from-primary-900/70 via-secondary-900/70 to-accent-900/60"
            style={{ mixBlendMode: 'multiply' }}
          ></div>
          <img 
            src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80" 
            alt="Fashion background" 
            className="absolute inset-0 object-cover w-full h-full"
          />
          <div className="absolute inset-0 bg-texture-fabric opacity-20"></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-40 relative z-10 text-center">
          {/* Logo */}
          <div className="mb-10 flex justify-center animate-fade-in-down">
            <div className="bg-white/10 backdrop-blur-sm p-6 rounded-full w-32 h-32 flex items-center justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-accent-400 to-secondary-500 rounded-full blur-sm transform scale-95 opacity-70"></div>
                <div className="relative bg-white rounded-full p-4 shadow-lg">
                  <div className="text-3xl font-serif font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-secondary-600 flex items-center justify-center">
                    <span>A</span>
                  </div>
                </div>
                <div className="absolute top-0 right-0 w-3 h-3 bg-accent-400 rounded-full shadow-accent-400/40 shadow-lg"></div>
              </div>
            </div>
          </div>
          
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-serif font-bold text-white mb-6 drop-shadow-lg animate-fade-in-down">
            <span className="block mb-2">ELEVATE YOUR</span>
            <span className="text-gradient-alt text-shadow-lg">FASHION IDENTITY</span>
          </h1>
          
          {/* Slogan */}
          <p className="text-xl md:text-2xl text-white/90 font-serif italic max-w-3xl mx-auto mb-4 animate-fade-in-down" style={{ animationDelay: '0.15s' }}>
            Aspire. Unveil. Refine.
          </p>
          
          <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto mb-10 animate-fade-in-down" style={{ animationDelay: '0.3s' }}>
            Discover your true style with AI-powered recommendations tailored just for you.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-fade-in-down" style={{ animationDelay: '0.4s' }}>
            <Link to="/analyze" className="btn-accent px-8 py-4 rounded-full shadow-lg hover:shadow-accent-500/30 hover:translate-y-1 transition-all">
              <i className="fas fa-tshirt mr-2"></i> Analyze Your Fit
            </Link>
            <Link to="/virtual-tryon" className="btn-outline border-white text-white hover:bg-white/20 hover:text-white px-8 py-4 rounded-full">
              <i className="fas fa-magic mr-2"></i> Try Virtual Fitting
            </Link>
          </div>
          
          {/* Scroll indicator */}
          <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 animate-bounce-slow">
            <i className="fas fa-chevron-down text-white text-2xl"></i>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gradient-to-br from-white to-gray-50 relative">
        <div className="absolute inset-0 bg-texture-paper opacity-10"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-20">
            <h2 className="section-title text-gradient mb-6">
              FASHION REIMAGINED WITH AI
            </h2>
            <p className="section-subtitle">
              Explore our suite of intelligent fashion tools designed to transform your style experience
            </p>
            {/* Slogan as subtitle */}
            <p className="mt-2 text-lg font-serif italic text-gray-600">
              Aspire. Unveil. Refine.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div id="feature-1" className={`card-glass group ${isVisible.feature1 ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ transitionDelay: '0.1s' }}>
              <div className="h-60 bg-gradient-to-br from-primary-100 to-primary-50 rounded-lg mb-6 overflow-hidden relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <i className="fas fa-search text-primary-400 text-6xl opacity-20 group-hover:scale-110 transition-transform duration-500"></i>
                </div>
                <img 
                  src="https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Style Analysis" 
                  className="w-full h-full object-cover rounded-lg opacity-90 group-hover:scale-105 group-hover:opacity-100 transition-all duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-primary-900/70 to-transparent"></div>
                <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
                <h3 className="text-2xl font-semibold text-white absolute bottom-4 left-4 right-4">Analyze Your Fit</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Our AI analyzes your outfit to identify clothing items, style classification, and key features.
              </p>
              <Link to="/analyze" className="text-primary-500 font-medium hover:text-primary-700 inline-flex items-center">
                Try Now <i className="fas fa-arrow-right ml-2 group-hover:translate-x-1 transition-transform"></i>
              </Link>
            </div>

            {/* Feature 2 */}
            <div id="feature-2" className={`card-glass group ${isVisible.feature2 ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ transitionDelay: '0.2s' }}>
              <div className="h-60 bg-gradient-to-br from-secondary-100 to-secondary-50 rounded-lg mb-6 overflow-hidden relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <i className="fas fa-tshirt text-secondary-400 text-6xl opacity-20 group-hover:scale-110 transition-transform duration-500"></i>
                </div>
                <img 
                  src="https://images.unsplash.com/photo-1560243563-062bfc001d68?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Virtual Try-On" 
                  className="w-full h-full object-cover rounded-lg opacity-90 group-hover:scale-105 group-hover:opacity-100 transition-all duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-secondary-900/70 to-transparent"></div>
                <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
                <h3 className="text-2xl font-semibold text-white absolute bottom-4 left-4 right-4">Fitting Room</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Try on garments virtually before buying with our state-of-the-art AI try-on technology.
              </p>
              <Link to="/virtual-tryon" className="text-secondary-500 font-medium hover:text-secondary-700 inline-flex items-center">
                Try Now <i className="fas fa-arrow-right ml-2 group-hover:translate-x-1 transition-transform"></i>
              </Link>
            </div>

            {/* Feature 3 */}
            <div id="feature-3" className={`card-glass group ${isVisible.feature3 ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ transitionDelay: '0.3s' }}>
              <div className="h-60 bg-gradient-to-br from-pastel-purple to-secondary-50 rounded-lg mb-6 overflow-hidden relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <i className="fas fa-comment text-secondary-400 text-6xl opacity-20 group-hover:scale-110 transition-transform duration-500"></i>
                </div>
                <img 
                  src="https://images.unsplash.com/photo-1585435557343-3b092031a831?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Elegance Chatbot" 
                  className="w-full h-full object-cover rounded-lg opacity-90 group-hover:scale-105 group-hover:opacity-100 transition-all duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-purple-900/70 to-transparent"></div>
                <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
                <h3 className="text-2xl font-semibold text-white absolute bottom-4 left-4 right-4">Elegance Chatbot</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Get personalized fashion advice from our AI-powered chatbot that understands your style preferences.
              </p>
              <Link to="/chatbot" className="text-purple-500 font-medium hover:text-purple-700 inline-flex items-center">
                Chat Now <i className="fas fa-arrow-right ml-2 group-hover:translate-x-1 transition-transform"></i>
              </Link>
            </div>
            
            {/* Feature 4 */}
            <div id="feature-4" className={`card-glass group ${isVisible.feature4 ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ transitionDelay: '0.4s' }}>
              <div className="h-60 bg-gradient-to-br from-accent-100 to-accent-50 rounded-lg mb-6 overflow-hidden relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <i className="fas fa-sync-alt text-accent-400 text-6xl opacity-20 group-hover:scale-110 transition-transform duration-500"></i>
                </div>
                <img 
                  src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Outfit Matcher" 
                  className="w-full h-full object-cover rounded-lg opacity-90 group-hover:scale-105 group-hover:opacity-100 transition-all duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-accent-900/70 to-transparent"></div>
                <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
                <h3 className="text-2xl font-semibold text-white absolute bottom-4 left-4 right-4">Outfit Matcher</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Find out how well your garments match each other and get intelligent styling suggestions.
              </p>
              <Link to="/outfit-matcher" className="text-accent-500 font-medium hover:text-accent-700 inline-flex items-center">
                Match Now <i className="fas fa-arrow-right ml-2 group-hover:translate-x-1 transition-transform"></i>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-24 bg-gradient-to-br from-fashion-beige to-white relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-b from-white to-transparent"></div>
        <div className="absolute -top-10 -right-10 w-40 h-40 bg-pastel-pink rounded-full opacity-20 blur-xl"></div>
        <div className="absolute top-1/4 -left-20 w-60 h-60 bg-pastel-blue rounded-full opacity-20 blur-xl"></div>
        <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <h2 className="section-title text-gradient mb-6">
              ABOUT AURAI FASHION
            </h2>
            <p className="section-subtitle">
              Our mission is to bring AI innovation to fashion, providing tools that enhance your style journey
            </p>
            <p className="mt-2 font-serif italic text-xl text-gray-600">
              Aspire. Unveil. Refine.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
            <div className="relative">
              <div className="absolute -top-4 -left-4 w-24 h-24 border-2 border-primary-300 rounded-lg opacity-30"></div>
              <div className="absolute -bottom-4 -right-4 w-24 h-24 border-2 border-accent-300 rounded-lg opacity-30"></div>
              <div className="rounded-xl overflow-hidden shadow-fashion relative z-10">
                <img 
                  src="https://images.unsplash.com/photo-1558769132-cb1aea458c5e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1974&q=80" 
                  alt="Fashion Technology" 
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                />
              </div>
            </div>
            
            <div>
              <h3 className="text-2xl font-bold text-primary-800 mb-6 font-serif">Our Mission</h3>
              <p className="text-gray-700 mb-8 leading-relaxed">
                At <span className="font-serif font-bold text-primary-600">AURAI</span>, we believe that fashion is more than just clothing—it's self-expression, confidence, and identity. 
                Our mission is to leverage cutting-edge AI technology to help you discover and refine your personal style, 
                making fashion more accessible, sustainable, and enjoyable for everyone.
              </p>
              
              <div className="space-y-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0 h-12 w-12 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center">
                    <i className="fas fa-brain text-xl"></i>
                  </div>
                  <div className="ml-4">
                    <h4 className="text-lg font-medium text-primary-800">AI-Powered Analysis</h4>
                    <p className="mt-2 text-gray-600">Our platform combines advanced computer vision, machine learning, and natural language processing
                    to create a comprehensive fashion advisor system.</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="flex-shrink-0 h-12 w-12 rounded-full bg-secondary-100 text-secondary-600 flex items-center justify-center">
                    <i className="fas fa-tshirt text-xl"></i>
                  </div>
                  <div className="ml-4">
                    <h4 className="text-lg font-medium text-primary-800">Virtual Try-On</h4>
                    <p className="mt-2 text-gray-600">See how clothes look on you without the hassle of physical fitting rooms, making shopping more convenient.</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="flex-shrink-0 h-12 w-12 rounded-full bg-accent-100 text-accent-600 flex items-center justify-center">
                    <i className="fas fa-palette text-xl"></i>
                  </div>
                  <div className="ml-4">
                    <h4 className="text-lg font-medium text-primary-800">Personal Style Guidance</h4>
                    <p className="mt-2 text-gray-600">Receive customized fashion advice that aligns with your preferences, body type, and style goals.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-24 bg-gradient-to-br from-primary-900 to-secondary-900 text-white relative">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-b from-fashion-beige to-transparent opacity-10"></div>
        <div className="absolute top-40 right-10 w-60 h-60 rounded-full bg-primary-500/10 blur-xl"></div>
        <div className="absolute bottom-20 left-10 w-40 h-40 rounded-full bg-accent-500/10 blur-xl"></div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold font-serif tracking-tight mb-6 text-white">
              GET IN TOUCH
            </h2>
            <p className="mt-4 max-w-2xl text-xl text-gray-300 mx-auto">
              Have questions or feedback? We'd love to hear from you!
            </p>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="card-glass backdrop-blur-xl bg-white/5 border border-white/10">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-8">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-6 font-serif">Contact Information</h3>
                  <div className="space-y-6">
                    <div className="flex items-start">
                      <div className="h-10 w-10 rounded-full bg-accent-500/20 flex items-center justify-center">
                        <i className="fas fa-map-marker-alt text-accent-400"></i>
                      </div>
                      <div className="ml-4">
                        <p className="text-white font-medium">Our Location</p>
                        <p className="text-gray-300 mt-1">Beirut, Lebanon</p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <div className="h-10 w-10 rounded-full bg-accent-500/20 flex items-center justify-center">
                        <i className="fas fa-envelope text-accent-400"></i>
                      </div>
                      <div className="ml-4">
                        <p className="text-white font-medium">Email Us</p>
                        <p className="text-gray-300 mt-1">zbl00@mail.aub.edu</p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <div className="h-10 w-10 rounded-full bg-accent-500/20 flex items-center justify-center">
                        <i className="fas fa-phone-alt text-accent-400"></i>
                      </div>
                      <div className="ml-4">
                        <p className="text-white font-medium">Call Us</p>
                        <p className="text-gray-300 mt-1">+961 3 408 680</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-6 font-serif">Send a Message</h3>
                  <form className="space-y-4">
                    <div>
                      <input 
                        type="text" 
                        placeholder="Your Name" 
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-500 text-white placeholder-gray-400"
                      />
                    </div>
                    <div>
                      <input 
                        type="email" 
                        placeholder="Your Email" 
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-500 text-white placeholder-gray-400"
                      />
                    </div>
                    <div>
                      <textarea 
                        placeholder="Your Message" 
                        rows="4" 
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-500 text-white placeholder-gray-400"
                      ></textarea>
                    </div>
                    <button
                      type="submit"
                      className="w-full bg-accent-500 hover:bg-accent-600 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-300 flex items-center justify-center"
                    >
                      <i className="fas fa-paper-plane mr-2"></i>
                      Send Message
                    </button>
                  </form>
                </div>
              </div>
              
              <div className="pt-6 border-t border-white/10 text-center">
                <p className="text-gray-400">
                  We're available Monday through Friday, 9:00 AM to 6:00 PM EST
                </p>
                <div className="flex justify-center space-x-4 mt-4">
                  <a href="#" className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-accent-500 transition-colors duration-300">
                    <i className="fab fa-facebook-f"></i>
                  </a>
                  <a href="#" className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-accent-500 transition-colors duration-300">
                    <i className="fab fa-twitter"></i>
                  </a>
                  <a href="#" className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-accent-500 transition-colors duration-300">
                    <i className="fab fa-instagram"></i>
                  </a>
                  <a href="#" className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-accent-500 transition-colors duration-300">
                    <i className="fab fa-pinterest"></i>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home 