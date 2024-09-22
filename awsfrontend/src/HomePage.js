import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactWebcam from 'react-webcam';
import './i18n';
import './styles/HomePage.css';

const HomePage = () => {
  const { t, i18n } = useTranslation();
  
  const [isOpen, setIsOpen] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [photoURL, setPhotoURL] = useState(null);
  const [videoURL, setVideoURL] = useState('/instructions_en.mp4'); // Initialize with default video URL
  const webcamRef = useRef(null); // Webcam reference
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
        fileType: 'application/pdf',
        lang: i18n.language // Pass the current language along
      }
    });
  };

  const capturePhoto = () => {
    const imageSrc = webcamRef.current.getScreenshot(); // Get the screenshot from the webcam
    setPhotoURL(imageSrc);
    navigate('/results', { state: { file: imageSrc, fileType: 'image/png' } });
  };

  

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
          <button>{t('Take a photo')}</button>

          <div className="camera-preview">
          <ReactWebcam ref={webcamRef} screenshotFormat="image/png" style={{ width: '600px', height: 'auto' }} />
            <button onClick={capturePhoto}>{t('Capture Photo')}</button>
          </div>
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
