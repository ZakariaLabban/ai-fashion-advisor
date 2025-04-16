import React, { useState, useEffect, useRef } from 'react'
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
  const [showRecoModal, setShowRecoModal] = useState(false)
  const [activeOperation, setActiveOperation] = useState('similarity')
  const [activeItemData, setActiveItemData] = useState(null)
  const [recoLoading, setRecoLoading] = useState(false)
  const [recoResultImage, setRecoResultImage] = useState(null)
  const formRef = useRef(null)
  
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

  // Debug helper to view confidence details
  const debugObject = (obj, label) => {
    if (obj && typeof obj === 'object') {
      console.log(`DEBUG ${label}:`, 
        JSON.stringify({
          confidence: obj.confidence,
          confidenceType: typeof obj.confidence,
          confidenceValue: obj.confidence ? parseFloat(obj.confidence) : null
        })
      )
    }
  }

  // Ensure confidence is numeric
  const parseConfidence = (value) => {
    if (value === undefined || value === null) return 0
    if (typeof value === 'number') return value
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      return isNaN(parsed) ? 0 : parsed
    }
    return 0
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
      setRawResponse(response.data)  // Store entire response for debugging
      
      if (response.data) {
        try {
          // 1. Try JSON
          const jsonData = JSON.parse(response.data)
          setResults(jsonData)
          setDebugData(JSON.stringify(jsonData, null, 2))
        } catch (parseError) {
          // 2. If not JSON, maybe HTML
          if (response.data.includes('<!DOCTYPE html>')) {
            const htmlContainer = document.createElement('div')
            htmlContainer.innerHTML = response.data

            // Extract from HTML
            const detectionItems = htmlContainer.querySelectorAll('.detection-box')
            const styleItems = htmlContainer.querySelectorAll('.style-item')

            const extractedResults = {
              detections: Array.from(detectionItems).map((item, index) => {
                const title = item.querySelector('.detection-header h3').textContent
                const className = title.split(' (')[0]

                let confidence = 0
                const match = title.match(/Confidence: ([\d.]+)/)
                if (match && match[1]) {
                  confidence = parseFloat(match[1]) // e.g. 0.95
                }
                
                const imgSrc = item.querySelector('img').src
                
                // Extract features and color histogram data
                let features = []
                let colorHistogram = []
                
                // Look for features preview
                const featuresPreviewElem = item.querySelector('.features-preview')
                if (featuresPreviewElem) {
                  try {
                    // Handle preview text. Remove any 'undefined' or 'null' text
                    let featuresText = featuresPreviewElem.textContent.trim()
                    
                    // Check if it's not empty before trying to parse
                    if (featuresText && featuresText.length > 0) {
                      // Try to extract numbers - this format is usually like: [0.1234, 0.5678, 0.91011, 0.121314, 0.151617]...
                      featuresText = featuresText.replace('...', '')
                      
                      // Clean up any non-numeric characters except commas, dots, and minus signs
                      const cleanedText = featuresText.replace(/[^\d,.-]/g, '')
                      
                      // Split by comma and convert to numbers
                      const numberStrings = cleanedText.split(',').filter(s => s.trim().length > 0)
                      features = numberStrings.map(s => parseFloat(s)).filter(n => !isNaN(n))
                      
                      console.log(`Extracted ${features.length} feature values for detection #${index}`)
                    }
                  } catch (e) {
                    console.error('Error parsing features:', e)
                  }
                }
                
                // Look for color histogram preview
                const histogramPreviewElem = item.querySelector('.histogram-preview')
                if (histogramPreviewElem) {
                  try {
                    // Handle preview text. Remove any 'undefined' or 'null' text
                    let histogramText = histogramPreviewElem.textContent.trim()
                    
                    // Check if it's not empty before trying to parse
                    if (histogramText && histogramText.length > 0) {
                      // Try to extract numbers - this format is usually like: [0.1234, 0.5678, 0.91011, 0.121314, 0.151617]...
                      histogramText = histogramText.replace('...', '')
                      
                      // Clean up any non-numeric characters except commas, dots, and minus signs
                      const cleanedText = histogramText.replace(/[^\d,.-]/g, '')
                      
                      // Split by comma and convert to numbers
                      const numberStrings = cleanedText.split(',').filter(s => s.trim().length > 0)
                      colorHistogram = numberStrings.map(s => parseFloat(s)).filter(n => !isNaN(n))
                      
                      console.log(`Extracted ${colorHistogram.length} color histogram values for detection #${index}`)
                    }
                  } catch (e) {
                    console.error('Error parsing color histogram:', e)
                  }
                }

                const detection = {
                  class_name: className,
                  confidence,
                  crop_path: imgSrc,
                  bbox: [0, 0, 0, 0], // Placeholder
                  features,
                  color_histogram: colorHistogram
                }
                debugObject(detection, `HTML detection #${index}`)
                return detection
              }),
              styles: Array.from(styleItems).map((item) => {
                const styleName = item.querySelector('.style-name').textContent
                const confidenceText = item.querySelector('.confidence-value').textContent

                // HTML stores style confidences as e.g. "95.0%"
                let confidence = 0
                const numericValue = confidenceText.replace(/[^\d.]/g, '')
                if (numericValue) {
                  confidence = parseFloat(numericValue) / 100
                }

                const style = {
                  style_name: styleName,
                  style_id: 0,
                  confidence
                }
                debugObject(style, `HTML style (${styleName})`)
                return style
              }),
              request_id: response.data.match(/Request ID:<\/strong> ([^<]+)/)?.[1] || '',
              original_image_path: htmlContainer.querySelector('.images-container .image-box:first-child img')?.src || '',
              annotated_image_path: htmlContainer.querySelector('.images-container .image-box:nth-child(2) img')?.src || ''
            }

            // Force numeric
            extractedResults.detections.forEach(d => d.confidence = parseConfidence(d.confidence))
            extractedResults.styles.forEach(s => s.confidence = parseConfidence(s.confidence))

            console.log("FINAL EXTRACTED RESULTS:", JSON.stringify(extractedResults, null, 2))
            setResults(extractedResults)
            setDebugData('HTML response successfully parsed')
            setActiveTab('results')
          } else {
            // Not HTML or JSON
            setError('Unrecognized response format from server')
            setDebugData(response.data)
          }
        }
      } else {
        setError('Empty response from server.')
      }
    } catch (err) {
      console.error('Error analyzing image:', err)
      let errorMessage = `Error analyzing image: ${err.message}`
      let errorDetails = ''

      if (err.response) {
        console.log('Error response:', err.response)
        errorMessage += ` (Status: ${err.response.status})`
        if (err.response.data) {
          if (typeof err.response.data === 'object') {
            const detail = err.response.data.detail || err.response.data.error || JSON.stringify(err.response.data)
            errorDetails = detail
          } else if (typeof err.response.data === 'string') {
            errorDetails = err.response.data
          }
        }
      }

      setError(errorMessage)
      setDebugData(errorDetails || JSON.stringify(err, null, 2))
    } finally {
      setLoading(false)
      if (rawResponse && rawResponse.includes('<!DOCTYPE html>')) {
        setActiveTab('results')
      }
    }
  }

  // Helper to safely display an object property
  const displayProperty = (obj, property, defaultValue = 'N/A') => {
    try {
      if (!obj) return defaultValue
      return obj[property] !== undefined && obj[property] !== null ? obj[property] : defaultValue
    } catch (e) {
      console.error(`Error accessing ${property}:`, e)
      return defaultValue
    }
  }

  //
  // 1) getConfidencePercent -> returns decimal in [0..1]
  //
  const getConfidencePercent = (item) => {
    if (!item) return 0

    let val = 0
    if (typeof item.confidence === 'number') {
      val = item.confidence
    } else if (typeof item.confidence === 'string') {
      const parsed = parseFloat(item.confidence.replace(/[^\d.]/g, ''))
      val = isNaN(parsed) ? 0 : parsed
    } else {
      val = parseFloat(displayProperty(item, 'confidence', 0))
    }

    // If val is e.g. 95, make it 0.95
    const normalized = val > 1 ? val / 100 : val
    console.log(`GET CONFIDENCE: raw:${item.confidence} → normalized: ${normalized}`)
    return normalized
  }

  //
  // 2) formatConfidence -> transforms [0..1] → "XX.X%"
  //
  const formatConfidence = (value) => {
    let c = 0
    if (typeof value === 'number') {
      c = value
    } else {
      // e.g. "0.94" or "94"
      const parsed = parseFloat(value)
      if (!isNaN(parsed)) c = parsed
    }

    // If value is over 1 (like 95), normalize it to decimal (0.95)
    if (c > 1) c = c / 100
    
    // Debug the values
    console.log(`FORMAT CONFIDENCE: Raw input: ${value} (${typeof value}) → Normalized: ${c} → Final: ${(c * 100).toFixed(1)}%`)
    
    // Convert from decimal (0-1) to percentage (0-100) with 1 decimal place
    return (c * 100).toFixed(1) + '%'
  }

  //
  // 3) getWidthStyle -> produce a width for a progress bar
  //
  const getWidthStyle = (confidence) => {
    // Guarantee min 1% width for visibility
    const percent = Math.max(1, confidence * 100)
    return `${percent}%`
  }

  const displayStyles = (styles) => {
    if (!styles || !Array.isArray(styles) || styles.length === 0) {
      return <p className="text-gray-500">No style classification available.</p>
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {styles.map((style, index) => {
          // DIRECT METHOD - same exact approach as displayDetections
          const rawConfidence = parseFloat(style.confidence || 0);
          const formattedConfidence = (rawConfidence * 100).toFixed(1) + '%';
          const confidenceForWidth = Math.max(1, rawConfidence * 100) + '%';
          
          console.log(`STYLE ${index} (${style.style_name}): Raw: ${rawConfidence} → Formatted: ${formattedConfidence}`);
          
          return (
            <div
              key={index}
              className="p-4 bg-white rounded-md shadow-sm mb-2 hover:shadow-md transition-all duration-300 border-l-4 border-secondary"
            >
              <p className="font-medium text-primary">
                {displayProperty(style, 'style_name') || displayProperty(style, 'style')}
              </p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-gradient-to-r from-blue-400 to-secondary h-2.5 rounded-full"
                  style={{ width: confidenceForWidth }}
                />
              </div>
              <p className="text-right text-sm text-gray-500 mt-1">{formattedConfidence}</p>
            </div>
          )
        })}
      </div>
    )
  }

  const displayDetections = (detections) => {
    if (!detections || !Array.isArray(detections) || detections.length === 0) {
      return <p className="text-gray-500">No clothing items detected in the image.</p>
    }

    // EEP logic for recommended classes
    const recoCapable = ["Shirt", "Jumpsuit", "Pants", "Shorts", "Pants/Shorts", "Skirt", "Dress"]
    
    return (
      <div className="space-y-4">
        {detections.map((item, index) => {
          const className = displayProperty(item, 'class_name')
          
          // Simple direct conversion: take the raw confidence and convert to percentage string
          const rawConfidence = parseFloat(item.confidence || 0);
          const formattedConfidence = (rawConfidence * 100).toFixed(1) + '%';
          const confidenceForWidth = Math.max(1, rawConfidence * 100) + '%';
          
          console.log(`DETECTION ${index} (${className}): Raw: ${rawConfidence} → Formatted: ${formattedConfidence}`);

          const isRecoCapable =
            recoCapable.includes(className) ||
            (className && className.includes("Pants")) ||
            (className && className.includes("Shorts"))

          return (
            <div key={index} className="p-4 bg-white rounded-md shadow-sm border hover:shadow-md transition-all duration-300">
              <div className="flex items-start mb-2">
                {item.crop_path && (
                  <div className="mr-3 flex-shrink-0">
                    <img
                      src={item.crop_path}
                      alt={className}
                      className="w-16 h-16 object-cover rounded border border-gray-200"
                    />
                  </div>
                )}
                <div className="flex-grow">
                  <div className="flex items-center">
                    <h4 className="font-medium text-primary">{className}</h4>
                    <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                      {formattedConfidence}
                    </span>
                  </div>
                  <div className="mt-1 relative">
                    <div className="bg-gray-200 rounded-full h-2.5 mb-1">
                      <div
                        className="bg-gradient-to-r from-green-400 to-blue-500 h-2.5 rounded-full"
                        style={{ width: confidenceForWidth }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>0%</span>
                      <span>{formattedConfidence}</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </div>

              {isRecoCapable && (
                <div className="mt-4 flex space-x-2 justify-center">
                  <button
                    onClick={() => openRecoModal(item, index, 'similarity')}
                    className="px-3 py-1.5 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-all flex items-center"
                  >
                    <i className="fas fa-search mr-1" /> Find Similar
                  </button>
                  <button
                    onClick={() => openRecoModal(item, index, 'matching')}
                    className="px-3 py-1.5 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-all flex items-center"
                  >
                    <i className="fas fa-random mr-1" /> Find Matching
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  const displayFeatures = (detections) => {
    if (!detections || !Array.isArray(detections)) {
      return <p className="text-gray-500">No feature extraction data available.</p>
    }

    const detectionsWithFeatures = detections.filter(item => item && item.class_name)

    if (detectionsWithFeatures.length === 0) {
      return <p className="text-gray-500">No feature extraction data available.</p>
    }

    return (
      <div className="space-y-4">
        <p className="text-sm text-primary font-medium mb-2">Feature extraction for {detectionsWithFeatures.length} items</p>
        {detectionsWithFeatures.map((item, index) => {
          const features = Array.isArray(item.features) ? item.features : []
          const colorHistogram = Array.isArray(item.color_histogram) ? item.color_histogram : []

          // Simple direct conversion of confidence
          const rawConfidence = parseFloat(item.confidence || 0);
          const formattedConfidence = (rawConfidence * 100).toFixed(1) + '%';
          const confidenceForWidth = Math.max(1, rawConfidence * 100) + '%';
          
          console.log(`FEATURE ${index} (${item.class_name}): Raw: ${rawConfidence} → Formatted: ${formattedConfidence}`);

          return (
            <div key={index} className="p-4 bg-white rounded-md shadow-sm hover:shadow-md transition-all duration-300">
              <div className="flex items-center justify-between mb-2 border-b pb-2">
                <p className="font-medium text-gray-800">{displayProperty(item, 'class_name')}</p>
                <div className="flex items-center">
                  <div className="w-24 bg-gray-100 rounded-full h-2 mr-2">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: confidenceForWidth }}
                    />
                  </div>
                  <span className="text-xs text-gray-600">{formattedConfidence}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Feature vectors */}
                <div>
                  <div className="text-xs text-gray-700 font-medium mb-1 pb-1 border-b border-gray-100">
                    Feature Vector {features.length ? `(${features.length})` : ''}
                  </div>
                  <p className="text-sm font-mono bg-gray-50 p-2 rounded overflow-x-auto h-20 overflow-y-auto">
                    {features.length > 0
                      ? `[${features.slice(0, 16).map(v => Number(v).toFixed(4)).join(', ')}${features.length > 16 ? ', ...' : ''}]`
                      : 'No feature data'}
                  </p>
                </div>

                {/* Color histogram */}
                <div>
                  <div className="text-xs text-gray-700 font-medium mb-1 pb-1 border-b border-gray-100">
                    Color Histogram {colorHistogram.length ? `(${colorHistogram.length})` : ''}
                  </div>
                  <p className="text-sm font-mono bg-gray-50 p-2 rounded overflow-x-auto h-20 overflow-y-auto">
                    {colorHistogram.length > 0
                      ? `[${colorHistogram.slice(0, 16).map(v => Number(v).toFixed(3)).join(', ')}${colorHistogram.length > 16 ? ', ...' : ''}]`
                      : 'No color data'}
                  </p>
                </div>
              </div>

              {/* Visual color representation */}
              {colorHistogram.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs text-gray-700 font-medium mb-1">Color Distribution</div>
                  <div className="flex h-4 w-full rounded overflow-hidden">
                    {Array.from({ length: Math.min(10, colorHistogram.length) }).map((_, i) => {
                      const hue = (i * 36) % 360
                      const weight = colorHistogram[i] || 0
                      return (
                        <div
                          key={i}
                          className="h-full"
                          style={{
                            backgroundColor: `hsl(${hue}, 80%, 50%)`,
                            width: `${Math.max(5, (weight * 100) || 10)}%`
                          }}
                        />
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  // Extract & render HTML
  const extractAndRenderResults = () => {
    if (!rawResponse || typeof rawResponse !== 'string' || !rawResponse.includes('<!DOCTYPE html>')) {
      return null
    }

    try {
      const htmlContainer = document.createElement('div')
      htmlContainer.innerHTML = rawResponse

      const detectionItems = htmlContainer.querySelectorAll('.detection-box')
      const styleItems = htmlContainer.querySelectorAll('.style-item')

      const requestIdMatch = rawResponse.match(/Request ID:<\/strong> ([^<]+)/)
      const requestId = requestIdMatch ? requestIdMatch[1] : ''
      
      const originalImg = htmlContainer.querySelector('.images-container .image-box:first-child img')?.src || ''
      const annotatedImg = htmlContainer.querySelector('.images-container .image-box:nth-child(2) img')?.src || ''

      // Detections
      const detections = Array.from(detectionItems).map((item, index) => {
        const title = item.querySelector('.detection-header h3')?.textContent || ''
        const className = title.split(' (')[0]
        
        let conf = 0
        const confMatch = title.match(/Confidence: ([\d.]+)/)
        if (confMatch && confMatch[1]) {
          conf = parseFloat(confMatch[1]) // decimal
        }
        const imgSrc = item.querySelector('img')?.src || ''
        
        // Extract features and color histogram data
        let features = []
        let colorHistogram = []
        
        // Look for features preview
        const featuresPreviewElem = item.querySelector('.features-preview')
        if (featuresPreviewElem) {
          try {
            // Handle preview text. Remove any 'undefined' or 'null' text
            let featuresText = featuresPreviewElem.textContent.trim()
            
            // Check if it's not empty before trying to parse
            if (featuresText && featuresText.length > 0) {
              // Try to extract numbers - this format is usually like: [0.1234, 0.5678, 0.91011, 0.121314, 0.151617]...
              featuresText = featuresText.replace('...', '')
              
              // Clean up any non-numeric characters except commas, dots, and minus signs
              const cleanedText = featuresText.replace(/[^\d,.-]/g, '')
              
              // Split by comma and convert to numbers
              const numberStrings = cleanedText.split(',').filter(s => s.trim().length > 0)
              features = numberStrings.map(s => parseFloat(s)).filter(n => !isNaN(n))
              
              console.log(`Extracted ${features.length} feature values for detection #${index}`)
            }
          } catch (e) {
            console.error('Error parsing features:', e)
          }
        }
        
        // Look for color histogram preview
        const histogramPreviewElem = item.querySelector('.histogram-preview')
        if (histogramPreviewElem) {
          try {
            // Handle preview text. Remove any 'undefined' or 'null' text
            let histogramText = histogramPreviewElem.textContent.trim()
            
            // Check if it's not empty before trying to parse
            if (histogramText && histogramText.length > 0) {
              // Try to extract numbers - this format is usually like: [0.1234, 0.5678, 0.91011, 0.121314, 0.151617]...
              histogramText = histogramText.replace('...', '')
              
              // Clean up any non-numeric characters except commas, dots, and minus signs
              const cleanedText = histogramText.replace(/[^\d,.-]/g, '')
              
              // Split by comma and convert to numbers
              const numberStrings = cleanedText.split(',').filter(s => s.trim().length > 0)
              colorHistogram = numberStrings.map(s => parseFloat(s)).filter(n => !isNaN(n))
              
              console.log(`Extracted ${colorHistogram.length} color histogram values for detection #${index}`)
            }
          } catch (e) {
            console.error('Error parsing color histogram:', e)
          }
        }
        
        return {
          class_name: className,
          confidence: conf,
          crop_path: imgSrc,
          bbox: [0, 0, 0, 0],
          features,
          color_histogram: colorHistogram
        }
      })

      // Styles
      const styles = Array.from(styleItems).map((item) => {
        const styleName = item.querySelector('.style-name')?.textContent || ''
        const confText = item.querySelector('.confidence-value')?.textContent || '0%'
        let confVal = 0
        const numeric = confText.replace(/[^\d.]/g, '')
        if (numeric) {
          confVal = parseFloat(numeric) / 100
        }
        return {
          style_name: styleName,
          style_id: 0,
          confidence: confVal
        }
      })

      // Build results object
      const htmlResults = {
        request_id: requestId,
        original_image_path: originalImg,
        annotated_image_path: annotatedImg,
        detections,
        styles
      }

      console.log('EXTRACTED HTML RESULTS:', htmlResults)
      if (!results) setResults(htmlResults)

      // Return a little container of rendered results
      return (
        <div className="mt-8">
          <div className="mb-8 text-center">
            <h3 className="text-xl font-medium mb-4 inline-block pb-2 border-b-2 border-secondary text-gray-800">
              Analysis Visualization
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-all duration-300">
                <h4 className="text-lg font-medium mb-3 text-gray-700">Original Image</h4>
                <img
                  src={originalImg || previewUrl}
                  alt="Original"
                  className="max-h-80 mx-auto rounded-lg"
                />
              </div>
              <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-all duration-300">
                <h4 className="text-lg font-medium mb-3 text-gray-700">Annotated Image</h4>
                <img
                  src={annotatedImg}
                  alt="Analysis Result"
                  className="max-h-80 mx-auto rounded-lg"
                  onError={(e) => {
                    console.error('Failed to load annotated image:', annotatedImg)
                    e.target.src = 'https://via.placeholder.com/600x400?text=Not+Available'
                  }}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Detections */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
              <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                <i className="fas fa-tshirt mr-2 text-secondary" />
                Clothing Items
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg">{displayDetections(detections)}</div>
            </div>

            {/* Style */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
              <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                <i className="fas fa-palette mr-2 text-secondary" />
                Style Classification
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg">{displayStyles(styles)}</div>
            </div>

            {/* Features */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
              <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                <i className="fas fa-vector-square mr-2 text-secondary" />
                Feature Extraction
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg">{displayFeatures(detections)}</div>
            </div>
          </div>
        </div>
      )
    } catch (err) {
      console.error('Error extracting from HTML:', err)
      return (
        <div className="p-4 bg-red-50 text-red-700 rounded-md border border-red-200">
          <p className="font-medium">Error processing HTML results</p>
          <p>Could not parse the results properly. Please try again.</p>
        </div>
      )
    }
  }

  // Open recommendation modal
  const openRecoModal = (item, index, operation) => {
    const className = displayProperty(item, 'class_name')
    let itemType = 'topwear'

    if (className === 'Shirt' || className === 'Jumpsuit' ||
        className === 'T-Shirt' || className === 'Top' ||
        className === 'Blouse' || className === 'Dress') {
      itemType = 'topwear'
    } else if (className === 'Pants' || className === 'Shorts' ||
               className === 'Pants/Shorts' || className === 'Skirt' ||
               className === 'Jeans' || className.includes('Pant') ||
               className.includes('Short')) {
      itemType = 'bottomwear'
    }

    setActiveItemData({ item, index, itemType, className })
    setActiveOperation(operation)
    setShowRecoModal(true)
  }

  // Submit recommendation
  const handleRecoSubmit = async (e) => {
    e.preventDefault()
    if (!results || !activeItemData) return

    setRecoLoading(true)
    setRecoResultImage(null)

    try {
      const formData = new FormData(formRef.current)
      formData.set('request_id', results.request_id)
      formData.set('detection_id', activeItemData.index.toString())
      formData.set('operation', activeOperation)

      // For "matching", we pick the opposite item type
      const originalType = activeItemData.itemType
      if (activeOperation === 'matching') {
        formData.set('item_type', originalType === 'topwear' ? 'bottomwear' : 'topwear')
      } else {
        formData.set('item_type', originalType)
      }

      const response = await fetch('/recommendation', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const blob = await response.blob()
        const imgUrl = URL.createObjectURL(blob)
        setRecoResultImage(imgUrl)
      } else {
        setError(`Error getting recommendations: ${response.statusText}`)
        console.error('Server error:', response.status, response.statusText)
        try {
          const errText = await response.text()
          console.error('Error response body:', errText)
        } catch {}
      }
    } catch (err) {
      console.error('Error getting recommendations:', err)
      setError(`Error: ${err.message}`)
    } finally {
      setRecoLoading(false)
    }
  }

  const downloadRecoResult = () => {
    if (!recoResultImage) return
    
    const a = document.createElement('a')
    a.href = recoResultImage
    a.download = `${activeOperation}-${activeItemData?.className || 'fashion'}-result.jpg`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const toggleRecoType = (operation) => {
    setActiveOperation(operation)
  }

  // Recommendation Modal
  const RecommendationModal = () => {
    if (!showRecoModal || !activeItemData) return null

    const { className, itemType, item } = activeItemData
    const modalTitle =
      activeOperation === 'matching'
        ? `Find Items to Match with ${className}`
        : `Find Similar ${className}s`

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 animate-fadeIn">
        <div className="bg-white rounded-lg w-full max-w-md relative shadow-xl">
          <div className="absolute top-0 right-0">
            <button
              onClick={() => {
                setShowRecoModal(false)
                setRecoResultImage(null)
              }}
              className="m-2 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
              aria-label="Close"
            >
              <i className="fas fa-times" />
            </button>
          </div>

          <div className="p-6 pt-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4 pr-6">{modalTitle}</h3>

            {recoResultImage ? (
              <div className="mb-6">
                <div className="flex justify-center mb-4">
                  <img 
                    src={recoResultImage} 
                    alt="Recommendation Results" 
                    className="max-h-80 rounded-lg border border-gray-200 shadow-sm"
                  />
                </div>
                
                <div className="bg-blue-50 p-3 rounded-lg mb-4 text-center text-blue-800">
                  {activeOperation === 'similarity' ? (
                    <p>
                      <i className="fas fa-info-circle mr-2"></i>
                      {itemType === 'topwear' ? 'This is a similar top that matches your style!' : 'This is a similar bottom that matches your style!'}
                    </p>
                  ) : (
                    <p>
                      <i className="fas fa-info-circle mr-2"></i>
                      {itemType === 'topwear' ? 'This bottom will complement your top perfectly!' : 'This top will complement your bottom perfectly!'}
                    </p>
                  )}
                  
                  <p className="text-sm mt-2 text-blue-600">
                    <i className="fas fa-tshirt mr-1"></i>
                    Download this image and try this item in our virtual fitting room!
                  </p>
                </div>
                
                <div className="flex justify-center space-x-3">
                  <button
                    onClick={downloadRecoResult}
                    className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-md shadow-sm transition-colors flex items-center"
                  >
                    <i className="fas fa-download mr-2"></i>
                    Download Result
                  </button>
                  <button
                    onClick={() => setRecoResultImage(null)}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md shadow-sm transition-colors flex items-center"
                  >
                    <i className="fas fa-arrow-left mr-2"></i>
                    Back to Form
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Item preview */}
                {item.crop_path && (
                  <div className="mb-4 flex justify-center">
                    <div className="relative inline-block">
                      <img
                        src={item.crop_path}
                        alt={className}
                        className="h-32 object-contain rounded border border-gray-200"
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-gray-800 bg-opacity-70 text-white text-xs py-1 px-2 text-center">
                        {className}
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex border rounded-lg mb-6 overflow-hidden bg-gray-50">
                  <button
                    onClick={() => toggleRecoType('similarity')}
                    className={`flex-1 py-2 px-4 flex items-center justify-center font-medium transition-colors duration-300 ${
                      activeOperation === 'similarity'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <i
                      className={`fas fa-search mr-2 ${
                        activeOperation === 'similarity' ? 'text-white' : 'text-blue-500'
                      }`}
                    />
                    Find Similar
                  </button>
                  <button
                    onClick={() => toggleRecoType('matching')}
                    className={`flex-1 py-2 px-4 flex items-center justify-center font-medium transition-colors duration-300 ${
                      activeOperation === 'matching'
                        ? 'bg-red-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <i
                      className={`fas fa-random mr-2 ${
                        activeOperation === 'matching' ? 'text-white' : 'text-red-500'
                      }`}
                    />
                    Find Matching
                  </button>
                </div>

                <form ref={formRef} onSubmit={handleRecoSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender:</label>
                    <select
                      name="gender"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Any</option>
                      <option value="male">Men</option>
                      <option value="female">Women</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Style:</label>
                    <select
                      name="style"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Any</option>
                      <option value="casual">Casual</option>
                      <option value="formal">Formal</option>
                      <option value="athletic wear">Athletic Wear</option>
                      <option value="streetwear">Streetwear</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={recoLoading}
                      className={`w-full py-3 px-4 rounded-md font-medium text-white transition-all flex items-center justify-center ${
                        activeOperation === 'matching'
                          ? 'bg-red-500 hover:bg-red-600 focus:ring-red-400'
                          : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-400'
                      } focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50`}
                    >
                      {recoLoading ? (
                        <>
                          <i className="fas fa-circle-notch fa-spin mr-2" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <i
                            className={`${
                              activeOperation === 'matching' ? 'fas fa-random' : 'fas fa-search'
                            } mr-2`}
                          />
                          {activeOperation === 'matching' ? 'Find Matching Items' : 'Find Similar Items'}
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    )
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
              <i className="fas fa-upload mr-2" />
              Upload
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
                <i className="fas fa-chart-bar mr-2" />
                Results
              </button>
            )}
          </div>

          {/* Loading with FashionFacts */}
          {loading && (
            <div className="animate-fadeIn">
              <div className="text-center mb-4">
                <div className="inline-block mx-auto animate-bounce-slow">
                  <i className="fas fa-tshirt text-5xl text-indigo-400" />
                </div>
                <h3 className="mt-4 text-xl font-medium text-gray-700">Analyzing your fashion...</h3>
                <p className="text-gray-500">Please wait while our AI works its magic</p>
              </div>

              <FashionFacts />

              <div className="w-full max-w-md mx-auto bg-gray-200 rounded-full h-2.5 mt-6 overflow-hidden">
                <div className="bg-gradient-to-r from-indigo-400 to-purple-500 h-2.5 rounded-full animate-progress" />
              </div>
            </div>
          )}

          {/* Upload Tab */}
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
                      <i className="fas fa-image text-xl" />
                    </div>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">Supported formats: JPG, PNG, WebP (Max: 10MB)</p>
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
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-300 rounded-lg" />
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
                        <i className="fas fa-circle-notch fa-spin mr-2" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-search mr-2" />
                        Analyze Image
                      </>
                    )}
                  </button>
                </div>
              </form>

              {error && (
                <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-md border border-red-200 max-w-2xl mx-auto">
                  <p className="font-medium flex items-center">
                    <i className="fas fa-exclamation-circle mr-2" />
                    Error
                  </p>
                  <p>{error}</p>
                </div>
              )}
            </div>
          )}

          {/* Debug panel */}
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
                <button onClick={() => setActiveTab('upload')} className="text-secondary hover:text-blue-700 mr-4 flex items-center">
                  <i className="fas fa-arrow-left mr-2" />
                  Back to Upload
                </button>
                <h2 className="text-2xl font-bold text-primary">Analysis Results</h2>
              </div>

              {extractAndRenderResults()}

              {results && !rawResponse?.includes('<!DOCTYPE html>') && (
                <div className="mt-8">
                  {results.annotated_image_path && (
                    <div className="mb-8 text-center">
                      <h3 className="text-xl font-medium mb-4 inline-block pb-2 border-b-2 border-secondary text-gray-800">
                        Analysis Visualization
                      </h3>
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
                            src={
                              results.annotated_image_path.startsWith('/')
                                ? results.annotated_image_path
                                : `/${results.annotated_image_path}`
                            }
                            alt="Analysis"
                            className="max-h-80 mx-auto rounded-lg"
                            onError={(e) => {
                              console.error('Failed to load annotated image:', results.annotated_image_path)
                              e.target.src = 'https://via.placeholder.com/600x400?text=Not+Available'
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
                        <i className="fas fa-tshirt mr-2 text-secondary" />
                        Clothing Items
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg">{displayDetections(results.detections)}</div>
                    </div>

                    {/* Style */}
                    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
                      <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                        <i className="fas fa-palette mr-2 text-secondary" />
                        Style Classification
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg">{displayStyles(results.styles)}</div>
                    </div>

                    {/* Features */}
                    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
                      <h3 className="text-xl font-medium mb-4 flex items-center text-gray-800">
                        <i className="fas fa-vector-square mr-2 text-secondary" />
                        Feature Extraction
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg">{displayFeatures(results.detections)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <RecommendationModal />
    </div>
  )
}

export default Analyze
