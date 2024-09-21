import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useSound from 'use-sound';
import './styles/ResultsPage.css';

const ResultsPage = () => {
  
  const [showOptions, setShowOptions] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);
  const [photoURL, setPhotoURL] = useState(null);
  const videoRef = useRef(null);
  const { state } = useLocation(); // Get state from navigation
  const { t, i18n } = useTranslation();
  const { file, fileType } = state || {};
  const [play] = useSound('/audio.mp3');
  const navigate = useNavigate();
  
  const handleCameraClick = () => {
    setShowOptions(true); // Show options to upload or take a photo
  };

  const handleUploadFile = (event) => {
    const file = event.target.files[0];
    const fileUrl = URL.createObjectURL(file);
    console.log('Uploaded file:', file);
    navigate('/results', { state: { file: fileUrl, fileType: file.type } });
  };

  const handleTakePhoto = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setMediaStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream; // Set the video source to the stream
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
    }
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageUrl = canvas.toDataURL('image/png');
    setPhotoURL(imageUrl);
    navigate('/results', { state: { file: imageUrl, fileType: 'image/png' } });
    stopMediaStream();
  };

  const stopMediaStream = useCallback(() => {
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      setMediaStream(null);
    }
  }, [mediaStream]);

  useEffect(() => {
    return () => {
      stopMediaStream();
    };
  }, [stopMediaStream]);

  useEffect(() => {
    // Retrieve the passed language or fallback to localStorage
    const language = state?.lang || localStorage.getItem('selectedLanguage') || 'en';
    i18n.changeLanguage(language);
  }, [i18n, state]);

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
        <button className="camera-button" onClick={handleCameraClick}>
          <img src="/cameraIcon.png" alt="Camera Icon" className="camera-icon" />
        </button>
      </div>

      {showOptions && (
        <div className="camera-options">
          <h3>{t('Select an option')}</h3>
          <button onClick={() => document.getElementById('file-upload').click()}>
          {t('Upload a file')}
          </button>
          <input
            id="file-upload"
            type="file"
            accept="image/*,application/pdf"
            style={{ display: 'none' }}
            onChange={handleUploadFile}
          />
          <button onClick={handleTakePhoto}>{t('Take a photo')}</button>

          {mediaStream && (
            <div className="camera-preview">
              <video ref={videoRef} autoPlay playsInline></video>
              <button onClick={capturePhoto}>{t('Capture Photo')}</button>
            </div>
          )}
        </div>
      )}

      {photoURL && (
        <div className="photo-preview">
          <h3>{t('Captured Photo')}</h3>
          <img src={photoURL} alt="Captured" />
        </div>
      )}
    

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
