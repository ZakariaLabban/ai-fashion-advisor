import React, { useState, useEffect } from 'react'
import axios from 'axios'

// Fashion Style Tips Component for Outfit Matcher
function OutfitStyleTips() {
  const tips = [
    "Choose complementary colors that work well together in the color wheel",
    "Balance patterns - if one piece has a strong pattern, keep the other more subtle",
    "Consider the occasion - casual, formal, or business settings need different combinations",
    "Pay attention to proportions - oversized tops work well with fitted bottoms, and vice versa",
    "Think about the silhouette your outfit creates from top to bottom",
    "Texture mixing adds depth - try combining different fabric textures for interest",
    "Monochromatic outfits (same color family) create a sophisticated, elongated look"
  ]
  
  const [currentTip, setCurrentTip] = useState(0)
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTip((prev) => (prev + 1) % tips.length)
    }, 6000)
    
    return () => clearInterval(timer)
  }, [])
  
  return (
    <div className="bg-gradient-to-r from-primary-50 to-secondary-50 p-5 rounded-xl shadow-sm border border-secondary-100 mb-8 relative overflow-hidden">
      <div className="absolute -right-12 -bottom-10 opacity-5 text-9xl">
        <i className="fas fa-tshirt"></i>
      </div>
      <div className="flex items-start relative z-10">
        <div className="text-primary-500 mr-4 text-2xl mt-1">
          <i className="fas fa-lightbulb animate-pulse-subtle"></i>
        </div>
        <div>
          <h3 className="font-medium text-primary-700 mb-2">Style Tip:</h3>
          <div className="h-16">
            <p className="text-gray-700 transition-all duration-500 ease-in-out">
              {tips[currentTip]}
            </p>
          </div>
          <div className="flex space-x-1 mt-3">
            {tips.map((_, index) => (
              <button 
                key={index} 
                className={`w-2 h-2 rounded-full transition-all ${currentTip === index ? 'bg-primary-500 w-6' : 'bg-gray-300'}`}
                onClick={() => setCurrentTip(index)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Sample outfit combinations that work well
function OutfitInspirations() {
  const inspirations = [
    { top: "White button-down shirt", bottom: "Navy tailored pants", style: "Business casual" },
    { top: "Gray crew neck sweater", bottom: "Dark wash jeans", style: "Smart casual" },
    { top: "Black turtleneck", bottom: "Camel skirt or pants", style: "Minimalist chic" },
    { top: "Denim shirt", bottom: "Black pants", style: "Casual cool" },
    { top: "White t-shirt", bottom: "Olive chinos", style: "Relaxed everyday" },
  ]
  
  return (
    <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 mb-8">
      <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center">
        <i className="fas fa-star text-secondary-500 mr-2"></i>
        Outfit Inspiration
      </h3>
      <div className="overflow-x-auto pb-2">
        <div className="flex space-x-4">
          {inspirations.map((item, index) => (
            <div 
              key={index} 
              className="flex-shrink-0 w-48 p-3 bg-gradient-to-br from-gray-50 to-white rounded-lg border border-gray-200 hover:shadow-md transition-all duration-300 hover:-translate-y-1 transform"
            >
              <div className="text-center mb-2">
                <span className="text-xs font-medium px-3 py-1 bg-secondary-100 text-secondary-700 rounded-full">
                  {item.style}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <div className="flex-1 text-center px-2">
                  <div className="text-primary-500 mb-1"><i className="fas fa-tshirt"></i></div>
                  <p className="text-gray-700">{item.top}</p>
                </div>
                <div className="text-gray-400">+</div>
                <div className="flex-1 text-center px-2">
                  <div className="text-primary-500 mb-1"><i className="fas fa-socks"></i></div>
                  <p className="text-gray-700">{item.bottom}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function OutfitMatcher() {
  // State for file inputs
  const [topFile, setTopFile] = useState(null)
  const [bottomFile, setBottomFile] = useState(null)
  
  // State for previews
  const [topPreview, setTopPreview] = useState('')
  const [bottomPreview, setBottomPreview] = useState('')
  
  // State for loading, results and errors
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [progressStatus, setProgressStatus] = useState('')
  const [showTips, setShowTips] = useState(true)

  // Handle file change for top item
  const handleTopFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    setTopFile(file)
    
    // Create preview URL
    const reader = new FileReader()
    reader.onloadend = () => {
      setTopPreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  // Handle file change for bottom item
  const handleBottomFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    setBottomFile(file)
    
    // Create preview URL
    const reader = new FileReader()
    reader.onloadend = () => {
      setBottomPreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate inputs
    if (!topFile || !bottomFile) {
      setError('Please upload both a top and bottom item')
      return
    }
    
    setLoading(true)
    setError('')
    setResults(null)
    setProgressStatus('Initializing...')
    
    try {
      // Create FormData object
      const formData = new FormData()
      formData.append('topwear', topFile)
      formData.append('bottomwear', bottomFile)
      
      // Create a controller for aborting request if it takes too long
      const controller = new AbortController()
      const timeoutId = setTimeout(() => {
        controller.abort()
      }, 60000) // 60 second timeout
      
      setProgressStatus('Starting upload...')
      
      // Make API request with timeout
      const response = await axios.post('/api/match', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        signal: controller.signal,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          const status = `Uploading images... ${percentCompleted}%`;
          setProgressStatus(status)
        }
      })
      
      // Clear timeout since request completed
      clearTimeout(timeoutId)
      
      setProgressStatus('Upload complete, processing response...')
      
      // Check if response has data
      if (!response || !response.data) {
        throw new Error('No data received from server')
      }
      
      setProgressStatus('Rendering results...')
      
      // Set results
      setResults(response.data)
      
    } catch (err) {
      // Clear any results that might be partially set
      setResults(null);
      
      console.error('Error matching outfit:', err)
      
      // Extract the error message
      let errorMessage = '';
      
      // Handle specific error types
      if (err.name === 'AbortError' || err.name === 'TimeoutError') {
        errorMessage = 'Request timed out. The server is taking too long to respond. Please try again later.';
      } else if (err.response) {
        // The request was made and the server responded with a status code outside of 2xx range
        errorMessage = err.response.data?.detail || `Server error: ${err.response.status}`;
      } else if (err.request) {
        // The request was made but no response was received
        errorMessage = 'No response received from server. Please check your connection and try again.';
      } else {
        // Something happened in setting up the request
        errorMessage = err.message || 'Failed to match outfit. Please try again.';
      }
      
      console.log('Raw error message:', errorMessage);
      
      // Process the error message for a more user-friendly display
      if (errorMessage.includes('multiple people') || errorMessage.includes('detected multiple people')) {
        // Multiple people detected in one of the clothing images
        setError("Fashion is meant to be shared, but not in the same photo! Our AI works best with clothing images that have at most one person in them. Please upload photos that show just the clothing item or a single model.");
      } else {
        // For all other errors, clean up the message by removing technical prefixes
        let cleanMessage = errorMessage;
        
        // Remove specific known prefixes
        const prefixesToRemove = [
          "Server error: ",
          "Match analysis failed: ",
          "400: ",
          "500: "
        ];
        
        // Remove each prefix if found
        prefixesToRemove.forEach(prefix => {
          if (cleanMessage.includes(prefix)) {
            cleanMessage = cleanMessage.replace(prefix, '');
          }
        });
        
        // Set the cleaned error message
        setError(cleanMessage.trim());
      }
    } finally {
      setLoading(false)
      setProgressStatus('')
    }
  }

  // Get color for match score
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  // Render match score indicator
  const renderMatchScore = (score) => {
    return (
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32">
          {/* Circular progress background */}
          <svg className="w-32 h-32" viewBox="0 0 100 100">
            <circle 
              className="text-gray-200" 
              strokeWidth="10" 
              stroke="currentColor" 
              fill="transparent" 
              r="42" 
              cx="50" 
              cy="50" 
            />
            {/* Progress circle */}
            <circle 
              className={`${score >= 80 ? 'text-green-500' : score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}
              strokeWidth="10" 
              strokeDasharray={264} 
              strokeDashoffset={264 - (264 * score) / 100} 
              strokeLinecap="round" 
              stroke="currentColor" 
              fill="transparent" 
              r="42" 
              cx="50" 
              cy="50" 
            />
          </svg>
          <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center">
            <span className={`text-3xl font-bold ${getScoreColor(score)}`}>{score}</span>
          </div>
        </div>
        <p className="text-lg font-medium mt-2">Match Score</p>
        <p className="text-sm text-gray-500">
          {score >= 80 ? 'Excellent Match!' : 
           score >= 60 ? 'Good Match' : 
           'Needs Improvement'}
        </p>
      </div>
    )
  }

  useEffect(() => {
    // Component initialization code if needed
    
    return () => {
      // Cleanup code if needed
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white py-12 relative">
      {/* Background texture */}
      <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600 mb-2">
            Outfit Matcher
          </h1>
          <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
            Upload top and bottom garments to see how well they match and get styling suggestions.
          </p>
          <p className="mt-2 text-gray-500 max-w-3xl mx-auto">
            Our AI will automatically detect clothing styles and analyze their compatibility.
          </p>
          
          <div className="flex justify-center mt-4">
            <button 
              onClick={() => setShowTips(!showTips)}
              className="text-primary-500 hover:text-primary-700 transition-colors flex items-center text-sm"
            >
              <i className={`fas fa-${showTips ? 'eye-slash' : 'lightbulb'} mr-2`}></i>
              {showTips ? 'Hide style tips' : 'Show style tips'}
            </button>
          </div>
        </div>

        {showTips && <OutfitStyleTips />}

        {!results && showTips && <OutfitInspirations />}

        <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">
          <div className="p-8">
            {!results ? (
              <form onSubmit={handleSubmit} className="animate-fadeIn">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                  {/* Top Item Section */}
                  <div className="bg-gradient-to-br from-primary-50 to-white p-6 rounded-xl border border-primary-100 transform transition-all duration-300 hover:shadow-md">
                    <h2 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-800 mb-4 flex items-center">
                      <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mr-3 text-primary-500">
                        <i className="fas fa-tshirt"></i>
                      </div>
                      Top Item
                    </h2>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                          <i className="fas fa-upload text-primary-500 mr-2"></i>
                          Upload Top Garment
                        </label>
                        {!topFile ? (
                          <div 
                            onClick={() => document.getElementById('top-file').click()}
                            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-all duration-300 hover:border-primary-300 hover:bg-primary-50"
                          >
                            <input
                              id="top-file"
                              type="file"
                              onChange={handleTopFileChange}
                              accept="image/*"
                              className="hidden"
                            />
                            <div className="mx-auto w-16 h-16 text-primary-300">
                              <i className="fas fa-tshirt text-5xl"></i>
                            </div>
                            <p className="text-gray-600 font-medium mt-3">Drag and drop or click to upload</p>
                            <p className="text-gray-500 text-xs mt-2">
                              Supported formats: JPG, PNG, WEBP. Max size: 10MB
                            </p>
                          </div>
                        ) : (
                          <div className="relative group">
                            <div className="border-2 border-primary-200 bg-primary-50 rounded-lg p-3 relative overflow-hidden">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-medium text-primary-600 inline-flex items-center">
                                  <i className="fas fa-check-circle mr-1"></i> 
                                  Uploaded
                                </span>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setTopFile(null);
                                    setTopPreview('');
                                  }}
                                  className="text-red-500 hover:text-red-700 transition-colors text-xs"
                                >
                                  <i className="fas fa-times mr-1"></i> Remove
                                </button>
                              </div>
                              <div className="flex items-center text-xs text-gray-500">
                                <i className="fas fa-file-image text-primary-400 mr-2"></i>
                                <span className="truncate">{topFile.name}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-4">
                        {topPreview ? (
                          <div className="bg-white rounded-lg p-2 relative group shadow-sm overflow-hidden">
                            <img 
                              src={topPreview} 
                              alt="Top Preview" 
                              className="max-h-64 mx-auto rounded object-contain transform transition-transform duration-500 group-hover:scale-105"
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 rounded-lg">
                              <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300">
                                <button 
                                  type="button"
                                  onClick={() => document.getElementById('top-file').click()}
                                  className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors"
                                >
                                  <i className="fas fa-exchange-alt"></i>
                                </button>
                                <button 
                                  type="button"
                                  onClick={() => {
                                    setTopFile(null);
                                    setTopPreview('');
                                  }}
                                  className="bg-white text-red-500 rounded-full w-10 h-10 flex items-center justify-center shadow-md hover:bg-red-50 transition-colors"
                                >
                                  <i className="fas fa-trash-alt"></i>
                                </button>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="border border-gray-200 rounded-lg p-12 text-center bg-white">
                            <div className="text-gray-300 text-5xl mb-3 mx-auto w-16 h-16 flex items-center justify-center">
                              <i className="fas fa-tshirt"></i>
                            </div>
                            <p className="text-gray-400">Top item preview will appear here</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                
                  {/* Bottom Item Section */}
                  <div className="bg-gradient-to-br from-secondary-50 to-white p-6 rounded-xl border border-secondary-100 transform transition-all duration-300 hover:shadow-md">
                    <h2 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-secondary-800 mb-4 flex items-center">
                      <div className="w-10 h-10 bg-secondary-100 rounded-full flex items-center justify-center mr-3 text-secondary-500">
                        <i className="fas fa-socks"></i>
                      </div>
                      Bottom Item
                    </h2>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                          <i className="fas fa-upload text-secondary-500 mr-2"></i>
                          Upload Bottom Garment
                        </label>
                        {!bottomFile ? (
                          <div 
                            onClick={() => document.getElementById('bottom-file').click()}
                            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-all duration-300 hover:border-secondary-300 hover:bg-secondary-50"
                          >
                            <input
                              id="bottom-file"
                              type="file"
                              onChange={handleBottomFileChange}
                              accept="image/*"
                              className="hidden"
                            />
                            <div className="mx-auto w-16 h-16 text-secondary-300">
                              <i className="fas fa-socks text-5xl"></i>
                            </div>
                            <p className="text-gray-600 font-medium mt-3">Drag and drop or click to upload</p>
                            <p className="text-gray-500 text-xs mt-2">
                              Supported formats: JPG, PNG, WEBP. Max size: 10MB
                            </p>
                          </div>
                        ) : (
                          <div className="relative group">
                            <div className="border-2 border-secondary-200 bg-secondary-50 rounded-lg p-3 relative overflow-hidden">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-medium text-secondary-600 inline-flex items-center">
                                  <i className="fas fa-check-circle mr-1"></i> 
                                  Uploaded
                                </span>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setBottomFile(null);
                                    setBottomPreview('');
                                  }}
                                  className="text-red-500 hover:text-red-700 transition-colors text-xs"
                                >
                                  <i className="fas fa-times mr-1"></i> Remove
                                </button>
                              </div>
                              <div className="flex items-center text-xs text-gray-500">
                                <i className="fas fa-file-image text-secondary-400 mr-2"></i>
                                <span className="truncate">{bottomFile.name}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-4">
                        {bottomPreview ? (
                          <div className="bg-white rounded-lg p-2 relative group shadow-sm overflow-hidden">
                            <img 
                              src={bottomPreview} 
                              alt="Bottom Preview" 
                              className="max-h-64 mx-auto rounded object-contain transform transition-transform duration-500 group-hover:scale-105"
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 rounded-lg">
                              <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300">
                                <button 
                                  type="button"
                                  onClick={() => document.getElementById('bottom-file').click()}
                                  className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors"
                                >
                                  <i className="fas fa-exchange-alt"></i>
                                </button>
                                <button 
                                  type="button"
                                  onClick={() => {
                                    setBottomFile(null);
                                    setBottomPreview('');
                                  }}
                                  className="bg-white text-red-500 rounded-full w-10 h-10 flex items-center justify-center shadow-md hover:bg-red-50 transition-colors"
                                >
                                  <i className="fas fa-trash-alt"></i>
                                </button>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="border border-gray-200 rounded-lg p-12 text-center bg-white">
                            <div className="text-gray-300 text-5xl mb-3 mx-auto w-16 h-16 flex items-center justify-center">
                              <i className="fas fa-socks"></i>
                            </div>
                            <p className="text-gray-400">Bottom item preview will appear here</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                {error && (
                  <div className="mt-8 p-6 bg-red-50 text-red-700 rounded-xl border-l-4 border-red-500 animate-fadeIn">
                    <div className="flex items-start">
                      <div className="text-red-500 text-2xl mr-4 mt-1">
                        {error.includes("multiple people") ? (
                          <i className="fas fa-users"></i>
                        ) : (
                          <i className="fas fa-exclamation-circle"></i>
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-lg">
                          {error.includes("multiple people") ? "Multiple People Detected" : "Something went wrong"}
                        </p>
                        <p className="mt-2">{error}</p>
                        
                        {error.includes("multiple people") && (
                          <div className="mt-3 p-3 bg-white rounded-md text-gray-700 text-sm border border-red-200">
                            <p className="font-medium mb-2">Tips for better results:</p>
                            <ul className="list-disc pl-5 space-y-1">
                              <li>Use photos that show just the clothing item without people</li>
                              <li>If you need to use a model photo, ensure only one person is visible</li>
                              <li>Crop your images before uploading to remove extra people</li>
                              <li>Take a clean product photo against a neutral background</li>
                            </ul>
                          </div>
                        )}
                        
                        <button 
                          onClick={() => setError('')}
                          className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md text-sm hover:bg-red-200 transition-colors inline-flex items-center"
                        >
                          <i className="fas fa-times mr-2"></i>
                          Dismiss
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="mt-10 flex justify-center">
                  <button
                    type="submit"
                    disabled={loading || !topFile || !bottomFile}
                    className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-full shadow-lg text-white bg-gradient-to-r from-primary-500 to-secondary-600 hover:from-primary-600 hover:to-secondary-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:-translate-y-1"
                  >
                    {loading ? (
                      <>
                        <i className="fas fa-circle-notch fa-spin mr-3"></i>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-magic mr-2"></i>
                        Check Outfit Match
                      </>
                    )}
                  </button>
                </div>
                
                {loading && (
                  <div className="mt-8 p-6 bg-gradient-to-r from-primary-50 to-secondary-50 border border-secondary-100 rounded-xl animate-pulse-subtle overflow-hidden relative">
                    <div className="absolute -right-12 -bottom-12 opacity-5 text-9xl">
                      <i className="fas fa-tshirt"></i>
                    </div>
                    <div className="relative z-10">
                      <div className="flex items-start">
                        <div className="mr-4 mt-1">
                          <div className="relative w-12 h-12">
                            <div className="absolute inset-0 rounded-full border-t-4 border-r-4 border-secondary-500 animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                              <i className="fas fa-tshirt text-secondary-500"></i>
                            </div>
                          </div>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-medium text-gray-800 mb-1">Analyzing Your Outfit</h3>
                          <p className="text-gray-600">{progressStatus || 'Processing your fashion items...'}</p>
                          
                          <div className="mt-5 w-full bg-white rounded-full h-3 shadow-inner overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-primary-500 via-secondary-400 to-primary-500 rounded-full animate-gradient-x" style={{ width: '100%' }}></div>
                          </div>
                          
                          <div className="grid grid-cols-4 gap-2 mt-4">
                            <div className="text-center">
                              <div className="w-8 h-8 mx-auto rounded-full bg-primary-100 flex items-center justify-center">
                                <i className={`fas fa-check text-primary-500 ${progressStatus.includes('Upload') ? 'animate-bounce-slow' : ''}`}></i>
                              </div>
                              <p className="text-xs mt-1 text-gray-500">Upload</p>
                            </div>
                            <div className="text-center">
                              <div className="w-8 h-8 mx-auto rounded-full bg-secondary-100 flex items-center justify-center">
                                <i className={`fas ${progressStatus.includes('Analyzing') ? 'fa-spinner fa-spin text-secondary-500' : 'fa-search text-gray-400'}`}></i>
                              </div>
                              <p className="text-xs mt-1 text-gray-500">Analysis</p>
                            </div>
                            <div className="text-center">
                              <div className="w-8 h-8 mx-auto rounded-full bg-gray-100 flex items-center justify-center">
                                <i className="fas fa-hand-holding-heart text-gray-400"></i>
                              </div>
                              <p className="text-xs mt-1 text-gray-500">Matching</p>
                            </div>
                            <div className="text-center">
                              <div className="w-8 h-8 mx-auto rounded-full bg-gray-100 flex items-center justify-center">
                                <i className="fas fa-chart-pie text-gray-400"></i>
                              </div>
                              <p className="text-xs mt-1 text-gray-500">Results</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </form>
            ) : (
              <div className="results-section animate-fadeIn">
                <div className="text-center mb-12">
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600 mb-2">
                    Outfit Analysis Results
                  </h2>
                  <p className="text-gray-600 max-w-3xl mx-auto">
                    Our AI has analyzed your items for style compatibility, color harmony, and seasonal appropriateness.
                  </p>
                </div>
                
                <div className="flex flex-col md:flex-row gap-8 mb-12 items-center">
                  <div className="flex-1 bg-gradient-to-tr from-primary-50 to-white p-6 rounded-xl border border-primary-100 shadow-sm text-center transform transition-all duration-300 hover:shadow-md">
                    <h3 className="text-lg font-medium mb-3 text-primary-700 inline-flex items-center">
                      <i className="fas fa-tshirt mr-2 text-primary-500"></i>
                      Top Item
                    </h3>
                    <div className="relative group overflow-hidden rounded-lg">
                      {topPreview && (
                        <img 
                          src={topPreview} 
                          alt="Top Item" 
                          className="max-h-64 mx-auto rounded shadow-sm transition-all duration-500 group-hover:scale-105"
                        />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300"></div>
                    </div>
                    <p className="mt-4 text-gray-700 font-medium px-4 py-2 bg-white rounded-full shadow-sm inline-block capitalize">
                      {results.analysis?.style_consistency?.analysis && 
                       results.analysis.style_consistency.analysis.includes('top') ? 
                        results.analysis.style_consistency.analysis.match(/(\w+) top/i)?.[1] || 'Detected' : 
                        'Detected'} Style
                    </p>
                  </div>
                  
                  <div className="text-center -my-4">
                    <div className="w-16 h-16 rounded-full bg-white shadow-md flex items-center justify-center text-2xl text-gray-400 mx-auto">
                      <i className="fas fa-plus"></i>
                    </div>
                  </div>
                  
                  <div className="flex-1 bg-gradient-to-tr from-secondary-50 to-white p-6 rounded-xl border border-secondary-100 shadow-sm text-center transform transition-all duration-300 hover:shadow-md">
                    <h3 className="text-lg font-medium mb-3 text-secondary-700 inline-flex items-center">
                      <i className="fas fa-socks mr-2 text-secondary-500"></i>
                      Bottom Item
                    </h3>
                    <div className="relative group overflow-hidden rounded-lg">
                      {bottomPreview && (
                        <img 
                          src={bottomPreview} 
                          alt="Bottom Item" 
                          className="max-h-64 mx-auto rounded shadow-sm transition-all duration-500 group-hover:scale-105"
                        />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300"></div>
                    </div>
                    <p className="mt-4 text-gray-700 font-medium px-4 py-2 bg-white rounded-full shadow-sm inline-block capitalize">
                      {results.analysis?.style_consistency?.analysis && 
                       results.analysis.style_consistency.analysis.includes('bottom') ? 
                        results.analysis.style_consistency.analysis.match(/(\w+) bottom/i)?.[1] || 'Detected' : 
                        'Detected'} Style
                    </p>
                  </div>
                </div>
                
                <div className="text-center mb-12 transform transition-all duration-500 hover:-translate-y-2">
                  <div className="inline-block p-10 bg-white rounded-2xl shadow-lg border border-gray-100">
                    {renderMatchScore(parseInt(results.match_score) || 0)}
                    
                    <p className="mt-4 text-gray-600 max-w-md mx-auto">
                      {parseInt(results.match_score) >= 80 
                        ? "These items complement each other perfectly! This outfit is well-balanced and stylish."
                        : parseInt(results.match_score) >= 60
                        ? "These items work well together, but there's room for improvement. Check the analysis below."
                        : "These items might not be the best match. See our detailed analysis and suggestions below."}
                    </p>
                  </div>
                </div>
                
                <div className="mb-12">
                  <h3 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600 mb-6 inline-flex items-center">
                    <i className="fas fa-chart-line mr-2 text-secondary-500"></i>
                    Detailed Analysis
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {typeof results.analysis === 'object' && results.analysis !== null 
                      ? Object.entries(results.analysis).map(([key, value]) => {
                        const score = value && typeof value === 'object' ? (value.score || 0) : 0;
                        const analysis = value && typeof value === 'object' ? (value.analysis || 'No analysis available') : 'No analysis available';
                        const icon = 
                          key.includes('color') ? 'palette' : 
                          key.includes('style') ? 'tshirt' : 
                          key.includes('seasonal') ? 'sun' : 
                          key.includes('occasion') ? 'calendar' : 
                          'chart-pie';
                        
                        return (
                          <div 
                            key={key} 
                            className={`bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all duration-300 transform hover:-translate-y-1 hover:shadow-md
                              ${score >= 80 ? 'hover:border-green-200' : 
                                score >= 60 ? 'hover:border-yellow-200' : 
                                'hover:border-red-200'}`}
                          >
                            <div className="flex items-center mb-4">
                              <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3
                                ${score >= 80 ? 'bg-green-100 text-green-500' : 
                                  score >= 60 ? 'bg-yellow-100 text-yellow-600' : 
                                  'bg-red-100 text-red-500'}`}
                              >
                                <i className={`fas fa-${icon}`}></i>
                              </div>
                              <h4 className="font-medium text-gray-800 capitalize flex-1">
                                {key.replace(/_/g, ' ')}
                              </h4>
                              <span className={`font-bold text-lg px-2 py-1 rounded-full
                                ${score >= 80 ? 'bg-green-100 text-green-700' : 
                                  score >= 60 ? 'bg-yellow-100 text-yellow-700' : 
                                  'bg-red-100 text-red-700'}`}
                              >
                                {score}
                              </span>
                            </div>
                            <p className="text-gray-600">{analysis}</p>
                            <div className="mt-4 w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${
                                  score >= 80 ? 'bg-gradient-to-r from-green-400 to-green-500' : 
                                  score >= 60 ? 'bg-gradient-to-r from-yellow-400 to-yellow-500' : 
                                  'bg-gradient-to-r from-red-400 to-red-500'
                                }`}
                                style={{ width: `${score}%`, transition: 'width 1s ease-in-out' }}
                              ></div>
                            </div>
                          </div>
                        );
                      })
                      : (
                        <div className="bg-yellow-50 p-6 rounded-xl col-span-2 text-center text-yellow-700 border border-yellow-200">
                          <div className="text-yellow-500 text-4xl mb-4">
                            <i className="fas fa-exclamation-triangle"></i>
                          </div>
                          <p className="font-medium">Detailed analysis is not available</p>
                          <p className="text-sm mt-2">Our AI couldn't generate a detailed breakdown for this outfit.</p>
                        </div>
                      )
                    }
                  </div>
                </div>
                
                {Array.isArray(results.suggestions) && results.suggestions.length > 0 && (
                  <div className="mb-12">
                    <h3 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600 mb-6 inline-flex items-center">
                      <i className="fas fa-lightbulb mr-2 text-primary-500 animate-pulse-subtle"></i>
                      Styling Suggestions
                    </h3>
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100 shadow-sm">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {results.suggestions.map((suggestion, index) => (
                          <div key={index} className="flex items-start bg-white p-4 rounded-lg shadow-sm transform transition-all duration-300 hover:-translate-y-1 hover:shadow-md">
                            <div className="bg-blue-100 text-blue-500 w-8 h-8 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                              <i className="fas fa-lightbulb"></i>
                            </div>
                            <div>
                              <p className="text-gray-800">{typeof suggestion === 'string' ? suggestion : 'Styling suggestion'}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="flex justify-center mt-12 space-x-4">
                  <button
                    onClick={() => {
                      setResults(null)
                      setTopFile(null)
                      setBottomFile(null)
                      setTopPreview('')
                      setBottomPreview('')
                    }}
                    className="inline-flex items-center px-6 py-3 border border-secondary-200 shadow-sm rounded-full text-secondary-700 bg-white hover:bg-secondary-50 focus:outline-none transition-all duration-300"
                  >
                    <i className="fas fa-redo mr-2"></i>
                    Try Another Outfit
                  </button>
                  
                  <button
                    onClick={() => {
                      // Here you would implement save or share functionality
                      // For now, we'll just create a download of the match results
                      const element = document.createElement('a');
                      const file = new Blob([JSON.stringify(results, null, 2)], {type: 'application/json'});
                      element.href = URL.createObjectURL(file);
                      element.download = `outfit-match-${new Date().toISOString().slice(0,10)}.json`;
                      document.body.appendChild(element);
                      element.click();
                      document.body.removeChild(element);
                    }}
                    className="inline-flex items-center px-6 py-3 border border-transparent shadow-sm rounded-full text-white bg-gradient-to-r from-primary-500 to-secondary-500 hover:from-primary-600 hover:to-secondary-600 focus:outline-none transition-all duration-300"
                  >
                    <i className="fas fa-download mr-2"></i>
                    Save Results
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default OutfitMatcher 