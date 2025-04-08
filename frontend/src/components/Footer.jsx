import React from 'react'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center">
          <div className="flex space-x-6 mb-4">
            <a href="#" className="text-gray-500 hover:text-gray-900">
              <i className="fab fa-facebook-f text-xl"></i>
            </a>
            <a href="#" className="text-gray-500 hover:text-gray-900">
              <i className="fab fa-twitter text-xl"></i>
            </a>
            <a href="#" className="text-gray-500 hover:text-gray-900">
              <i className="fab fa-instagram text-xl"></i>
            </a>
            <a href="#" className="text-gray-500 hover:text-gray-900">
              <i className="fab fa-pinterest text-xl"></i>
            </a>
          </div>
          <p className="text-center text-gray-600">
            &copy; {currentYear} AURAI. All rights reserved.
          </p>
          <p className="text-center text-sm text-gray-500 mt-2">
            Fashion Technology at its finest
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer 