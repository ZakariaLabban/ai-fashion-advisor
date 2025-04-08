import React, { useState, useEffect } from 'react'
import axios from 'axios'
import FashionFacts from '../components/FashionFacts'

function Analyze() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [debugData, setDebugData] = useState(null)
  const [rawResponse, setRawResponse] = useState(null)
  const [activeTab, setActiveTab] = useState('upload')
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreviewUrl(URL.createObjectURL(selectedFile))
      setResults(null)
      setError('')
      setDebugData(null)
      setRawResponse(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      setError('Please select an image to upload.')
      return
    }

    setLoading(true)
    setError('')
    setResults(null)
    setDebugData(null)
    setRawResponse(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('Sending request to /api/analyze...')
      const response = await axios.post('/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        responseType: 'text'  // Force text response type
      })

      console.log('Raw API response:', response)
      
      // Store full raw response for debugging
      setRawResponse(response.data)
      
      if (response.data) {
        try {
          // First try to parse as JSON
          const jsonData = JSON.parse(response.data)
          setResults(jsonData)
          setDebugData(JSON.stringify(jsonData, null, 2))
        } catch (parseError) {
          // If it's not JSON, it's probably HTML (direct response)
          if (response.data.includes('<!DOCTYPE html>')) {
            // Create a temporary iframe to display the HTML response
            const htmlContainer = document.createElement('div')
            htmlContainer.innerHTML = response.data
            
            // Extract important data from the HTML response
            const detectionItems = htmlContainer.querySelectorAll('.detection-box')
            const styleItems = htmlContainer.querySelectorAll('.style-item')
            
            // Create a synthetic results object from the HTML
            const extractedResults = {
              detections: Array.from(detectionItems).map((item, index) => {
                const title = item.querySelector('.detection-header h3').textContent
                const className = title.split(' (')[0]
                const confidence = parseFloat(title.match(/Confidence: ([\d.]+)/)[1])
                const imgSrc = item.querySelector('img').src
                
                return {
                  class_name: className,
                  confidence: confidence,
                  crop_path: imgSrc,
                  bbox: [0, 0, 0, 0] // Placeholder since we can't extract this from HTML
                }
              }),
              styles: Array.from(styleItems).map((item) => {
                const styleName = item.querySelector('.style-name').textContent
                const confidenceText = item.querySelector('.confidence-value').textContent
                const confidence = parseFloat(confidenceText.replace('%', '')) / 100
                
                return {
                  style_name: styleName,
                  style_id: 0, // Placeholder
                  confidence: confidence
                }
              }),
              // Use regex to extract requestId and other metadata
              request_id: response.data.match(/Request ID:<\/strong> ([^<]+)/)?.[1] || '',
              original_image_path: htmlContainer.querySelector('.images-container .image-box:first-child img')?.src || '',
              annotated_image_path: htmlContainer.querySelector('.images-container .image-box:nth-child(2) img')?.src || ''
            }
            
            setResults(extractedResults)
            setDebugData("HTML response successfully parsed")
            // Switch to results tab after successful analysis
            setActiveTab('results')
          } else {
            // Neither JSON nor HTML, so it's probably an error message
            setError('Received unrecognized response format from server')
            setDebugData(response.data)
          }
        }
      } else {
        setError('Received empty response from server')
      }
    } catch (err) {
      console.error('Error analyzing image:', err)
      
      // Display detailed error information
      let errorMessage = `Error analyzing image: ${err.message}`;
      let errorDetails = '';
      
      if (err.response) {
        // The server responded with a status code outside the 2xx range
        console.log('Error response:', err.response);
        errorMessage += ` (Status: ${err.response.status})`;
        
        if (err.response.data) {
          if (typeof err.response.data === 'object') {
            // Try to extract error details from response data
            const errorDetail = err.response.data.detail || err.response.data.error || JSON.stringify(err.response.data);
            errorDetails = errorDetail;
          } else if (typeof err.response.data === 'string') {
            errorDetails = err.response.data;
          }
        }
      }
      
      setError(errorMessage);
      setDebugData(errorDetails || JSON.stringify(err, null, 2));
    } finally {
      setLoading(false)
      // If we got results, switch to results tab
      if (rawResponse && rawResponse.includes('<!DOCTYPE html>')) {
        setActiveTab('results')
      }
    }
  }

  // Helper function to display any object property safely
  const displayProperty = (obj, property, defaultValue = 'N/A') => {
    try {
      if (!obj) return defaultValue
      return obj[property] || defaultValue
    } catch (e) {
      console.error(`Error accessing ${property}:`, e)
      return defaultValue
    }
  }

  const displayStyles = (styles) => {
    if (!styles || !Array.isArray(styles) || styles.length === 0) {
      return <p className="text-gray-500">No style classification available.</p>
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {styles.map((style, index) => (
          <div key={index} className="p-4 bg-white rounded-md shadow-sm mb-2 hover:shadow-md transition-all duration-300 border-l-4 border-secondary">
            <p className="font-medium text-primary">
              {displayProperty(style, 'style_name') || displayProperty(style, 'style')}
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-gradient-to-r from-blue-400 to-secondary h-2.5 rounded-full" 
                style={{ width: `${displayProperty(style, 'confidence', 0) * 100}%` }}
              ></div>
            </div>
            <p className="text-right text-sm text-gray-500 mt-1">
              {(displayProperty(style, 'confidence', 0) * 100).toFixed(2)}%
            </p>
          </div>
        ))}
      </div>
    )
  }

  const displayDetections = (detections) => {
    if (!detections || !Array.isArray(detections) || detections.length === 0) {
      return <p className="text-gray-500">No clothing items detected in the image.</p>
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {detections.map((item, index) => (
          <div key={index} className="p-4 bg-white rounded-md shadow-sm border hover:shadow-md transition-all duration-300 flex flex-col">
            <p className="font-medium text-primary mb-2">
              {displayProperty(item, 'class_name')} 
            </p>
            <div className="relative">
              <div className="bg-gray-200 rounded-full h-2.5 mb-1">
                <div 
                  className="bg-gradient-to-r from-green-400 to-blue-500 h-2.5 rounded-full" 
                  style={{ width: `${displayProperty(item, 'confidence', 0) * 100}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>0%</span>
                <span>{(displayProperty(item, 'confidence', 0) * 100).toFixed(2)}%</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const displayFeatures = (detections) => {
    if (!detections || !Array.isArray(detections)) {
      return <p className="text-gray-500">No feature extraction data available.</p>
    }

    const detectionsWithFeatures = detections.filter(
      item => item.features && Array.isArray(item.features) && item.features.length > 0
    )

    if (detectionsWithFeatures.length === 0) {
      return <p className="text-gray-500">No feature extraction data available.</p>
    }

    return (
      <div className="space-y-4">
        <p className="text-sm text-primary font-medium">Feature vectors extracted successfully for {detectionsWithFeatures.length} items</p>
        {detectionsWithFeatures.map((item, index) => (
          <div key={index} className="p-4 bg-white rounded-md shadow-sm hover:shadow-md transition-all duration-300">
            <p className="text-sm font-medium text-gray-800">{displayProperty(item, 'class_name')}:</p>
            <p className="text-sm font-mono bg-gray-50 p-2 rounded mt-2 overflow-x-auto">
              [{item.features.slice(0, 8).map(v => Number(v).toFixed(4)).join(', ')}...]
            </p>
          </div>
        ))}
      </div>
    )
  }

  // Add a method to render the analyzed HTML directly
  const renderHtmlResponse = () => {
    if (rawResponse && typeof rawResponse === 'string' && rawResponse.includes('<!DOCTYPE html>')) {
      return (
        <div className="mt-4">
          <iframe 
            srcDoc={`
              <!DOCTYPE html>
              <html>
              <head>
                <style>
                  body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: white;
                  }
                  .container {
                    padding: 20px;
                  }
                  img {
                    max-width: 100%;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                  }
                  h1, h2, h3 {
                    color: #2c3e50;
                  }
                  .images-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    justify-content: center;
                    margin-bottom: 30px;
                  }
                  .image-box {
                    max-width: 45%;
                    transition: transform 0.3s ease;
                  }
                  .image-box:hover {
                    transform: scale(1.02);
                  }
                  .detection-box {
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    transition: all 0.3s ease;
                  }
                  .detection-box:hover {
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    border-color: #4299e1;
                  }
                  .detection-header {
                    margin-bottom: 10px;
                  }
                  .style-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                  }
                  .style-item {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 10px;
                    min-width: 150px;
                    transition: all 0.3s ease;
                  }
                  .style-item:hover {
                    background: #edf2f7;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                  }
                  .confidence-bar {
                    height: 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                    margin-top: 5px;
                    overflow: hidden;
                  }
                  .confidence-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #4299e1, #3182ce);
                    border-radius: 4px;
                  }
                  table {
                    width: 100%;
                    border-collapse: collapse;
                  }
                  th, td {
                    border: 1px solid #e0e0e0;
                    padding: 8px 12px;
                    text-align: left;
                  }
                  th {
                    background: #f8f9fa;
                  }
                  a.back-link {
                    display: inline-block;
                    margin-bottom: 20px;
                    color: #4299e1;
                    text-decoration: none;
                    font-weight: 500;
                    transition: color 0.2s;
                  }
                  a.back-link:hover {
                    color: #2b6cb0;
                    text-decoration: underline;
                  }
                </style>
              </head>
              <body>
                <div class="container">
                  ${rawResponse.replace('<!DOCTYPE html>', '').replace(/<html>.*?<body>/s, '').replace(/<\/body>.*?<\/html>/s, '')}
                </div>
              </body>
              </html>
            `}
            title="Analysis Results"
            className="w-full rounded-lg shadow-md border-0"
            style={{height: '750px', borderRadius: '8px'}}
          />
        </div>
      )
    }
    return null
  }

  return (
    <div className="py-8 bg-gradient-to-b from-gray-50 to-white min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">Style Analyzer</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Our AI-powered style analyzer identifies clothing items, classifies style, and extracts feature data
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 md:p-8 overflow-hidden border border-gray-100">
          {/* Tabs */}
          <div className="flex border-b border-gray-200 mb-6">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 font-medium text-sm mr-2 ${
                activeTab === 'upload'
                  ? 'text-secondary border-b-2 border-secondary'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <i className="fas fa-upload mr-2"></i>Upload
            </button>
            {(results || (rawResponse && rawResponse.includes('<!DOCTYPE html>'))) && (
              <button
                onClick={() => setActiveTab('results')}
                className={`px-4 py-2 font-medium text-sm ${
                  activeTab === 'results'
                    ? 'text-secondary border-b-2 border-secondary'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <i className="fas fa-chart-bar mr-2"></i>Results
              </button>
            )}
          </div>

          {/* Loading state with Fashion Facts */}
          {loading && (
            <div className="animate-fadeIn">
              <div className="text-center mb-4">
                <div className="inline-block mx-auto">
                  <div className="animate-bounce-slow">
                    <i className="fas fa-tshirt text-5xl text-indigo-400"></i>
                  </div>
                </div>
                <h3 className="mt-4 text-xl font-medium text-gray-700">Analyzing your fashion...</h3>
                <p className="text-gray-500">Please wait while our AI works its magic</p>
              </div>
              
              <FashionFacts />
              
              <div className="w-full max-w-md mx-auto bg-gray-200 rounded-full h-2.5 mt-6 overflow-hidden">
                <div className="bg-gradient-to-r from-indigo-400 to-purple-500 h-2.5 rounded-full animate-progress"></div>
              </div>
            </div>
          )}

          {!loading && activeTab === 'upload' && (
            <div className="animate-fadeIn">
              <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
                <div className="mb-6">
                  <label htmlFor="imageFile" className="block text-sm font-medium text-gray-700 mb-2">
                    Select a fashion image to analyze:
                  </label>
                  <div className="relative">
                    <input
                      type="file"
                      id="imageFile"
                      onChange={handleFileChange}
                      accept="image/*"
                      className="block w-full px-3 py-3 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-secondary"
                    />
                    <div className="absolute right-2 top-2 text-gray-400">
                      <i className="fas fa-image text-xl"></i>
                    </div>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">
                    Supported formats: JPG, PNG, WebP (Max: 10MB)
                  </p>
                </div>

                {previewUrl && (
                  <div className="mb-6 text-center p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-lg font-medium mb-3 text-gray-700">Image Preview</h3>
                    <div className="relative inline-block group">
                      <img 
                        src={previewUrl} 
                        alt="Preview" 
                        className="max-h-96 rounded-lg shadow-sm transition-all duration-300 group-hover:shadow-md"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-300 rounded-lg"></div>
                    </div>
                  </div>
                )}

                <div className="text-center mt-8">
                  <button
                    type="submit"
                    disabled={loading || !file}
                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
                  >
                    {loading ? (
                      <>
                        <i className="fas fa-circle-notch fa-spin mr-2"></i>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-search mr-2"></i>
                        Analyze Image
                      </>
                    )}
                  </button>
                </div>
              </form>

              {error && (
                <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-md border border-red-200 max-w-2xl mx-auto">
                  <p className="font-medium flex items-center">
                    <i className="fas fa-exclamation-circle mr-2"></i>Error
                  </p>
                  <p>{error}</p>
                </div>
              )}
            </div>
          )}

          {/* Debug panel to show response data */}
          {debugData && activeTab === 'upload' && !loading && (
            <div className="mt-6 mb-6 p-4 bg-gray-100 rounded-lg overflow-auto max-h-60 max-w-2xl mx-auto">
              <h3 className="text-sm font-mono mb-2">Response Data:</h3>
              <pre className="text-xs">{debugData}</pre>
            </div>
          )}

          {/* Results Tab */}
          {!loading && activeTab === 'results' && (
            <div className="animate-fadeIn">
              <div className="flex items-center mb-6">
                <button 
                  onClick={() => setActiveTab('upload')}
                  className="text-secondary hover:text-blue-700 mr-4 flex items-center"
                >
                  <i className="fas fa-arrow-left mr-2"></i>
                  Back to Upload
                </button>
                <h2 className="text-2xl font-bold text-primary">Analysis Results</h2>
              </div>
              
              {/* Render HTML directly */}
              {renderHtmlResponse()}

              {/* JSON-based results display */}
              {results && !rawResponse?.includes("<!DOCTYPE html>") && (
                <div className="mt-8">
                  
                  {/* Result Image */}
                  {results.annotated_image_path && (
                    <div className="mb-8 text-center">
                      <h3 className="text-xl font-medium mb-4 inline-block pb-2 border-b-2 border-secondary text-gray-800">Analysis Visualization</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-all duration-300">
                          <h4 className="text-lg font-medium mb-3 text-gray-700">Original Image</h4>
                          <img 
                            src={previewUrl} 
                            alt="Original" 
                            className="max-h-80 mx-auto rounded-lg"
                          />
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-all duration-300">
                          <h4 className="text-lg font-medium mb-3 text-gray-700">Annotated Image</h4>
                          <img 
                            src={results.annotated_image_path.startsWith('/') ? results.annotated_image_path : `/${results.annotated_image_path}`} 
                            alt="Analysis Result" 
                            className="max-h-80 mx-auto rounded-lg"
                            onError={(e) => {
                              console.error("Failed to load result image:", results.annotated_image_path);
                              e.target.src = 'https://via.placeholder.com/600x400?text=Analysis+Image+Not+Available';
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Detections */}
                    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
                      <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                        <i className="fas fa-tshirt mr-2 text-secondary"></i>
                        Clothing Items
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        {displayDetections(results.detections)}
                      </div>
                    </div>

                    {/* Style Classification */}
                    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
                      <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                        <i className="fas fa-palette mr-2 text-secondary"></i>
                        Style Classification
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        {displayStyles(results.styles)}
                      </div>
                    </div>

                    {/* Feature Extraction */}
                    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
                      <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                        <i className="fas fa-vector-square mr-2 text-secondary"></i>
                        Feature Extraction
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        {displayFeatures(results.detections)}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Analyze