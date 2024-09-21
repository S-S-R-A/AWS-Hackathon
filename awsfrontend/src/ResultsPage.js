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

      {/* Camera Icon */}
      <div className="camera-section">
        <img 
          src="https://cdn-icons-png.flaticon.com/512/72/72500.png" 
          alt="Camera Icon" 
          className="camera-icon"
        />
      </div>

      {/* Microphone Icon */}
      <div className="microphone-section">
        <img 
          src="https://cdn-icons-png.flaticon.com/512/848/848043.png" 
          alt="Microphone Icon" 
          className="microphone-icon"
        />
      </div>
    </div>
  );
};

export default ResultsPage;
