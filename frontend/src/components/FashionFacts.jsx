import React, { useState, useEffect } from 'react';

const fashionFacts = [
  "The average person owns 7 pairs of jeans.",
  "High heels were originally worn by men in the 10th century to help ride horses.",
  "The T-shirt is the most popular clothing item in the world.",
  "The world's longest fashion runway was over 3 kilometers long!",
  "Blue jeans were invented in 1873 by Levi Strauss and Jacob Davis.",
  "Fashion Week takes place in the \"Big Four\" cities: New York, London, Milan, and Paris.",
  "The little black dress was made famous by Coco Chanel in the 1920s.",
  "Wearing black used to be a sign of wealth in 14th-century Spain, because black dye was expensive.",
  "Sneakers were originally called \"plimsolls.\"",
  "The wedding dress tradition of wearing white started with Queen Victoria in 1840.",
  "Thrift shopping is more popular than ever thanks to sustainability trends.",
  "Karl Lagerfeld had over 300,000 books — and loved fashion just as much as reading.",
  "Some fashion brands now use AI to design clothes and predict trends.",
  "The global fashion industry is worth over $2.5 trillion.",
  "Velcro was inspired by burrs sticking to a dog's fur."
];

const icons = [
  "fa-tshirt",
  "fa-shoe-prints",
  "fa-tag",
  "fa-ruler",
  "fa-vest",
  "fa-city",
  "fa-female",
  "fa-palette",
  "fa-running",
  "fa-gem",
  "fa-recycle",
  "fa-book",
  "fa-robot",
  "fa-dollar-sign",
  "fa-magic"
];

function FashionFacts() {
  const [currentFactIndex, setCurrentFactIndex] = useState(0);
  const [fadeIn, setFadeIn] = useState(true);

  useEffect(() => {
    // Change fact every 5 seconds
    const interval = setInterval(() => {
      setFadeIn(false);
      
      // Wait for fade out animation to complete
      setTimeout(() => {
        setCurrentFactIndex((prevIndex) => (prevIndex + 1) % fashionFacts.length);
        setFadeIn(true);
      }, 500);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-lg mx-auto my-6 bg-white rounded-xl shadow-md p-5 overflow-hidden border border-gray-100">
      <div className={`transition-opacity duration-500 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <div className="flex items-center mb-3">
          <div className="bg-indigo-100 text-indigo-600 rounded-full w-10 h-10 flex items-center justify-center mr-3">
            <i className={`fas ${icons[currentFactIndex]}`}></i>
          </div>
          <h3 className="text-lg font-bold text-gray-800">Fashion Fact</h3>
        </div>
        
        <div className="bg-gradient-to-r from-gray-50 to-white p-4 rounded-lg">
          <p className="text-gray-700">
            {fashionFacts[currentFactIndex]}
          </p>
        </div>
        
        <div className="flex justify-center mt-4">
          {fashionFacts.map((_, index) => (
            <div 
              key={index}
              className={`w-2 h-2 mx-1 rounded-full ${
                index === currentFactIndex ? 'bg-indigo-500' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default FashionFacts; 