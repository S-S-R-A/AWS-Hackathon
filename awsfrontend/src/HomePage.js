import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './styles/HomePage.css';

const HomePage = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);
  const [photoURL, setPhotoURL] = useState(null);
  const videoRef = useRef(null);
  const navigate = useNavigate(); // Hook for navigation

  const togglePopup = () => {
    setIsOpen(!isOpen);
  };

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

  return (
    <div className="container">
      <div className="flags">
        <button className="flag-item">
          <img src="/usFlag.png" alt="English" />
          <p>English</p>
        </button>
        <button className="flag-item">
          <img src="https://upload.wikimedia.org/wikipedia/commons/f/fc/Flag_of_Mexico.svg" alt="Español" />
          <p>Español</p>
        </button>
        <button className="flag-item">
          <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Flag_of_the_People%27s_Republic_of_China.svg" alt="Chinese" />
          <p>中文</p>
        </button>
      </div>

      <div className="docuvoice">
        <button onClick={handleCameraClick}>
          <img src="/cameraIcon.png" alt="DocuVoice Camera" />
        </button>
      </div>

      <div className="docuvoice">
        <p>DocuVoice</p>
      </div>

      <div className="question">
        <button onClick={togglePopup}>
          <p>?</p>
        </button>

        {isOpen && (
          <div className="popup-overlay">
            <div className="popup">
              <h2>This is a Popup!</h2>
              <p>Click the button below to close the popup.</p>
              <button onClick={togglePopup} className="close-btn">
                Close
              </button>
            </div>
          </div>
        )}
      </div>

      {showOptions && (
        <div className="camera-options">
          <h3>Select an option</h3>
          <button onClick={() => document.getElementById('file-upload').click()}>
            Upload a file
          </button>
          <input
            id="file-upload"
            type="file"
            accept="image/*application/pdf"
            style={{ display: 'none' }}
            onChange={handleUploadFile}
          />
          <button onClick={handleTakePhoto}>Take a photo</button>

          {mediaStream && (
            <div className="camera-preview">
              <video ref={videoRef} autoPlay playsInline></video>
              <button onClick={capturePhoto}>Capture Photo</button>
            </div>
          )}
        </div>
      )}

      {photoURL && (
        <div className="photo-preview">
          <h3>Captured Photo</h3>
          <img src={photoURL} alt="Captured" />
        </div>
      )}
    </div>
  );
};

export default HomePage;
