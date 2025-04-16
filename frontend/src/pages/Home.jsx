import React from 'react'
import { Link } from 'react-router-dom'

function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative bg-gray-900 text-white">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: "linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url('https://images.unsplash.com/photo-1529139574466-a303027c1d8b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1974&q=80')",
            backgroundPosition: "center 30%"
          }}
        ></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32 md:py-48 lg:py-56 relative z-10">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              WEAR CLOTHES THAT MATTER
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto mb-8">
              Discover your true style with AI-powered recommendations tailored just for you.
            </p>
            <Link to="/analyze" className="btn inline-block">
              Try It Now
            </Link>
          </div>
        </div>
      </section>

      {/* What's New Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary tracking-tight">
              WHAT'S NEW
            </h2>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
              Explore our latest AI-powered fashion technology features
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Card 1 */}
            <div className="card group">
              <div className="h-48 bg-gray-200 rounded-lg mb-4 overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Style Analysis" 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <h3 className="text-xl font-semibold text-primary mb-2">Analyze Your Fit</h3>
              <p className="text-gray-600 mb-4">
                Our AI analyzes your outfit to identify clothing items, style classification, and key features.
              </p>
              <Link to="/analyze" className="text-secondary font-medium hover:underline inline-flex items-center">
                Try Now <i className="fas fa-arrow-right ml-1"></i>
              </Link>
            </div>

            {/* Card 2 */}
            <div className="card group">
              <div className="h-48 bg-gray-200 rounded-lg mb-4 overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1560243563-062bfc001d68?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Virtual Try-On" 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <h3 className="text-xl font-semibold text-primary mb-2">Fitting Room</h3>
              <p className="text-gray-600 mb-4">
                Try on garments virtually before buying with our state-of-the-art AI try-on technology.
              </p>
              <Link to="/virtual-tryon" className="text-secondary font-medium hover:underline inline-flex items-center">
                Try Now <i className="fas fa-arrow-right ml-1"></i>
              </Link>
            </div>

            {/* Card 3 */}
            <div className="card group">
              <div className="h-48 bg-gray-200 rounded-lg mb-4 overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1585435557343-3b092031a831?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Elegance Chatbot" 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <h3 className="text-xl font-semibold text-primary mb-2">Elegance Chatbot</h3>
              <p className="text-gray-600 mb-4">
                Get personalized fashion advice from our AI-powered chatbot that understands your style preferences.
              </p>
              <Link to="/chatbot" className="text-secondary font-medium hover:underline inline-flex items-center">
                Chat Now <i className="fas fa-arrow-right ml-1"></i>
              </Link>
            </div>
            
            {/* Card 4 - New Outfit Matcher */}
            <div className="card group">
              <div className="h-48 bg-gray-200 rounded-lg mb-4 overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80" 
                  alt="Outfit Matcher" 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <h3 className="text-xl font-semibold text-primary mb-2">Outfit Matcher</h3>
              <p className="text-gray-600 mb-4">
                Find out how well your garments match each other and get intelligent styling suggestions.
              </p>
              <Link to="/outfit-matcher" className="text-secondary font-medium hover:underline inline-flex items-center">
                Match Now <i className="fas fa-arrow-right ml-1"></i>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary tracking-tight">
              ABOUT AURAI
            </h2>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
              Empowering your fashion journey with AI technology
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-semibold text-primary mb-4">Our Mission</h3>
              <p className="text-gray-600 mb-6">
                At AURAI, we believe that fashion is more than just clothing—it's self-expression, confidence, and identity. 
                Our mission is to leverage cutting-edge AI technology to help you discover and refine your personal style, 
                making fashion more accessible, sustainable, and enjoyable for everyone.
              </p>
              <h3 className="text-2xl font-semibold text-primary mb-4">Our Technology</h3>
              <p className="text-gray-600">
                Our platform combines advanced computer vision, machine learning, and natural language processing
                to create a comprehensive fashion advisor system. From identifying clothing items to virtual try-on
                and personalized style advice, AURAI brings the future of fashion technology to your fingertips.
              </p>
            </div>
            <div className="rounded-xl overflow-hidden shadow-lg">
              <img 
                src="https://images.unsplash.com/photo-1558769132-cb1aea458c5e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1974&q=80" 
                alt="Fashion Technology" 
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary tracking-tight">
              CONTACT US
            </h2>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
              Have questions or feedback? We'd love to hear from you!
            </p>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="bg-white rounded-xl shadow-md overflow-hidden p-6 md:p-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div>
                  <h3 className="text-xl font-semibold text-primary mb-4">Get In Touch</h3>
                  <div className="space-y-4">
                    <div className="flex items-start">
                      <i className="fas fa-map-marker-alt text-secondary mt-1 w-5"></i>
                      <div className="ml-3">
                        <p className="text-gray-600">Beirut, Lebanon</p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <i className="fas fa-envelope text-secondary mt-1 w-5"></i>
                      <div className="ml-3">
                        <p className="text-gray-600">zbl00@mail.aub.edu</p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <i className="fas fa-phone-alt text-secondary mt-1 w-5"></i>
                      <div className="ml-3">
                        <p className="text-gray-600">+961 3 408 680</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-primary mb-4">Connect With Us</h3>
                  <p className="text-gray-600 mb-4">
                    Follow us on social media for the latest updates, fashion tips, and trends.
                  </p>
                  <div className="flex space-x-4">
                    <a href="#" className="text-secondary hover:text-primary transition duration-300">
                      <i className="fab fa-facebook-f text-2xl"></i>
                    </a>
                    <a href="#" className="text-secondary hover:text-primary transition duration-300">
                      <i className="fab fa-twitter text-2xl"></i>
                    </a>
                    <a href="#" className="text-secondary hover:text-primary transition duration-300">
                      <i className="fab fa-instagram text-2xl"></i>
                    </a>
                    <a href="#" className="text-secondary hover:text-primary transition duration-300">
                      <i className="fab fa-pinterest text-2xl"></i>
                    </a>
                  </div>
                </div>
              </div>
              
              <div className="text-center pt-6 border-t border-gray-200">
                <p className="text-gray-500">
                  We're available Monday through Friday, 9:00 AM to 6:00 PM EST
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home 