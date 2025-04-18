import React, { useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Analyze from './pages/Analyze'
import VirtualTryOn from './pages/VirtualTryOn'
import Chatbot from './pages/Chatbot'
import OutfitMatcher from './pages/OutfitMatcher'
import FashionFinder from './pages/FashionFinder'

function App() {
  const location = useLocation();

  useEffect(() => {
    // Check if there's a hash in the URL when the app loads or location changes
    if (location.hash) {
      // Remove the # character
      const id = location.hash.substring(1);
      // Find the element with that id
      const element = document.getElementById(id);
      if (element) {
        // Wait a bit for the page to fully render before scrolling
        setTimeout(() => {
          element.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }
  }, [location]);

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="analyze" element={<Analyze />} />
        <Route path="virtual-tryon" element={<VirtualTryOn />} />
        <Route path="chatbot" element={<Chatbot />} />
        <Route path="outfit-matcher" element={<OutfitMatcher />} />
        <Route path="fashion-finder" element={<FashionFinder />} />
      </Route>
    </Routes>
  )
}

export default App 