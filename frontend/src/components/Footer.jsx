import React from 'react'
import { Link } from 'react-router-dom'
import { Logo } from './Navbar'

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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-10">
          <div className="space-y-4">
            <div className="mb-4">
              <Logo />
            </div>
            
            <p className="text-gray-400 mt-4 pr-4">
              Enhance your fashion identity through AI-powered style analysis and recommendations.
            </p>
            
            <p className="text-gray-400 font-serif italic mt-2">
              Aspire. Unveil. Refine.
            </p>
            
            <div className="flex space-x-4 mt-6">
              <a href="#" className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-accent-500/20 transition-colors">
                <i className="fab fa-facebook-f text-white"></i>
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-accent-500/20 transition-colors">
                <i className="fab fa-twitter text-white"></i>
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-accent-500/20 transition-colors">
                <i className="fab fa-instagram text-white"></i>
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-accent-500/20 transition-colors">
                <i className="fab fa-linkedin-in text-white"></i>
              </a>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-bold mb-4 border-b border-white/10 pb-2">Features</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/analyze" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  Analyze Your Outfit
                </Link>
              </li>
              <li>
                <Link to="/virtual-tryon" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  Virtual Fitting Room
                </Link>
              </li>
              <li>
                <Link to="/outfit-matcher" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  Outfit Matcher
                </Link>
              </li>
              <li>
                <Link to="/chatbot" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  Fashion Chatbot
                </Link>
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-bold mb-4 border-b border-white/10 pb-2">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <a href="#about" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  About Us
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-accent-200 transition-colors flex items-center">
                  <i className="fas fa-angle-right mr-2 text-accent-500"></i>
                  FAQs
                </a>
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-bold mb-4 border-b border-white/10 pb-2">Contact</h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <i className="fas fa-map-marker-alt text-accent-500 mr-3 mt-1"></i>
                <span className="text-gray-400">Beirut, Lebanon</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-envelope text-accent-500 mr-3 mt-1"></i>
                <span className="text-gray-400">zbl00@mail.aub.edu</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-phone-alt text-accent-500 mr-3 mt-1"></i>
                <span className="text-gray-400">+961 3 408 680</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-clock text-accent-500 mr-3 mt-1"></i>
                <span className="text-gray-400">Monday-Friday: 9:00 AM - 6:00 PM</span>
              </li>
            </ul>
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