import React, { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'

// Logo Component
function Logo({ size = "default" }) {
  const sizes = {
    small: "w-8 h-8 text-xl p-2",
    default: "w-10 h-10 text-2xl p-2",
    large: "w-14 h-14 text-3xl p-3"
  }
  
  const bgSize = sizes[size] || sizes.default
  
  return (
    <div className="flex items-center group">
      <div className="relative mr-3">
        {/* Decorative ring */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-accent-300/50 to-secondary-400/50 blur-[2px] transform scale-110 group-hover:scale-125 transition-transform duration-500"></div>
        
        {/* Main logo container */}
        <div className={`relative rounded-full ${bgSize} bg-gradient-to-br from-white to-gray-100 shadow-lg border border-white/50 flex items-center justify-center overflow-hidden group-hover:shadow-accent-400/30 group-hover:shadow-lg transition-all duration-500`}>
          {/* Background glow effect */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary-400/10 to-secondary-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          
          {/* Logo letter */}
          <span className="font-serif font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-secondary-600 relative z-10 group-hover:scale-110 transition-transform duration-500">A</span>
          
          {/* Accent dot with pulse effect */}
          <div className="absolute top-0 right-0 w-2.5 h-2.5 bg-accent-400 rounded-full shadow-accent-400/40 shadow-md group-hover:animate-pulse"></div>
          
          {/* Subtle shine effect */}
          <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/80 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -rotate-45 translate-y-full group-hover:translate-y-0"></div>
        </div>
      </div>
      
      <div className="flex flex-col">
        <span className="text-lg md:text-xl font-serif font-bold text-white text-shadow group-hover:text-accent-100 transition-colors duration-500">
          AURAI
        </span>
        <div className="flex items-center">
          <span className="text-xs font-light tracking-widest text-white/90 group-hover:text-white transition-colors duration-500">
            FASHION
          </span>
          <span className="ml-1 w-6 h-[1px] bg-gradient-to-r from-accent-400/0 via-accent-400 to-accent-400/0 transform scale-0 group-hover:scale-100 transition-transform duration-700 origin-left"></span>
        </div>
      </div>
    </div>
  )
}

function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  // Handle scroll effect for navbar
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 60) {
        setScrolled(true)
      } else {
        setScrolled(false)
      }
    }
    
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

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

  // Check if a link is active
  const isActive = (path) => {
    return location.pathname === path ? 'nav-link-active' : 'nav-link';
  };

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled 
        ? 'bg-gradient-to-r from-secondary-700/95 to-secondary-900/95 shadow-lg py-2' 
        : 'bg-gradient-to-r from-secondary-700/95 to-secondary-900/95 py-4'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <Logo />
            </Link>
          </div>

          {/* Desktop menu */}
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/" className={`${isActive('/')} text-white hover:text-accent-200`}>Home</Link>
            <Link to="/analyze" className={`${isActive('/analyze')} text-white hover:text-accent-200`}>Analyze</Link>
            <Link to="/virtual-tryon" className={`${isActive('/virtual-tryon')} text-white hover:text-accent-200`}>Fitting Room</Link>
            <Link to="/outfit-matcher" className={`${isActive('/outfit-matcher')} text-white hover:text-accent-200`}>Outfit Matcher</Link>
            <Link to="/chatbot" className={`${isActive('/chatbot')} text-white hover:text-accent-200`}>Elegance Bot</Link>
            <button onClick={() => scrollToSection('#about')} className="text-white hover:text-accent-200 nav-link">About</button>
            <button 
              onClick={() => scrollToSection('#contact')} 
              className="px-4 py-2 rounded-full border-2 border-accent-500 text-white bg-accent-500/30 hover:bg-accent-500 
                transition duration-300 hover:shadow-lg hover:shadow-accent-500/30"
            >
              Contact
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-white hover:text-accent-200 
                hover:bg-secondary-600 focus:outline-none transition duration-300"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              <i className={`fas ${isMenuOpen ? 'fa-times' : 'fa-bars'}`}></i>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`md:hidden transition-all duration-300 ease-in-out ${isMenuOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="px-2 pt-2 pb-3 space-y-1 bg-gradient-to-b from-secondary-700 to-secondary-800 backdrop-blur shadow-lg">
          <Link to="/" className="block px-3 py-2 text-base font-medium rounded-md text-white hover:bg-secondary-600 transition duration-300">Home</Link>
          <Link to="/analyze" className="block px-3 py-2 text-base font-medium rounded-md text-white hover:bg-secondary-600 transition duration-300">Analyze</Link>
          <Link to="/virtual-tryon" className="block px-3 py-2 text-base font-medium rounded-md text-white hover:bg-secondary-600 transition duration-300">Fitting Room</Link>
          <Link to="/outfit-matcher" className="block px-3 py-2 text-base font-medium rounded-md text-white hover:bg-secondary-600 transition duration-300">Outfit Matcher</Link>
          <Link to="/chatbot" className="block px-3 py-2 text-base font-medium rounded-md text-white hover:bg-secondary-600 transition duration-300">Elegance Bot</Link>
          <button onClick={() => scrollToSection('#about')} className="w-full text-left block px-3 py-2 text-base font-medium rounded-md text-white hover:bg-secondary-600 transition duration-300">About</button>
          <button onClick={() => scrollToSection('#contact')} className="w-full text-left block px-3 py-2 text-base font-medium text-white bg-accent-500/30 rounded-md hover:bg-accent-500 transition duration-300">Contact</button>
        </div>
      </div>
    </nav>
  )
}

export { Logo };
export default Navbar; 