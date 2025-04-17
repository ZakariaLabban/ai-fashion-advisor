import React from 'react'
import { Link } from 'react-router-dom'

function Footer() {
  const currentYear = new Date().getFullYear()
  
  return (
    <footer className="relative bg-gradient-to-br from-primary-900 to-secondary-900 text-white pt-16 pb-8 overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-primary-500/10 backdrop-blur-xl"></div>
        <div className="absolute top-1/2 left-1/4 w-48 h-48 rounded-full bg-secondary-500/10 backdrop-blur-xl"></div>
        <div className="absolute bottom-20 right-20 w-24 h-24 rounded-full bg-accent-500/10 backdrop-blur-xl"></div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand */}
          <div className="col-span-1 md:col-span-1">
            <Link to="/" className="flex items-center mb-6">
              <span className="text-3xl font-serif font-bold">AURAI</span>
              <span className="ml-2 text-xs font-light tracking-widest text-white/90">FASHION</span>
            </Link>
            <p className="text-gray-300 mb-6">
              Empowering your fashion journey with AI technology that understands your style preferences.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-white hover:text-accent-300 transition-colors duration-300">
                <i className="fab fa-instagram text-xl"></i>
              </a>
              <a href="#" className="text-white hover:text-accent-300 transition-colors duration-300">
                <i className="fab fa-twitter text-xl"></i>
              </a>
              <a href="#" className="text-white hover:text-accent-300 transition-colors duration-300">
                <i className="fab fa-facebook text-xl"></i>
              </a>
              <a href="#" className="text-white hover:text-accent-300 transition-colors duration-300">
                <i className="fab fa-pinterest text-xl"></i>
              </a>
            </div>
          </div>
          
          {/* Quick Links */}
          <div className="col-span-1">
            <h3 className="text-xl font-medium mb-6 relative inline-block">
              Quick Links
              <span className="absolute -bottom-2 left-0 w-12 h-0.5 bg-accent-500"></span>
            </h3>
            <ul className="space-y-3">
              <li>
                <Link to="/" className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                  <i className="fas fa-chevron-right text-xs mr-2 text-accent-500"></i>
                  Home
                </Link>
              </li>
              <li>
                <Link to="/analyze" className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                  <i className="fas fa-chevron-right text-xs mr-2 text-accent-500"></i>
                  Analyze Your Fit
                </Link>
              </li>
              <li>
                <Link to="/virtual-tryon" className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                  <i className="fas fa-chevron-right text-xs mr-2 text-accent-500"></i>
                  Fitting Room
                </Link>
              </li>
              <li>
                <Link to="/outfit-matcher" className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                  <i className="fas fa-chevron-right text-xs mr-2 text-accent-500"></i>
                  Outfit Matcher
                </Link>
              </li>
              <li>
                <Link to="/chatbot" className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                  <i className="fas fa-chevron-right text-xs mr-2 text-accent-500"></i>
                  Elegance Bot
                </Link>
              </li>
            </ul>
          </div>
          
          {/* Services */}
          <div className="col-span-1">
            <h3 className="text-xl font-medium mb-6 relative inline-block">
              Our Services
              <span className="absolute -bottom-2 left-0 w-12 h-0.5 bg-accent-500"></span>
            </h3>
            <ul className="space-y-3">
              <li className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                <i className="fas fa-tshirt text-accent-500 mr-2"></i>
                Clothing Analysis
              </li>
              <li className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                <i className="fas fa-magic text-accent-500 mr-2"></i>
                Virtual Try-On
              </li>
              <li className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                <i className="fas fa-robot text-accent-500 mr-2"></i>
                Fashion AI Assistant
              </li>
              <li className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                <i className="fas fa-tags text-accent-500 mr-2"></i>
                Style Matching
              </li>
              <li className="text-gray-300 hover:text-white transition-colors duration-300 flex items-center">
                <i className="fas fa-search text-accent-500 mr-2"></i>
                Fashion Recommendations
              </li>
            </ul>
          </div>
          
          {/* Newsletter */}
          <div className="col-span-1">
            <h3 className="text-xl font-medium mb-6 relative inline-block">
              Newsletter
              <span className="absolute -bottom-2 left-0 w-12 h-0.5 bg-accent-500"></span>
            </h3>
            <p className="text-gray-300 mb-4">
              Subscribe to our newsletter for the latest fashion trends and AI technology updates.
            </p>
            <form className="space-y-2">
              <div className="relative">
                <input 
                  type="email" 
                  placeholder="Your email address" 
                  className="w-full px-4 py-3 bg-white/10 backdrop-blur border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-500 text-white placeholder-gray-400"
                />
              </div>
              <button 
                type="submit"
                className="w-full px-4 py-3 bg-accent-500 hover:bg-accent-600 text-white rounded-lg transition-colors duration-300 flex items-center justify-center"
              >
                <span>Subscribe</span>
                <i className="fas fa-paper-plane ml-2"></i>
              </button>
            </form>
          </div>
        </div>
        
        <div className="divider mt-12 mb-8"></div>
        
        <div className="flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-400 text-sm">
            &copy; {currentYear} AURAI Fashion Technology. All rights reserved.
          </p>
          <div className="mt-4 md:mt-0 flex space-x-6">
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors duration-300">Privacy Policy</a>
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors duration-300">Terms of Service</a>
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors duration-300">Cookie Policy</a>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer 