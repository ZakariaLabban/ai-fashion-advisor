import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'

function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  // Function to handle navigation to sections
  const scrollToSection = (sectionId) => {
    // Check if we're on the home page
    if (location.pathname !== '/') {
      // Navigate to home page first with the section hash
      navigate('/' + sectionId);
    } else {
      // Already on home page, just scroll to section
      const element = document.getElementById(sectionId.replace('#', ''));
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
    // Close mobile menu if open
    setIsMenuOpen(false);
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl font-bold text-primary">AURAI</span>
            </Link>
          </div>

          {/* Desktop menu */}
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/analyze" className="nav-link">Analyze</Link>
            <Link to="/virtual-tryon" className="nav-link">Fitting Room</Link>
            <Link to="/outfit-matcher" className="nav-link">Outfit Matcher</Link>
            <Link to="/chatbot" className="nav-link">Elegance Bot</Link>
            <button onClick={() => scrollToSection('#about')} className="nav-link">About</button>
            <button onClick={() => scrollToSection('#contact')} className="nav-link">
              <i className="fas fa-envelope"></i>
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-primary hover:bg-gray-100 focus:outline-none"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              <i className={`fas ${isMenuOpen ? 'fa-times' : 'fa-bars'}`}></i>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`md:hidden ${isMenuOpen ? 'block' : 'hidden'}`}>
        <div className="pt-2 pb-3 space-y-1">
          <Link to="/" className="block px-3 py-2 text-base font-medium hover:bg-gray-50">Home</Link>
          <Link to="/analyze" className="block px-3 py-2 text-base font-medium hover:bg-gray-50">Analyze</Link>
          <Link to="/virtual-tryon" className="block px-3 py-2 text-base font-medium hover:bg-gray-50">Fitting Room</Link>
          <Link to="/outfit-matcher" className="block px-3 py-2 text-base font-medium hover:bg-gray-50">Outfit Matcher</Link>
          <Link to="/chatbot" className="block px-3 py-2 text-base font-medium hover:bg-gray-50">Elegance Bot</Link>
          <button onClick={() => scrollToSection('#about')} className="w-full text-left block px-3 py-2 text-base font-medium hover:bg-gray-50">About</button>
          <button onClick={() => scrollToSection('#contact')} className="w-full text-left block px-3 py-2 text-base font-medium hover:bg-gray-50">Contact</button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar 