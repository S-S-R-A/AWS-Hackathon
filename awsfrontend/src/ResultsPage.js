import React from 'react';
import { useLocation } from 'react-router-dom';
import useSound from 'use-sound';
import './styles/ResultsPage.css';

const ResultsPage = () => {
  const { state } = useLocation(); // Get state from navigation
  const { file, fileType } = state || {};
  const [play] = useSound('/audio.mp3');

  return (
    <div className="container">
      <div className="pdf-section">
        {file && (
          fileType === 'application/pdf' ? (
            <embed
              src={file}
              width="600"
              height="800"
              title="Embedded PDF"
              className="pdf-viewer"
            />
          ) : (
            <img
              src={file}
              alt="Uploaded Content"
              className="uploaded-image"
              style={{ width: '600px', height: 'auto' }}
            />
          )
        )}
      </div>
      <div className="camera-section">
        <button className="camera-button">
          <img src="/cameraIcon.png" alt="Camera Icon" className="camera-icon" />
        </button>
      </div>

      <div className="microphone-section">
        <button className="microphone-button">
          <img src="/microphoneIcon.png" alt="Microphone Icon" className="microphone-icon" />
        </button>
      </div>

      <div className="replay-section">
        <button className="replay-button" onClick={play}>
          <img src="/replayButton.png" alt="Replay Button" className="microphone-icon" />
        </button>
      </div>
    </div>
  );
};

export default ResultsPage;
