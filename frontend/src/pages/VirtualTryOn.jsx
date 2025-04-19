import React, { useState, useEffect } from 'react'
import axios from 'axios'
import FashionFacts from '../components/FashionFacts'

// Fashion Tips Component for Virtual Try-On
function FashionTryOnTips() {
  const tips = [
    "For best results, use a full-body photo with a neutral background",
    "Make sure your photo contains only one person (yourself) for the system to work properly",
    "Stand straight facing the camera for the most accurate try-on experience",
    "Wear form-fitting clothes in your model photo for better garment alignment",
    "Make sure the lighting is even and your entire body is visible",
    "Try multiple garments in sequence to build a complete outfit",
    "The higher the image resolution, the better the results will be",
    "Solid color garments typically work better than complex patterns",
  ]

  const [currentTip, setCurrentTip] = useState(0)
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTip((prev) => (prev + 1) % tips.length)
    }, 6000)
    
    return () => clearInterval(timer)
  }, [])
  
  return (
    <div className="bg-gradient-to-r from-secondary-50 to-primary-50 p-4 rounded-xl shadow-sm border border-secondary-100 mb-6">
      <div className="flex items-start">
        <div className="text-secondary-500 mr-4 text-2xl mt-1">
          <i className="fas fa-lightbulb"></i>
        </div>
        <div>
          <h3 className="font-medium text-secondary-700 mb-1">Pro Tip:</h3>
          <p className="text-gray-600 transition-all duration-700 ease-in-out">
            {tips[currentTip]}
          </p>
          <div className="flex space-x-1 mt-2">
            {tips.map((_, index) => (
              <button 
                key={index} 
                className={`w-2 h-2 rounded-full transition-all ${currentTip === index ? 'bg-secondary-500 w-4' : 'bg-gray-300'}`}
                onClick={() => setCurrentTip(index)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Animated Clothing Icons Component
function AnimatedFashionIcons() {
  const icons = [
    { icon: 'tshirt', color: 'text-secondary-400', size: 'text-3xl', position: { top: '10%', left: '5%' }, delay: '0s' },
    { icon: 'socks', color: 'text-primary-400', size: 'text-2xl', position: { top: '25%', right: '10%' }, delay: '0.5s' },
    { icon: 'hat-cowboy', color: 'text-accent-400', size: 'text-2xl', position: { bottom: '15%', left: '15%' }, delay: '1s' },
    { icon: 'vest', color: 'text-secondary-500', size: 'text-3xl', position: { top: '40%', right: '20%' }, delay: '1.5s' },
    { icon: 'shirt', color: 'text-primary-500', size: 'text-2xl', position: { bottom: '30%', right: '15%' }, delay: '2s' },
    { icon: 'shoe-prints', color: 'text-accent-500', size: 'text-xl', position: { bottom: '10%', right: '25%' }, delay: '2.5s' },
  ]
  
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20">
      {icons.map((item, index) => (
        <div 
          key={index} 
          className={`absolute ${item.color} ${item.size} animate-float`}
          style={{ 
            top: item.position.top || 'auto', 
            left: item.position.left || 'auto',
            right: item.position.right || 'auto',
            bottom: item.position.bottom || 'auto',
            animationDelay: item.delay
          }}
        >
          <i className={`fas fa-${item.icon}`}></i>
        </div>
      ))}
    </div>
  )
}

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
  const [showTips, setShowTips] = useState(true)

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
      
      // Handle specific error cases related to person detection
      if (err.response && err.response.status === 400) {
        const errorMessage = err.response.data.detail || err.response.data.message || err.message
        
        // More user-friendly error messages based on the error content
        if (errorMessage.includes("social person") || errorMessage.includes("need a picture of you alone")) {
          setError("We detected multiple people in your photo. For the best try-on experience, please upload a photo with just you in it.")
        } else if (errorMessage.includes("couldn't detect anyone") || errorMessage.includes("provide a clear photo")) {
          setError("We couldn't detect a person in your photo. Please upload a clear, full-body photo of yourself.")
        } else {
          setError(`${errorMessage}`)
        }
      } else if (err.response && err.response.status === 500) {
        // Extract the specific error message from the server response for 500 errors
        const serverErrorMessage = err.response.data.detail || err.response.data.message || err.response.data.error || "Unknown server error"
        setError(`Server error: ${serverErrorMessage}`)
      } else {
        setError(`Error processing virtual try-on: ${err.message}`)
      }
      
      setProgressStatus('')
    } finally {
      setLoading(false)
    }
  }

  // Render step indicators with animations
  const renderStepIndicators = () => {
    const steps = [
      { num: 1, label: 'Upload Model', icon: 'user' },
      { num: 2, label: 'Select Garments', icon: 'tshirt' },
      { num: 3, label: 'Configure', icon: 'sliders-h' },
      { num: 4, label: 'View Results', icon: 'magic' }
    ]
    
    return (
      <div className="flex flex-wrap justify-center mb-12 relative">
        {/* Progress bar connecting the steps */}
        <div className="absolute top-1/2 left-0 w-full h-1 bg-gray-200 -translate-y-1/2 z-0"></div>
        <div 
          className="absolute top-1/2 left-0 h-1 bg-gradient-to-r from-secondary-500 to-primary-500 -translate-y-1/2 z-0 transition-all duration-500"
          style={{ width: `${(activeStep - 1) * 33.33}%` }}
        ></div>
        
        {steps.map((step, index) => (
          <div key={step.num} className="flex flex-col items-center relative z-10 px-4 md:px-8 lg:px-12">
            <div 
              className={`w-14 h-14 rounded-full flex items-center justify-center font-medium border-2 transition-all duration-500
                ${activeStep >= step.num 
                  ? 'bg-gradient-to-r from-secondary-500 to-primary-500 text-white border-white shadow-lg' 
                  : 'bg-white text-gray-400 border-gray-200'}`}
              onClick={() => {
                // Allow navigating to previous steps or current step
                if (step.num <= activeStep) {
                  setActiveStep(step.num)
                }
              }}
              style={{
                cursor: step.num <= activeStep ? 'pointer' : 'default',
                transform: activeStep === step.num ? 'scale(1.1)' : 'scale(1)'
              }}
            >
              <i className={`fas fa-${step.icon} ${activeStep === step.num ? 'animate-pulse' : ''}`}></i>
            </div>
            <div className="text-center mt-3">
              <span className={`font-medium transition-all duration-300 ${activeStep >= step.num ? 'text-secondary-700' : 'text-gray-400'}`}>
                {step.label}
              </span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white py-12 relative">
      {/* Background texture */}
      <div className="absolute inset-0 bg-texture-fabric opacity-10"></div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600 mb-2">
            Virtual Fitting Room
          </h1>
          <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
            Experience AI-powered virtual try-on technology. Upload a model photo and garments to create a virtual outfit.
          </p>
          
          <div className="mt-6 flex justify-center">
            <button 
              onClick={() => setShowTips(!showTips)} 
              className="text-secondary-500 hover:text-secondary-700 transition-colors flex items-center text-sm"
            >
              <i className={`fas fa-${showTips ? 'eye-slash' : 'lightbulb'} mr-2`}></i>
              {showTips ? 'Hide tips' : 'Show tips'}
            </button>
          </div>
          
          {showTips && <FashionTryOnTips />}
        </div>

        <div className="relative mb-16 mt-12">
          {renderStepIndicators()}
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 md:p-8 border border-gray-100 relative overflow-hidden">
          <AnimatedFashionIcons />
          
          {loading ? (
            <div className="animate-fadeIn">
              <div className="text-center mb-10">
                <div className="relative inline-block w-40 h-40">
                  <div className="absolute inset-0 rounded-full border-4 border-gray-200 opacity-25"></div>
                  <div className="absolute inset-0 rounded-full border-t-4 border-r-4 border-secondary-500 animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="relative">
                      <i className="fas fa-magic text-5xl text-secondary-500 animate-pulse"></i>
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent-400 rounded-full animate-ping"></div>
                  </div>
                </div>
                </div>
                <h3 className="mt-6 text-2xl font-medium text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-primary-600">
                  Creating your virtual outfit...
                </h3>
                <p className="text-gray-500 text-lg mt-1">
                  {progressStatus || "Please wait while our AI works its magic"}
                </p>
                <div className="max-w-lg mx-auto mt-8 bg-gray-50 rounded-lg p-4 border border-gray-100">
                  <div className="flex items-center mb-2">
                    <div className="w-8 h-8 rounded-full bg-secondary-100 flex items-center justify-center mr-3">
                      <i className="fas fa-info-circle text-secondary-500"></i>
                    </div>
                    <p className="text-gray-600 font-medium">Processing Details</p>
                  </div>
                  <ul className="space-y-2 text-sm text-gray-500">
                    <li className="flex items-center">
                      <i className="fas fa-check-circle text-green-500 mr-2"></i>
                      Analyzing model image
                    </li>
                    <li className="flex items-center">
                      <i className={`${progressStatus.includes('Processing garment') ? 'fas fa-spinner fa-spin text-secondary-500' : 'fas fa-circle text-gray-300'} mr-2`}></i>
                      Extracting garment features
                      {progressStatus.includes('Processing garment') && (
                        <span className="ml-2 text-xs bg-secondary-100 text-secondary-700 px-2 py-0.5 rounded-full">
                          In progress
                        </span>
                      )}
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-circle text-gray-300 mr-2"></i>
                      Generating virtual fit
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-circle text-gray-300 mr-2"></i>
                      Finalizing results
                    </li>
                  </ul>
                </div>
              </div>
              
              <FashionFacts />
              
              <div className="w-full max-w-lg mx-auto mt-10">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-secondary-400 via-primary-500 to-secondary-500 animate-gradient-x animate-progress"></div>
                </div>
                <div className="flex justify-between mt-2 text-xs text-gray-400">
                  <span>Garment processing</span>
                  <span>Image generation</span>
                  <span>Finalization</span>
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {/* Step 1: Model Upload */}
              <div className={`transition-all duration-500 ${activeStep === 1 ? 'animate-fadeIn opacity-100' : 'opacity-60'}`}>
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-secondary-500 to-primary-500 text-white flex items-center justify-center mr-4 shadow-md">
                    <i className="fas fa-user"></i>
                  </div>
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-primary-600">
                    Upload Your Photo
                  </h2>
                </div>
                
                <div className="p-8 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-white hover:border-secondary-300 transition-all duration-300 mb-8 group">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                        <label className="block text-lg font-medium text-gray-700 mb-3 flex items-center">
                          <i className="fas fa-camera text-secondary-500 mr-2"></i>
                        Select a full-body photo:
                      </label>
                        <div className="relative group">
                          {!modelFile ? (
                            <>
                              <div className="flex flex-col items-center justify-center py-6 border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 hover:bg-white hover:border-secondary-200 transition-all duration-300 cursor-pointer">
                                <div className="text-secondary-500 mb-4">
                                  <i className="fas fa-user-circle text-6xl"></i>
                                </div>
                                <p className="text-gray-700 font-medium mb-2">Drag and drop your photo here</p>
                                <p className="text-gray-500 text-sm mb-4">or</p>
                                <label htmlFor="modelFile" className="px-4 py-2 bg-secondary-500 text-white rounded-lg hover:bg-secondary-600 transition-colors cursor-pointer flex items-center">
                                  <i className="fas fa-upload mr-2"></i>
                                  Browse files
                                </label>
                                <input
                                  id="modelFile"
                                  type="file"
                                  accept="image/*"
                                  className="hidden"
                                  onChange={handleModelFileChange}
                                />
                              </div>
                              <div className="mt-4 text-xs text-secondary-600 bg-secondary-50 p-2 rounded-md flex items-start border border-secondary-100">
                                <i className="fas fa-info-circle mr-2 mt-0.5 text-secondary-500"></i>
                                <div>
                                  <p className="font-medium">Important:</p>
                                  <p>Please upload a photo with only one person (yourself) for the best results. Photos with multiple people or no visible person will be rejected.</p>
                                </div>
                              </div>
                            </>
                          ) : (
                            <div className="relative">
                              <div className="flex justify-between items-center mb-3">
                                <span className="text-sm text-secondary-600 font-medium flex items-center">
                                  <i className="fas fa-check-circle mr-1"></i>
                                  Photo selected
                                </span>
                                <button 
                                  type="button" 
                                  onClick={() => {
                                    setModelFile(null);
                                    setModelPreview('');
                                  }}
                                  className="text-red-500 hover:text-red-700 transition-colors text-sm"
                                >
                                  <i className="fas fa-times mr-1"></i>
                                  Remove
                                </button>
                              </div>
                              <img 
                                src={modelPreview} 
                                alt="Selected model" 
                                className="max-h-80 rounded-lg mx-auto shadow-sm"
                              />
                            </div>
                          )}
                        </div>
                        
                      <div className="mt-4">
                          <p className="text-sm text-gray-500">
                            For best results:
                          </p>
                          <ul className="mt-2 space-y-1 text-sm text-gray-500">
                            <li className="flex items-start">
                              <i className="fas fa-check-circle text-green-500 mr-2 mt-0.5"></i>
                              <span>Upload a photo with <strong>only yourself</strong> in the frame</span>
                            </li>
                            <li className="flex items-start">
                              <i className="fas fa-check-circle text-green-500 mr-2 mt-0.5"></i>
                              Use a photo with a neutral background
                            </li>
                            <li className="flex items-start">
                              <i className="fas fa-check-circle text-green-500 mr-2 mt-0.5"></i>
                              Stand straight, facing the camera
                            </li>
                            <li className="flex items-start">
                              <i className="fas fa-check-circle text-green-500 mr-2 mt-0.5"></i>
                              Ensure good lighting and visibility
                            </li>
                          </ul>
                        </div>
                      </div>
                      
                      <div className="flex justify-center">
                        <button 
                          type="button" 
                          onClick={() => modelFile && setActiveStep(2)}
                          disabled={!modelFile}
                          className="px-6 py-3 bg-gradient-to-r from-secondary-500 to-primary-500 text-white rounded-full shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-all duration-300 hover:-translate-y-1 transform"
                        >
                          <span>Continue to Garments</span>
                          <i className="fas fa-arrow-right ml-2"></i>
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-center">
                      {modelPreview ? (
                        <div className="text-center">
                          <div className="relative inline-block group overflow-hidden rounded-lg shadow-md">
                            <img 
                              src={modelPreview} 
                              alt="Your Photo" 
                              className="max-h-96 rounded-lg transition-all duration-500 group-hover:scale-105"
                            />
                            <div className="absolute inset-0 rounded-lg flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300">
                              <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-4 group-hover:translate-y-0">
                              <button 
                                type="button" 
                                  onClick={() => document.querySelector('#modelFile').click()}
                                  className="bg-white text-gray-800 rounded-full w-12 h-12 flex items-center justify-center shadow-lg hover:bg-gray-100 transition-all duration-300 mx-2"
                              >
                                  <i className="fas fa-exchange-alt"></i>
                              </button>
                            </div>
                          </div>
                          </div>
                          <p className="text-sm text-gray-500 mt-3">Click on the image to change it</p>
                        </div>
                      ) : (
                        <div className="text-center p-12 bg-white rounded-xl border border-gray-200 w-full h-full shadow-inner flex flex-col items-center justify-center">
                          <div className="bg-gray-100 w-32 h-32 rounded-full flex items-center justify-center mb-4">
                            <i className="fas fa-user-circle text-gray-300 text-6xl"></i>
                          </div>
                          <p className="text-gray-400 text-lg">Your photo will appear here</p>
                          <p className="text-gray-300 text-sm mt-2">Upload a photo to get started</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 2-3: Garments and Configuration */}
              <div className={`transition-all duration-500 ${activeStep >= 2 && activeStep <= 3 ? 'animate-fadeIn opacity-100' : (activeStep < 2 ? 'hidden' : 'opacity-60')}`}>
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-secondary-500 to-primary-500 text-white flex items-center justify-center mr-4 shadow-md">
                    <i className="fas fa-tshirt"></i>
                  </div>
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-primary-600">
                    Select Garments
                  </h2>
                  <div className="ml-auto">
                    <button 
                      type="button" 
                      onClick={addGarment}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-full shadow-md text-white bg-gradient-to-r from-secondary-500 to-primary-500 hover:from-secondary-600 hover:to-primary-600 focus:outline-none transition-all duration-300 hover:-translate-y-1 transform"
                    >
                      <i className="fas fa-plus mr-2"></i>
                      Add Garment
                    </button>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border-l-4 border-blue-400 shadow-sm mb-8">
                  <div className="flex items-start">
                    <div className="text-blue-500 mr-3 mt-1">
                      <i className="fas fa-info-circle text-xl"></i>
                    </div>
                    <div>
                      <p className="text-blue-800 font-medium">Processing Order</p>
                      <p className="text-blue-600 text-sm mt-1">
                  Garments will be processed in sequence, with each item tried on over the previous result.
                        This lets you build a complete outfit piece by piece.
                </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-8 mb-10">
                  {garments.map((garment, index) => (
                    <div key={index} className="p-6 border border-gray-200 rounded-xl bg-white hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 group">
                      <div className="flex justify-between items-center mb-5 pb-3 border-b border-gray-100">
                        <h4 className="font-medium text-gray-800 flex items-center text-lg">
                          <div className="w-8 h-8 rounded-full bg-secondary-100 text-secondary-500 flex items-center justify-center mr-3 text-sm">
                            {index + 1}
                          </div>
                          Garment {index + 1}
                        </h4>
                        {garments.length > 1 && (
                          <button 
                            type="button" 
                            onClick={() => removeGarment(index)}
                            className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-full text-red-600 hover:bg-red-50 focus:outline-none transition-colors duration-300"
                          >
                            <i className="fas fa-trash-alt text-sm mr-2"></i>
                            Remove
                          </button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                          <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                              <i className="fas fa-tshirt text-secondary-500 mr-2"></i>
                            Upload Garment Image
                          </label>
                          <div className="relative">
                              {!garment.file ? (
                                <div className="flex flex-col items-center justify-center py-8 border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 hover:bg-white hover:border-secondary-200 transition-all duration-300 cursor-pointer">
                                  <div className="text-secondary-400 mb-3">
                                    <i className="fas fa-tshirt text-4xl"></i>
                                  </div>
                                  <p className="text-gray-600 font-medium mb-1">Drag and drop a garment image</p>
                                  <p className="text-gray-500 text-sm mb-3">or</p>
                                  <label htmlFor={`garmentFile-${index}`} className="px-3 py-1.5 bg-secondary-500 text-white rounded-lg hover:bg-secondary-600 transition-colors cursor-pointer text-sm flex items-center">
                                    <i className="fas fa-image mr-2"></i>
                                    Browse files
                                  </label>
                            <input
                                    id={`garmentFile-${index}`}
                              type="file"
                              onChange={(e) => handleGarmentFileChange(index, e)}
                              accept="image/*"
                                    className="hidden"
                                  />
                                </div>
                              ) : (
                                <div className="flex justify-between items-center p-3 border border-secondary-200 rounded-lg bg-secondary-50">
                                  <div className="flex items-center">
                                    <i className="fas fa-file-image text-secondary-400 mr-2"></i>
                                    <span className="text-gray-700 text-sm truncate max-w-[150px]">{garment.file.name}</span>
                                  </div>
                                  <div className="flex items-center">
                                    <button 
                                      type="button"
                                      onClick={() => document.querySelector(`#garmentFile-${index}`).click()}
                                      className="text-xs px-2 py-1 bg-white text-secondary-500 rounded border border-secondary-200 hover:bg-secondary-50 transition-colors mr-2"
                                    >
                                      Change
                                    </button>
                                    <button 
                                      type="button"
                                      onClick={() => {
                                        const updatedGarments = [...garments];
                                        updatedGarments[index] = { ...updatedGarments[index], file: null, preview: '' };
                                        setGarments(updatedGarments);
                                      }}
                                      className="text-xs px-2 py-1 bg-white text-red-500 rounded border border-red-200 hover:bg-red-50 transition-colors"
                                    >
                                      Remove
                                    </button>
                                    <input
                                      id={`garmentFile-${index}`}
                                      type="file"
                                      onChange={(e) => handleGarmentFileChange(index, e)}
                                      accept="image/*"
                                      className="hidden"
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                              <i className="fas fa-tag text-secondary-500 mr-2"></i>
                              Garment Category
                            </label>
                            <select
                              value={garment.category}
                              onChange={(e) => handleCategoryChange(index, e.target.value)}
                              className="block w-full px-3 py-2 text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 bg-white transition-colors duration-200"
                            >
                              <option value="auto">Auto-detect</option>
                              <option value="tops">Tops</option>
                              <option value="bottoms">Bottoms</option>
                              <option value="dresses">Dresses</option>
                              <option value="outerwear">Outerwear</option>
                            </select>
                            
                            <div className="mt-3 text-sm text-gray-500">
                              <p className="flex items-center">
                                <i className="fas fa-lightbulb text-yellow-400 mr-2"></i>
                                {garment.category === 'auto' 
                                  ? 'Our AI will try to detect the garment type automatically.' 
                                  : `You've selected ${garment.category} for more accurate try-on.`}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-center">
                          {garment.preview ? (
                            <div className="text-center">
                              <div className="relative inline-block group overflow-hidden rounded-lg shadow-md">
                                <img 
                                  src={garment.preview} 
                                  alt="Garment Preview" 
                                  className="max-h-60 rounded-lg transition-all duration-500 group-hover:scale-105"
                                />
                                <div className="absolute inset-0 rounded-lg flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300">
                                  <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-4 group-hover:translate-y-0">
                                    <button 
                                      type="button" 
                                      onClick={() => document.querySelector(`#garmentFile-${index}`).click()}
                                      className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center shadow-lg hover:bg-gray-100 transition-all duration-300 mx-1"
                                    >
                                      <i className="fas fa-exchange-alt"></i>
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-center p-8 bg-white rounded-xl border border-gray-200 w-full shadow-inner">
                              <div className="text-gray-300 mb-3">
                                <i className="fas fa-tshirt text-6xl"></i>
                              </div>
                              <p className="text-gray-400">Garment image will appear here</p>
                              <p className="text-gray-300 text-sm mt-1">Upload an image to see preview</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className={`transition-all duration-500 mb-8 ${activeStep >= 3 ? 'animate-fadeIn opacity-100' : 'opacity-60'}`}>
                  <div className="flex items-center mb-6">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-secondary-500 to-primary-500 text-white flex items-center justify-center mr-4 shadow-md">
                      <i className="fas fa-sliders-h"></i>
                    </div>
                    <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-primary-600">
                      Processing Options
                    </h2>
                  </div>
                  
                  <div className="p-8 border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-all duration-300">
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                      <div>
                        <label className="block text-base font-medium text-gray-700 mb-3">
                          Processing Quality
                        </label>
                        <div className="space-y-3">
                          <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                            <input
                              type="radio"
                              value="quality"
                              checked={mode === 'quality'}
                          onChange={(e) => setMode(e.target.value)}
                              className="mr-3 h-4 w-4 text-secondary-500 focus:ring-secondary-400"
                            />
                            <div>
                              <p className="font-medium text-gray-800">High Quality</p>
                              <p className="text-xs text-gray-500">Best results, slower processing</p>
                            </div>
                          </label>
                          
                          <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                            <input
                              type="radio"
                              value="balanced"
                              checked={mode === 'balanced'}
                              onChange={(e) => setMode(e.target.value)}
                              className="mr-3 h-4 w-4 text-secondary-500 focus:ring-secondary-400"
                            />
                            <div>
                              <p className="font-medium text-gray-800">Balanced</p>
                              <p className="text-xs text-gray-500">Good quality with reasonable speed</p>
                            </div>
                          </label>
                          
                          <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                            <input
                              type="radio"
                              value="performance"
                              checked={mode === 'performance'}
                              onChange={(e) => setMode(e.target.value)}
                              className="mr-3 h-4 w-4 text-secondary-500 focus:ring-secondary-400"
                            />
                            <div>
                              <p className="font-medium text-gray-800">Fast</p>
                              <p className="text-xs text-gray-500">Quick results, lower quality</p>
                            </div>
                          </label>
                        </div>
                      </div>
                      
                      <div className="md:col-span-2">
                        <div className="bg-gradient-to-br from-gray-50 to-white rounded-xl shadow-sm p-6 h-full border border-gray-100">
                          <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                            <i className="fas fa-chart-line text-secondary-500 mr-2"></i>
                            Quality Guide
                          </h4>
                          
                          <div className="mb-6">
                            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                              <span>Faster Processing</span>
                              <span>Higher Quality</span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-400 transition-all duration-500`} 
                                style={{ 
                                  width: mode === 'performance' ? '33%' : 
                                         mode === 'balanced' ? '66%' : '100%' 
                                }}
                              ></div>
                            </div>
                          </div>
                          
                          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
                            <h5 className="font-medium text-gray-700 mb-2">{mode === 'quality' ? 'High Quality Mode' : mode === 'balanced' ? 'Balanced Mode' : 'Fast Mode'}</h5>
                            <p className="text-sm text-gray-600">
                              {mode === 'quality' && 'Produces the highest quality output with more accurate garment fitting and details. The AI model runs at maximum precision for the best possible results, but takes longer to process.'}
                              {mode === 'balanced' && 'Balances quality and speed for most everyday use cases. This option provides good results in a reasonable amount of time and is suitable for most garments and body types.'}
                              {mode === 'performance' && 'Prioritizes processing speed over quality. Best for quick tests or when you need immediate results. May have reduced accuracy with complex garments or poses.'}
                            </p>
                            
                            <div className="mt-3 flex items-center">
                              <div className="flex items-center mr-4">
                                <i className="fas fa-clock text-yellow-500 mr-1"></i>
                                <span className="text-xs font-medium text-gray-700">
                                  {mode === 'quality' ? 'Slower' : mode === 'balanced' ? 'Medium' : 'Fast'}
                                </span>
                              </div>
                              <div className="flex items-center">
                                <i className="fas fa-star text-yellow-500 mr-1"></i>
                                <span className="text-xs font-medium text-gray-700">
                                  {mode === 'quality' ? 'Excellent Result' : mode === 'balanced' ? 'Good Result' : 'Basic Result'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-between">
                  <button
                    type="button"
                    onClick={() => setActiveStep(Math.max(1, activeStep - 1))}
                    className="px-5 py-2.5 border border-gray-300 text-gray-700 bg-white rounded-full hover:bg-gray-50 transition-colors flex items-center shadow-sm"
                  >
                    <i className="fas fa-arrow-left mr-2"></i>
                    Back
                  </button>
                  
                  <div>
                    {activeStep === 3 ? (
                      <button
                        type="submit"
                        disabled={loading || !modelFile || !garments.some(g => g.file !== null)}
                        className="inline-flex items-center px-6 py-3 border border-transparent text-lg font-medium rounded-full shadow-lg text-white bg-gradient-to-r from-secondary-500 to-primary-500 hover:from-secondary-600 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:-translate-y-1"
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
                        className="inline-flex items-center px-5 py-2.5 border border-transparent text-base font-medium rounded-full shadow-md text-white bg-gradient-to-r from-secondary-500 to-primary-500 hover:from-secondary-600 hover:to-primary-600 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:-translate-y-1"
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
            <div className="mt-6 p-6 bg-gradient-to-r from-secondary-50 to-primary-50 text-gray-700 rounded-lg border border-secondary-100 animate-pulse">
              <div className="flex items-start">
                <div className="text-secondary-500 text-xl mr-4 mt-1">
                  <i className="fas fa-sync-alt fa-spin"></i>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-secondary-800">Processing Your Virtual Try-On</p>
                  <p className="text-gray-600 mt-1">{progressStatus}</p>
                  <div className="w-full bg-white rounded-full h-2 mt-4 overflow-hidden shadow-inner">
                    <div className="bg-gradient-to-r from-secondary-400 to-primary-500 h-2 rounded-full animate-progress"></div>
              </div>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 p-6 bg-red-50 text-red-700 rounded-lg border-l-4 border-red-500 animate-fadeIn">
              <div className="flex items-start">
                <div className="text-red-500 text-2xl mr-4 mt-1">
                  {error.includes("multiple people") ? (
                    <i className="fas fa-users"></i>
                  ) : error.includes("couldn't detect a person") ? (
                    <i className="fas fa-user-slash"></i>
                  ) : (
                    <i className="fas fa-exclamation-circle"></i>
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-lg">
                    {error.includes("multiple people") ? "Multiple People Detected" : 
                     error.includes("couldn't detect a person") ? "No Person Detected" : 
                     "Something went wrong"}
                  </p>
                  <p className="mt-2 text-red-600">{error}</p>
                  {(error.includes("multiple people") || error.includes("couldn't detect a person")) && (
                    <div className="mt-3 p-3 bg-white rounded-md text-gray-700 text-sm border border-red-200">
                      <p className="font-medium mb-2">Tips for better results:</p>
                      <ul className="list-disc pl-5 space-y-1">
                        {error.includes("multiple people") && (
                          <>
                            <li>Use a photo with only yourself in the frame</li>
                            <li>Crop out other people from your photo before uploading</li>
                            <li>Take a new selfie in a location where you're alone</li>
                          </>
                        )}
                        {error.includes("couldn't detect a person") && (
                          <>
                            <li>Use a well-lit photo that clearly shows your full body</li>
                            <li>Ensure there's good contrast between you and the background</li>
                            <li>Make sure your photo is not too small or blurry</li>
                          </>
                        )}
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

          {/* Results section */}
          {result && (
            <div className={`mt-8 pt-8 border-t border-gray-200 transition-all duration-500 ${activeStep === 4 ? 'animate-fadeIn opacity-100' : 'opacity-60'}`}>
              <div className="flex items-center mb-8">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-green-400 to-green-500 text-white flex items-center justify-center mr-4 shadow-lg">
                  <i className="fas fa-check text-xl"></i>
                </div>
                <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-secondary-700 to-primary-700">Virtual Try-On Result</h2>
                
                <button
                  onClick={() => {
                    // Share functionality - in a real app, this could open a modal with sharing options
                    if (navigator.share) {
                      navigator.share({
                        title: 'My Virtual Try-On',
                        text: 'Check out my virtual outfit!',
                        url: result.result_image,
                      })
                    } else {
                      window.open(result.result_image, '_blank')
                    }
                  }}
                  className="ml-auto px-4 py-2 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors flex items-center"
                >
                  <i className="fas fa-share-alt mr-2"></i>
                  Share
                </button>
              </div>
              
              <div className="bg-gradient-to-b from-white to-gray-50 p-8 rounded-xl shadow-md border border-gray-100">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                  <div className="text-center">
                    <h4 className="text-xl font-medium mb-4 text-gray-700 inline-flex items-center">
                      <span className="w-8 h-8 rounded-full bg-secondary-100 flex items-center justify-center mr-2">
                        <i className="fas fa-user text-secondary-500"></i>
                      </span>
                      Original Model
                    </h4>
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300 group">
                      {modelPreview && (
                        <div className="relative overflow-hidden rounded-lg">
                        <img 
                          src={modelPreview} 
                          alt="Original Model" 
                            className="max-h-96 mx-auto rounded-lg shadow-sm transition-all duration-500 group-hover:scale-[1.02]"
                        />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300"></div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <h4 className="text-xl font-medium mb-4 text-gray-700 inline-flex items-center">
                      <span className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center mr-2">
                        <i className="fas fa-magic text-primary-500"></i>
                      </span>
                      Final Result
                    </h4>
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300 relative group">
                      {result.result_image && (
                        <div className="relative overflow-hidden rounded-lg">
                          <img 
                            src={result.result_image} 
                            alt="Result" 
                            className="max-h-96 mx-auto rounded-lg shadow-sm transition-all duration-500 group-hover:scale-[1.02]"
                            onError={(e) => {
                              console.error("Failed to load result image:", result.result_image);
                              e.target.src = 'https://via.placeholder.com/300x400?text=Result+Image+Not+Available';
                            }}
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300"></div>
                          <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300">
                            <div className="flex space-x-2">
                              <a 
                                href={result.result_image} 
                                download="virtual-tryon-result.jpg"
                                className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors"
                                title="Download"
                              >
                                <i className="fas fa-download"></i>
                              </a>
                            <a 
                              href={result.result_image} 
                              target="_blank" 
                              rel="noopener noreferrer"
                                className="bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors"
                              title="Open full size image"
                            >
                                <i className="fas fa-expand"></i>
                            </a>
                          </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="mt-10 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                  <h4 className="text-xl font-medium mb-6 text-gray-700 flex items-center">
                    <i className="fas fa-chart-line text-secondary-500 mr-3"></i>
                    Processing Details
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
                    <div className="bg-gray-50 p-4 rounded-lg hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                      <div className="text-secondary-500 text-xl mb-2">
                        <i className="fas fa-fingerprint"></i>
                      </div>
                      <p className="text-xs text-gray-500 mb-1">Request ID</p>
                      <p className="font-medium text-gray-800 break-all text-sm">{result.request_id}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                      <div className="text-secondary-500 text-xl mb-2">
                        <i className="fas fa-stopwatch"></i>
                      </div>
                      <p className="text-xs text-gray-500 mb-1">Processing Time</p>
                      <p className="font-medium text-gray-800">
                        <span className="text-2xl">{result.processing_time.toFixed(1)}</span>
                        <span className="text-xs ml-1">seconds</span>
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                      <div className="text-secondary-500 text-xl mb-2">
                        <i className="fas fa-calendar-alt"></i>
                      </div>
                      <p className="text-xs text-gray-500 mb-1">Timestamp</p>
                      <p className="font-medium text-gray-800 text-sm">{result.timestamp}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                      <div className="text-secondary-500 text-xl mb-2">
                        <i className="fas fa-tshirt"></i>
                      </div>
                      <p className="text-xs text-gray-500 mb-1">Garments Processed</p>
                      <p className="font-medium text-gray-800">
                        <span className="text-2xl">{garments.filter(g => g.file !== null).length}</span>
                        <span className="text-xs ml-1">items</span>
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="mt-8 flex justify-center space-x-4">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveStep(1);
                      setModelFile(null);
                      setModelPreview('');
                      setGarments([{ file: null, preview: '', category: 'auto' }]);
                      setResult(null);
                    }}
                    className="px-6 py-3 border border-secondary-200 rounded-full text-secondary-700 bg-white hover:bg-secondary-50 flex items-center transition-all duration-300 shadow-sm hover:shadow-md"
                  >
                    <i className="fas fa-redo mr-2"></i>
                    Try New Outfit
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => {
                      // Here you would implement logic to share or save the result
                      // For now, just download the image
                      const link = document.createElement('a');
                      link.href = result.result_image;
                      link.download = 'virtual-tryon-result.jpg';
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    className="px-6 py-3 border border-transparent rounded-full text-white bg-gradient-to-r from-secondary-500 to-primary-600 hover:from-secondary-600 hover:to-primary-700 flex items-center transition-all duration-300 shadow-sm hover:shadow-md"
                  >
                    <i className="fas fa-download mr-2"></i>
                    Save Result
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