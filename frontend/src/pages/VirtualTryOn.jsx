import React, { useState } from 'react'
import axios from 'axios'
import FashionFacts from '../components/FashionFacts'

function VirtualTryOn() {
  const [modelFile, setModelFile] = useState(null)
  const [garments, setGarments] = useState([{ file: null, preview: '', category: 'auto' }])
  const [modelPreview, setModelPreview] = useState('')
  const [mode, setMode] = useState('quality')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [progressStatus, setProgressStatus] = useState('')
  const [activeStep, setActiveStep] = useState(1)

  const handleModelFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setModelFile(selectedFile)
      setModelPreview(URL.createObjectURL(selectedFile))
      // Move to next step when model is uploaded
      setActiveStep(2)
    }
  }

  const handleGarmentFileChange = (index, e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      const updatedGarments = [...garments]
      updatedGarments[index] = { 
        ...updatedGarments[index], 
        file: selectedFile, 
        preview: URL.createObjectURL(selectedFile) 
      }
      setGarments(updatedGarments)
      
      // Move to step 3 if this is the first garment
      if (activeStep === 2) {
        setActiveStep(3)
      }
    }
  }

  const handleCategoryChange = (index, value) => {
    const updatedGarments = [...garments]
    updatedGarments[index] = { ...updatedGarments[index], category: value }
    setGarments(updatedGarments)
  }

  const addGarment = () => {
    setGarments([...garments, { file: null, preview: '', category: 'auto' }])
  }

  const removeGarment = (index) => {
    if (garments.length > 1) {
      const updatedGarments = [...garments]
      updatedGarments.splice(index, 1)
      setGarments(updatedGarments)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!modelFile) {
      setError('Please select a model image.')
      return
    }

    // Check if at least one garment is selected
    const hasGarment = garments.some(g => g.file !== null)
    if (!hasGarment) {
      setError('Please select at least one garment image.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    setProgressStatus('Starting virtual try-on process...')

    try {
      // We'll process garments one by one and keep track of the latest result
      let latestResult = null
      const validGarments = garments.filter(g => g.file !== null)
      
      for (let i = 0; i < validGarments.length; i++) {
        const garment = validGarments[i]
        
        setProgressStatus(`Processing garment ${i+1} of ${validGarments.length}...`)
        
        const formData = new FormData()
        
        // For the first garment, use the original model image
        if (i === 0) {
          formData.append('model_image', modelFile)
        } else {
          // For subsequent garments, use the result image from the previous step as the model
          // First, we need to fetch the result image as a blob
          const prevResultUrl = latestResult.result_image
          const response = await fetch(prevResultUrl)
          const blob = await response.blob()
          const resultImageFile = new File([blob], 'previous_result.jpg', { type: 'image/jpeg' })
          formData.append('model_image', resultImageFile)
        }
        
        formData.append('garment_image', garment.file)
        formData.append('category', garment.category)
        formData.append('mode', mode)
        
        const apiResponse = await axios.post('/api/tryon', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        console.log(`Garment ${i+1} result:`, apiResponse.data)
        latestResult = apiResponse.data
      }
      
      // Set the final result
      setResult(latestResult)
      setProgressStatus('')
      // Move to results step
      setActiveStep(4)
    } catch (err) {
      console.error('Error processing virtual try-on:', err)
      setError(`Error processing virtual try-on: ${err.message}`)
      setProgressStatus('')
    } finally {
      setLoading(false)
    }
  }

  // Render step indicators
  const renderStepIndicators = () => {
    const steps = [
      { num: 1, label: 'Model' },
      { num: 2, label: 'Garments' },
      { num: 3, label: 'Configure' },
      { num: 4, label: 'Results' }
    ]
    
    return (
      <div className="flex justify-center mb-8">
        {steps.map((step, index) => (
          <div key={step.num} className="flex items-center">
            <div 
              className={`w-10 h-10 rounded-full flex items-center justify-center font-medium text-sm border-2 transition-all duration-300 
                ${activeStep >= step.num 
                  ? 'border-secondary bg-secondary text-white' 
                  : 'border-gray-300 text-gray-500'}`}
            >
              {step.num}
            </div>
            <div className="text-xs text-center mt-2 absolute -bottom-6 w-16" style={{marginLeft: '-10px'}}>
              <span className={activeStep >= step.num ? 'text-secondary font-medium' : 'text-gray-500'}>
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div 
                className={`w-16 h-0.5 mx-1 transition-all duration-300 ${activeStep > step.num ? 'bg-secondary' : 'bg-gray-300'}`}
              ></div>
            )}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="py-8 bg-gradient-to-b from-indigo-50 to-white min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">AI Fitting Room</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience the future of fashion with our AI-powered virtual try-on technology
          </p>
        </div>

        <div className="relative mb-16 mt-12">
          {renderStepIndicators()}
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 md:p-8 border border-gray-100">
          {loading ? (
            <div className="animate-fadeIn">
              <div className="text-center mb-6">
                <div className="inline-block mx-auto">
                  <div className="animate-bounce-slow">
                    <i className="fas fa-magic text-5xl text-indigo-400"></i>
                  </div>
                </div>
                <h3 className="mt-4 text-xl font-medium text-gray-700">Creating your virtual outfit...</h3>
                <p className="text-gray-500">{progressStatus || "Please wait while our AI works its magic"}</p>
              </div>
              
              <FashionFacts />
              
              <div className="w-full max-w-md mx-auto bg-gray-200 rounded-full h-2.5 mt-6 overflow-hidden">
                <div className="bg-gradient-to-r from-indigo-400 to-purple-500 h-2.5 rounded-full animate-progress"></div>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {/* Step 1: Model Upload */}
              <div className={`transition-all duration-500 ${activeStep === 1 ? 'opacity-100' : 'opacity-60'}`}>
                <div className="flex items-center mb-4">
                  <div className="bg-secondary text-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
                    <i className="fas fa-user"></i>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-800">Upload Your Photo</h2>
                </div>
                
                <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 hover:bg-gray-100 transition-all duration-300 mb-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select a full-body photo:
                      </label>
                      <div className="relative">
                        <input
                          type="file"
                          onChange={handleModelFileChange}
                          accept="image/*"
                          className="block w-full px-3 py-3 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-secondary"
                        />
                        <div className="absolute right-2 top-2 text-gray-400">
                          <i className="fas fa-camera text-xl"></i>
                        </div>
                      </div>
                      <p className="mt-2 text-sm text-gray-500">
                        For best results, use a photo with neutral background and good lighting
                      </p>
                      <div className="mt-4">
                        <button 
                          type="button" 
                          onClick={() => modelFile && setActiveStep(2)}
                          disabled={!modelFile}
                          className="px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-all duration-300"
                        >
                          <span>Continue to Garments</span>
                          <i className="fas fa-arrow-right ml-2"></i>
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-center">
                      {modelPreview ? (
                        <div className="text-center">
                          <div className="relative inline-block group">
                            <img 
                              src={modelPreview} 
                              alt="Your Photo" 
                              className="max-h-80 rounded-lg shadow-sm transition-all duration-300 group-hover:shadow-md"
                            />
                            <div className="absolute inset-0 rounded-lg flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300">
                              <button 
                                type="button" 
                                onClick={() => document.querySelector('input[type="file"]').click()}
                                className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all duration-300"
                              >
                                <i className="fas fa-refresh"></i>
                              </button>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center p-8 bg-gray-100 rounded-lg border border-gray-200 w-full">
                          <div className="text-gray-400 mb-3">
                            <i className="fas fa-user-circle text-6xl"></i>
                          </div>
                          <p className="text-gray-500">Your photo will appear here</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 2-3: Garments and Configuration */}
              <div className={`transition-all duration-500 ${activeStep >= 2 && activeStep <= 3 ? 'opacity-100' : (activeStep < 2 ? 'opacity-50 hidden' : 'opacity-60')}`}>
                <div className="flex items-center mb-4">
                  <div className="bg-secondary text-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
                    <i className="fas fa-tshirt"></i>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-800">Select Garments</h2>
                  <div className="ml-auto">
                    <button 
                      type="button" 
                      onClick={addGarment}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-secondary hover:bg-blue-700 focus:outline-none transition-all duration-300"
                    >
                      <i className="fas fa-plus mr-2"></i>
                      Add Garment
                    </button>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-4 bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
                  <i className="fas fa-info-circle mr-2 text-blue-500"></i>
                  Garments will be processed in sequence, with each item tried on over the previous result.
                </p>

                <div className="space-y-6 mb-8">
                  {garments.map((garment, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg bg-white hover:shadow-md transition-all duration-300 group">
                      <div className="flex justify-between items-center mb-4 border-b pb-2">
                        <h4 className="font-medium text-gray-800 flex items-center">
                          <span className="bg-gray-100 text-secondary rounded-full w-6 h-6 inline-flex items-center justify-center mr-2 text-sm">
                            {index + 1}
                          </span>
                          Garment {index + 1}
                        </h4>
                        {garments.length > 1 && (
                          <button 
                            type="button" 
                            onClick={() => removeGarment(index)}
                            className="inline-flex items-center px-2 py-1 border border-transparent text-sm font-medium rounded-md text-red-600 hover:bg-red-50 focus:outline-none transition-all duration-300"
                          >
                            <i className="fas fa-trash-alt text-sm mr-1"></i>
                            Remove
                          </button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Upload Garment Image
                          </label>
                          <div className="relative">
                            <input
                              type="file"
                              onChange={(e) => handleGarmentFileChange(index, e)}
                              accept="image/*"
                              className="block w-full px-3 py-2 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-secondary"
                            />
                            <div className="absolute right-2 top-2 text-gray-400">
                              <i className="fas fa-tshirt text-lg"></i>
                            </div>
                          </div>
                          
                          <div className="mt-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Garment Category
                            </label>
                            <select
                              value={garment.category}
                              onChange={(e) => handleCategoryChange(index, e.target.value)}
                              className="block w-full px-3 py-2 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-secondary"
                            >
                              <option value="auto">Auto-detect</option>
                              <option value="tops">Tops</option>
                              <option value="bottoms">Bottoms</option>
                              <option value="dresses">Dresses</option>
                              <option value="outerwear">Outerwear</option>
                            </select>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-center">
                          {garment.preview ? (
                            <div className="text-center">
                              <div className="relative inline-block group">
                                <img 
                                  src={garment.preview} 
                                  alt="Garment Preview" 
                                  className="max-h-60 rounded-lg shadow-sm group-hover:shadow-md transition-all duration-300"
                                />
                              </div>
                            </div>
                          ) : (
                            <div className="text-center p-8 bg-gray-100 rounded-lg border border-gray-200 w-full">
                              <div className="text-gray-400 mb-3">
                                <i className="fas fa-tshirt text-6xl"></i>
                              </div>
                              <p className="text-gray-500">Garment image will appear here</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className={`transition-all duration-500 mb-8 ${activeStep >= 3 ? 'opacity-100' : 'opacity-60'}`}>
                  <div className="flex items-center mb-4">
                    <div className="bg-secondary text-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
                      <i className="fas fa-sliders-h"></i>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800">Processing Options</h2>
                  </div>
                  
                  <div className="p-6 border border-gray-200 rounded-lg bg-gray-50">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Processing Quality
                        </label>
                        <select
                          value={mode}
                          onChange={(e) => setMode(e.target.value)}
                          className="block w-full px-3 py-2 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-secondary"
                        >
                          <option value="quality">High Quality (Slower)</option>
                          <option value="balanced">Balanced</option>
                          <option value="performance">Fast (Lower Quality)</option>
                        </select>
                      </div>
                      
                      <div className="md:col-span-2">
                        <div className="p-3 bg-white rounded-md shadow-sm h-full">
                          <h4 className="font-medium text-gray-800 mb-2">Quality Guide</h4>
                          <div className="flex items-center space-x-1 text-xs text-gray-500 mb-1">
                            <span>Faster</span>
                            <div className="flex-grow bg-gray-200 h-1 rounded-full overflow-hidden mx-2">
                              <div 
                                className={`h-full bg-gradient-to-r from-red-400 to-green-400`} 
                                style={{ 
                                  width: mode === 'performance' ? '33%' : 
                                         mode === 'balanced' ? '66%' : '100%' 
                                }}
                              ></div>
                            </div>
                            <span>Better</span>
                          </div>
                          <p className="text-xs text-gray-500">
                            {mode === 'quality' && 'Produces the highest quality output with more accurate garment fitting and details. Takes longer to process.'}
                            {mode === 'balanced' && 'Balances quality and speed for most everyday use cases.'}
                            {mode === 'performance' && 'Prioritizes processing speed over quality. Best for quick tests.'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-between">
                  <button
                    type="button"
                    onClick={() => setActiveStep(Math.max(1, activeStep - 1))}
                    className="flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <i className="fas fa-arrow-left mr-2"></i>
                    Back
                  </button>
                  
                  <div>
                    {activeStep === 3 ? (
                      <button
                        type="submit"
                        disabled={loading || !modelFile || !garments.some(g => g.file !== null)}
                        className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
                      >
                        {loading ? (
                          <>
                            <i className="fas fa-circle-notch fa-spin mr-2"></i>
                            Processing...
                          </>
                        ) : (
                          <>
                            <i className="fas fa-magic mr-2"></i>
                            Try On Garments
                          </>
                        )}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          // Only proceed to step 3 if we have a model and at least one garment
                          if (activeStep === 2 && modelFile && garments.some(g => g.file !== null)) {
                            setActiveStep(3)
                          }
                        }}
                        disabled={activeStep === 2 && (!modelFile || !garments.some(g => g.file !== null))}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-secondary hover:bg-blue-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Continue
                        <i className="fas fa-arrow-right ml-2"></i>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </form>
          )}

          {!loading && progressStatus && (
            <div className="mt-6 p-4 bg-blue-50 text-blue-700 rounded-md border border-blue-200 animate-pulse">
              <div className="flex items-center">
                <i className="fas fa-sync-alt fa-spin mr-3 text-blue-500"></i>
                <div>
                  <p className="font-medium">Processing...</p>
                  <p>{progressStatus}</p>
                </div>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-1.5 mt-3">
                <div className="bg-blue-600 h-1.5 rounded-full animate-progress"></div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-md border border-red-200">
              <p className="font-medium flex items-center">
                <i className="fas fa-exclamation-circle mr-2"></i>
                Error
              </p>
              <p>{error}</p>
            </div>
          )}

          {/* Results section */}
          {result && (
            <div className={`mt-8 pt-8 border-t border-gray-200 transition-all duration-500 ${activeStep === 4 ? 'opacity-100' : 'opacity-60'}`}>
              <div className="flex items-center mb-6">
                <div className="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
                  <i className="fas fa-check"></i>
                </div>
                <h2 className="text-2xl font-bold text-gray-800">Virtual Try-On Result</h2>
              </div>
              
              <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="text-center">
                    <h4 className="text-lg font-medium mb-3 text-gray-700">Original Model</h4>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      {modelPreview && (
                        <img 
                          src={modelPreview} 
                          alt="Original Model" 
                          className="max-h-96 mx-auto rounded-lg shadow-sm"
                        />
                      )}
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <h4 className="text-lg font-medium mb-3 text-gray-700">Final Result</h4>
                    <div className="bg-gray-50 p-3 rounded-lg relative group">
                      {result.result_image && (
                        <>
                          <img 
                            src={result.result_image} 
                            alt="Result" 
                            className="max-h-96 mx-auto rounded-lg shadow-sm transition-all duration-300 group-hover:shadow-md"
                            onError={(e) => {
                              console.error("Failed to load result image:", result.result_image);
                              e.target.src = 'https://via.placeholder.com/300x400?text=Result+Image+Not+Available';
                            }}
                          />
                          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                            <a 
                              href={result.result_image} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center shadow-md"
                              title="Open full size image"
                            >
                              <i className="fas fa-external-link-alt"></i>
                            </a>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="mt-8 bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-lg font-medium mb-4 text-gray-700 border-b pb-2">Processing Details</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white p-3 rounded-md shadow-sm">
                      <p className="text-xs text-gray-500 mb-1">Request ID</p>
                      <p className="font-medium text-gray-800 break-all text-sm">{result.request_id}</p>
                    </div>
                    <div className="bg-white p-3 rounded-md shadow-sm">
                      <p className="text-xs text-gray-500 mb-1">Processing Time</p>
                      <p className="font-medium text-gray-800">
                        <span className="text-xl">{result.processing_time.toFixed(1)}</span> seconds
                      </p>
                    </div>
                    <div className="bg-white p-3 rounded-md shadow-sm">
                      <p className="text-xs text-gray-500 mb-1">Timestamp</p>
                      <p className="font-medium text-gray-800 text-sm">{result.timestamp}</p>
                    </div>
                    <div className="bg-white p-3 rounded-md shadow-sm">
                      <p className="text-xs text-gray-500 mb-1">Garments Processed</p>
                      <p className="font-medium text-gray-800">
                        <span className="text-xl">{garments.filter(g => g.file !== null).length}</span> items
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-center">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveStep(1);
                      setModelFile(null);
                      setModelPreview('');
                      setGarments([{ file: null, preview: '', category: 'auto' }]);
                      setResult(null);
                    }}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-secondary hover:bg-blue-700 focus:outline-none transition-all duration-300"
                  >
                    <i className="fas fa-redo mr-2"></i>
                    Try Another Outfit
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VirtualTryOn 