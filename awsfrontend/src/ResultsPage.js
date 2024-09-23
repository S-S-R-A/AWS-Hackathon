// File: ./awsfrontend/src/ResultsPage.js

import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useSound from 'use-sound';
import ReactWebcam from 'react-webcam';
import './styles/ResultsPage.css';

const ResultsPage = () => {
  const { t, i18n } = useTranslation();
  const { state } = useLocation();
  const { fileUrl, lang, predicted_label, confidence } = state || {};
  const [play] = useSound('/audio.mp3');
  const navigate = useNavigate();
  
  const [showOptions, setShowOptions] = useState(false);
  const [photoURL, setPhotoURL] = useState(null);
  const webcamRef = useRef(null);  // React Webcam ref

  // Audio Recording Hooks
  const [isRecording, setIsRecording] = useState(false); // Whether it's recording
  const mediaRecorderRef = useRef(null); // MediaRecorder reference for recording
  const [buttonImage, setButtonImage] = useState("/microphoneIcon.png");

  useEffect(() => {
    const language = lang || localStorage.getItem('selectedLanguage') || 'en';
    i18n.changeLanguage(language);
  }, [i18n, lang]);

  const handleCameraClick = () => {
    setShowOptions(true); // Show options to upload or take a photo
  };

  const handleUploadFile = (event) => {
    const file = event.target.files[0];
    const fileUrl = URL.createObjectURL(file);
    navigate('/results', { state: { fileUrl, fileType: file.type, predicted_label, confidence } });
  };

  const capturePhoto = () => {
    const imageSrc = webcamRef.current.getScreenshot(); // Get the screenshot
    setPhotoURL(imageSrc);
    navigate('/results', { state: { fileUrl: imageSrc, fileType: 'image/png', predicted_label, confidence } });
  };

  // Audio Recording Methods
  const startRecording = async () => {
    setIsRecording(true);
    setButtonImage("redMic.png");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      const audioChunks = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Handle audio data as needed
        // For example, you could upload it or process it further
      };

      mediaRecorderRef.current.start();
      console.log("Recording started...");
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      const stream = mediaRecorderRef.current.stream;
      stream.getTracks().forEach(track => track.stop());
      setButtonImage("/microphoneIcon.png");
      console.log('Recording stopped.');
    }
  };

  return (
    <div className="container">
      <div className="pdf-section">
        {fileUrl && (
          fileUrl.endsWith('.pdf') ? (
            <embed src={fileUrl} width="600" height="800" title="Embedded PDF" className="pdf-viewer" />
          ) : (
            <img src={fileUrl} alt="Uploaded Content" className="uploaded-image" style={{ width: '600px', height: 'auto' }} />
          )
        )}
      </div>

      {/* Display the predicted document type */}
      <div className="prediction-section">
        {predicted_label ? (
          <h2>{t('Predicted Document Type')}: {predicted_label} ({(confidence * 100).toFixed(2)}%)</h2>
        ) : (
          <h2>{t('Predicted Document Type')}: {t('Unknown')}</h2>
        )}
      </div>

      <div className="camera-section">
        <button className="camera-button" onClick={handleCameraClick}>
          <img src="/cameraIcon.png" alt="Camera Icon" className="camera-icon" />
        </button>
      </div>

      {showOptions && (
        <div className="camera-options">
          <h3>{t('Select an option')}</h3>
          <button onClick={() => document.getElementById('file-upload').click()}>{t('Upload a file')}</button>
          <input id="file-upload" type="file" accept="image/*,application/pdf" style={{ display: 'none' }} onChange={handleUploadFile} />
          <button onClick={capturePhoto}>{t('Take a photo')}</button>

          {/* React Webcam Component */}
          <div className="camera-preview">
            <ReactWebcam ref={webcamRef} screenshotFormat="image/png" style={{ width: '600px', height: 'auto' }} />
            <button className="capture-button" onClick={capturePhoto}>{t('Capture Photo')}</button>
          </div>
        </div>
      )}

      {photoURL && (
        <div className="photo-preview">
          <h3>{t('Captured Photo')}</h3>
          <img src={photoURL} alt="Captured" />
        </div>
      )}

      <div className="microphone-section">
        <button className="microphone-button" onClick={isRecording ? stopRecording : startRecording}>
          <img src={buttonImage} alt="Microphone Icon" className="microphone-icon" />
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
