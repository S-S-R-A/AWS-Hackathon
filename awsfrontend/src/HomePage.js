import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './i18n';
import './styles/HomePage.css';

const HomePage = () => {
  const { t, i18n } = useTranslation();
  
  const [isOpen, setIsOpen] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);
  const [photoURL, setPhotoURL] = useState(null);
  const [videoURL, setVideoURL] = useState('/instructions_en.mp4'); // Initialize with default video URL
  const videoRef = useRef(null);
  const navigate = useNavigate(); // Hook for navigation

  const togglePopup = () => {
    setIsOpen(!isOpen);
  };
  useEffect(() => {
    const storedLanguage = localStorage.getItem('selectedLanguage') || 'en'; // Fallback to English if no language is selected
    i18n.changeLanguage(storedLanguage);
  
    // Set the video URL based on the language in localStorage
    if (storedLanguage === 'en') {
      setVideoURL('/instructions_en.mp4');
    } else if (storedLanguage === 'es') {
      setVideoURL('/instructions_es.mp4');
    } else if (storedLanguage === 'zh') {
      setVideoURL('/instructions_zh.mp4');
    }
  }, [i18n]);

  const changeLanguage = (lang) => {
    localStorage.setItem('selectedLanguage', lang);
    i18n.changeLanguage(lang);
  };

  
  const handleCameraClick = () => {
    setShowOptions(true); // Show options to upload or take a photo
  };

  const handleUploadFile = (event) => {
    const file = event.target.files[0];
    const fileUrl = URL.createObjectURL(file);
    console.log('Uploaded file:', file);
    navigate('/results', {
      state: { 
        file: fileUrl, 
        fileType: 'image/png',
        lang: i18n.language // Pass the current language along
      }
    });
    
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
      stopMediaStream(); // Cleanup the media stream on component unmount
    };
  }, [stopMediaStream]);

  return (
    <div className="container">
      <div className="flags">
        <button className="flag-item" onClick={() => changeLanguage('en')}>
          <img src="/usFlag.png" alt="English" />
          <p>English</p>
        </button>
        <button className="flag-item" onClick={() => changeLanguage('es')}>
          <img src="https://upload.wikimedia.org/wikipedia/commons/f/fc/Flag_of_Mexico.svg" alt="Español" />
          <p>Español</p>
        </button>
        <button className="flag-item" onClick={() => changeLanguage('zh')}>
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
        <p>{t('DocuVoice')}</p>
      </div>

      <div className="question">
        <button onClick={togglePopup}>
          <p>?</p>
        </button>

        {isOpen && (
          <div className="popup-overlay">
            <div className="popup">
              <h2>{t('Instructions')}</h2>
              <video width="850" height="600" controls>
                <source src={videoURL} type="video/mp4" />
              </video>

              <div className="close-btn">
                <button onClick={togglePopup}>
                  {t('Close')}
                </button>
              </div>
            </div>
          </div>
        )}
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
    </div>
  );
};

export default HomePage;
