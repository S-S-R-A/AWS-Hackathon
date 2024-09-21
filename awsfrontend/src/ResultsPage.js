import React from 'react';
import './styles/ResultsPage.css'; // Import your custom styles

const ResultsPage = () => {
  const pdfUrl = 'https://clicklibrary.wordpress.com/wp-content/uploads/2018/01/diary-of-a-wimpy-kid-book-1-kinney-jeff.pdf'; // Hardcoded PDF URL

  return (
    <div className="container">
      {/* Container for the embedded PDF viewer */}
      <div className="pdf-section">
        <embed
          src={pdfUrl}
          width="600"
          height="800"
          title="Embedded PDF"
          className="pdf-viewer"
        />
      </div>
      <div className="camera-section">
  <button className="camera-button">
    <img 
      src="/cameraIcon.png" 
      alt="Camera Icon" 
      className="camera-icon"
    />
  </button>
</div>

{/* Microphone Button */}
<div className="microphone-section">
  <button className="microphone-button">
    <img 
      src="/microphoneIcon.png"
      alt="Microphone Icon" 
      className="microphone-icon"
    />
  </button>
</div>
    </div>
  );
};

export default ResultsPage;
