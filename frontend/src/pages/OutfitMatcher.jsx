import React, { useState, useEffect } from 'react'
import axios from 'axios'

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
  const [debugInfo, setDebugInfo] = useState(null)

  // Debug mode flag
  const DEBUG = true;

  // Log function for conditional logging
  const debugLog = (message, data) => {
    if (DEBUG) {
      console.log(`[OutfitMatcher] ${message}`, data);
    }
  };

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
    debugLog('Top file selected', file.name);
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
    debugLog('Bottom file selected', file.name);
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
    setDebugInfo(null)
    
    try {
      // Create FormData object
      const formData = new FormData()
      formData.append('topwear', topFile)
      formData.append('bottomwear', bottomFile)
      
      debugLog('FormData created', {
        topwear: topFile.name,
        bottomwear: bottomFile.name
      });
      
      // Create a controller for aborting request if it takes too long
      const controller = new AbortController()
      const timeoutId = setTimeout(() => {
        debugLog('Request timeout triggered', { timeout: '60 seconds' });
        controller.abort()
      }, 60000) // 60 second timeout
      
      setProgressStatus('Starting upload...')
      
      debugLog('Making API request', '/api/match');

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
          debugLog('Upload progress', { percent: percentCompleted });
        }
      })
      
      // Clear timeout since request completed
      clearTimeout(timeoutId)
      
      setProgressStatus('Upload complete, processing response...')
      debugLog('Response received', { status: response.status });
      
      // Check if response has data
      if (!response || !response.data) {
        throw new Error('No data received from server')
      }
      
      // Always save the response data for debugging, regardless of format
      setDebugInfo({
        message: 'Raw server response',
        data: response.data
      });
      
      // Log the response data for debugging
      debugLog('Response data', response.data);
      
      // Detailed validation of response structure
      if (!response.data.match_score) {
        debugLog('Missing match_score in response', response.data);
        throw new Error('Invalid response format: Missing match_score field');
      }
      
      if (!response.data.analysis) {
        debugLog('Missing analysis in response', response.data);
        throw new Error('Invalid response format: Missing analysis field');
      }
      
      debugLog('Response validation passed', { 
        match_score: response.data.match_score,
        analysis_keys: Object.keys(response.data.analysis)
      });
      
      setProgressStatus('Rendering results...')
      
      // Set results
      setResults(response.data)
      
      debugLog('Results set successfully', { 
        match_score: response.data.match_score,
        analysis_count: Object.keys(response.data.analysis).length,
        suggestions_count: response.data.suggestions?.length || 0
      });
      
    } catch (err) {
      // Clear any results that might be partially set
      setResults(null);
      
      debugLog('Error caught', { 
        name: err.name, 
        message: err.message, 
        response: err.response, 
        stack: err.stack 
      });
      
      console.error('Error matching outfit:', err)
      
      // Handle specific error types
      if (err.name === 'AbortError' || err.name === 'TimeoutError') {
        setError('Request timed out. The server is taking too long to respond. Please try again later.');
      } else if (err.response) {
        // The request was made and the server responded with a status code outside of 2xx range
        setError(err.response.data?.detail || `Server error: ${err.response.status}`);
        setDebugInfo({
          message: 'Server error response',
          status: err.response.status,
          data: err.response.data
        });
      } else if (err.request) {
        // The request was made but no response was received
        setError('No response received from server. Please check your connection and try again.');
        setDebugInfo({
          message: 'No response from server',
          request: err.request
        });
      } else {
        // Something happened in setting up the request
        setError(err.message || 'Failed to match outfit. Please try again.');
        // Keep any debug info that was set earlier
        if (!debugInfo) {
          setDebugInfo({
            message: 'General error',
            error: err.toString()
          });
        }
      }
    } finally {
      setLoading(false)
      setProgressStatus('')
      debugLog('Request completed', { success: !!results, error: !!error });
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

  // Log initialization
  useEffect(() => {
    debugLog('OutfitMatcher component mounted', { debug_mode: DEBUG });
    
    return () => {
      debugLog('OutfitMatcher component unmounted', {});
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-primary">Outfit Matcher</h1>
          <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
            Upload top and bottom garments to see how well they match and get styling suggestions.
          </p>
          <p className="mt-2 text-sm text-gray-500 max-w-3xl mx-auto">
            Our AI will automatically detect clothing styles and analyze their compatibility.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-6 md:p-8">
            {!results ? (
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Top Item Section */}
                  <div>
                    <h2 className="text-xl font-semibold text-primary mb-4 flex items-center">
                      <i className="fas fa-tshirt mr-2"></i>
                      Top Item
                    </h2>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Upload Top Garment
                        </label>
                        <div className="relative">
                          <input
                            id="top-file"
                            type="file"
                            onChange={handleTopFileChange}
                            accept="image/*"
                            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-secondary file:text-white hover:file:bg-blue-600"
                          />
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                          Supported formats: JPG, PNG, WEBP. Max size: 10MB
                        </p>
                      </div>
                      
                      <div className="mt-4">
                        {topPreview ? (
                          <div className="bg-gray-100 rounded-lg p-2 relative group">
                            <img 
                              src={topPreview} 
                              alt="Top Preview" 
                              className="max-h-64 mx-auto rounded object-contain"
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 rounded-lg">
                              <button 
                                type="button"
                                onClick={() => document.getElementById('top-file').click()}
                                className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all duration-300"
                              >
                                <i className="fas fa-sync"></i>
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                            <i className="fas fa-tshirt text-gray-400 text-5xl mb-3"></i>
                            <p className="text-gray-500">Top preview will appear here</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                
                  {/* Bottom Item Section */}
                  <div>
                    <h2 className="text-xl font-semibold text-primary mb-4 flex items-center">
                      <i className="fas fa-socks mr-2"></i>
                      Bottom Item
                    </h2>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Upload Bottom Garment
                        </label>
                        <div className="relative">
                          <input
                            id="bottom-file"
                            type="file"
                            onChange={handleBottomFileChange}
                            accept="image/*"
                            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-secondary file:text-white hover:file:bg-blue-600"
                          />
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                          Supported formats: JPG, PNG, WEBP. Max size: 10MB
                        </p>
                      </div>
                      
                      <div className="mt-4">
                        {bottomPreview ? (
                          <div className="bg-gray-100 rounded-lg p-2 relative group">
                            <img 
                              src={bottomPreview} 
                              alt="Bottom Preview" 
                              className="max-h-64 mx-auto rounded object-contain"
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 rounded-lg">
                              <button 
                                type="button"
                                onClick={() => document.getElementById('bottom-file').click()}
                                className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all duration-300"
                              >
                                <i className="fas fa-sync"></i>
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                            <i className="fas fa-socks text-gray-400 text-5xl mb-3"></i>
                            <p className="text-gray-500">Bottom preview will appear here</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                {error && (
                  <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-md">
                    <p className="font-medium flex items-center">
                      <i className="fas fa-exclamation-circle mr-2"></i>
                      Error
                    </p>
                    <p>{error}</p>
                    {DEBUG && (
                      <div className="mt-2 p-2 bg-gray-800 text-gray-200 rounded text-xs overflow-auto">
                        <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Always show debug info in debug mode, even without error */}
                {!error && debugInfo && DEBUG && (
                  <div className="mt-6 p-4 bg-blue-50 text-blue-700 rounded-md">
                    <p className="font-medium flex items-center">
                      <i className="fas fa-bug mr-2"></i>
                      Debug Information
                    </p>
                    <div className="mt-2 p-2 bg-gray-800 text-gray-200 rounded text-xs overflow-auto">
                      <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
                    </div>
                  </div>
                )}
                
                <div className="mt-8 flex justify-center">
                  <button
                    type="submit"
                    disabled={loading || !topFile || !bottomFile}
                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-secondary hover:bg-blue-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <i className="fas fa-circle-notch fa-spin mr-2"></i>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-tshirt mr-2"></i>
                        Check Match
                      </>
                    )}
                  </button>
                </div>
                
                {loading && (
                  <div className="mt-6 p-4 bg-blue-50 border border-blue-100 rounded-md">
                    <div className="flex items-center">
                      <i className="fas fa-spinner fa-spin text-blue-500 mr-3"></i>
                      <p className="text-blue-700">{progressStatus || 'Processing...'}</p>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-1.5 mt-3">
                      <div className="bg-blue-500 h-1.5 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                    </div>
                  </div>
                )}
              </form>
            ) : (
              <div className="results-section">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                  <div className="text-center">
                    <h3 className="text-lg font-medium mb-3 text-gray-700">Top Item</h3>
                    <div className="bg-gray-50 p-2 rounded-lg">
                      {topPreview && (
                        <img 
                          src={topPreview} 
                          alt="Top Item" 
                          className="max-h-64 mx-auto rounded"
                        />
                      )}
                    </div>
                    <p className="mt-2 text-gray-600 font-medium capitalize">
                      {results.analysis?.style_consistency?.analysis && 
                       results.analysis.style_consistency.analysis.includes('top') ? 
                        results.analysis.style_consistency.analysis.match(/(\w+) top/i)?.[1] || 'Detected' : 
                        'Detected'} Style
                    </p>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="text-lg font-medium mb-3 text-gray-700">Bottom Item</h3>
                    <div className="bg-gray-50 p-2 rounded-lg">
                      {bottomPreview && (
                        <img 
                          src={bottomPreview} 
                          alt="Bottom Item" 
                          className="max-h-64 mx-auto rounded"
                        />
                      )}
                    </div>
                    <p className="mt-2 text-gray-600 font-medium capitalize">
                      {results.analysis?.style_consistency?.analysis && 
                       results.analysis.style_consistency.analysis.includes('bottom') ? 
                        results.analysis.style_consistency.analysis.match(/(\w+) bottom/i)?.[1] || 'Detected' : 
                        'Detected'} Style
                    </p>
                  </div>
                </div>
                
                <div className="text-center mb-8">
                  {renderMatchScore(parseInt(results.match_score) || 0)}
                </div>
                
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-primary mb-4">Detailed Analysis</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {typeof results.analysis === 'object' && results.analysis !== null 
                      ? Object.entries(results.analysis).map(([key, value]) => {
                        const score = value && typeof value === 'object' ? (value.score || 0) : 0;
                        const analysis = value && typeof value === 'object' ? (value.analysis || 'No analysis available') : 'No analysis available';
                        
                        return (
                          <div key={key} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-800 capitalize">
                                {key.replace(/_/g, ' ')}
                              </h4>
                              <span className={`font-bold ${getScoreColor(score)}`}>
                                {score}/100
                              </span>
                            </div>
                            <p className="text-gray-600 text-sm">{analysis}</p>
                            <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                              <div 
                                className={`h-1.5 rounded-full ${score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                style={{ width: `${score}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })
                      : (
                        <div className="bg-yellow-50 p-4 rounded-lg col-span-2 text-center text-yellow-700">
                          <p>No detailed analysis available</p>
                        </div>
                      )
                    }
                  </div>
                </div>
                
                {Array.isArray(results.suggestions) && results.suggestions.length > 0 && (
                  <div className="mb-8">
                    <h3 className="text-xl font-semibold text-primary mb-4">Styling Suggestions</h3>
                    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-md">
                      <ul className="space-y-2">
                        {results.suggestions.map((suggestion, index) => (
                          <li key={index} className="flex items-start">
                            <i className="fas fa-lightbulb text-blue-500 mt-1 mr-2"></i>
                            <span>{typeof suggestion === 'string' ? suggestion : 'Styling suggestion'}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
                
                {DEBUG && (
                  <div className="mb-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <details>
                      <summary className="font-medium text-gray-700 cursor-pointer">Debug Information</summary>
                      <div className="mt-2 p-2 bg-gray-800 text-gray-200 rounded text-xs overflow-auto">
                        <pre>{JSON.stringify(results, null, 2)}</pre>
                      </div>
                    </details>
                  </div>
                )}
                
                <div className="flex justify-center mt-8">
                  <button
                    onClick={() => {
                      setResults(null)
                      setTopFile(null)
                      setBottomFile(null)
                      setTopPreview('')
                      setBottomPreview('')
                      setDebugInfo(null)
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none"
                  >
                    <i className="fas fa-redo mr-2"></i>
                    Try Another Outfit
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