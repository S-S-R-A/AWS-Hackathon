import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useSound from 'use-sound';
import ReactWebcam from 'react-webcam';
import './styles/ResultsPage.css';
import lamejs from 'lamejs';

const ResultsPage = () => {
  const { t, i18n } = useTranslation();
  const { state } = useLocation();
  const { file, fileType } = state || {};
  const [play] = useSound('/audio.mp3');
  const navigate = useNavigate();
  
  const [showOptions, setShowOptions] = useState(false);
  const [photoURL, setPhotoURL] = useState(null);
  const webcamRef = useRef(null);  // React Webcam ref

  // Audio Recording Hooks
  const [isRecording, setIsRecording] = useState(false); // Whether it's recording
  //const [audioURL, setAudioURL] = useState(''); // URL for playback of recording
  const mediaRecorderRef = useRef(null); // MediaRecorder reference for recording
  const [audioChunks, setAudioChunks] = useState([]); // To store audio data chunks
  const [buttonImage, setButtonImage] = useState("/microphoneIcon.png");

  useEffect(() => {
    const language = state?.lang || localStorage.getItem('selectedLanguage') || 'en';
    i18n.changeLanguage(language);
  }, [i18n, state]);

  const handleCameraClick = () => {
    setShowOptions(true); // Show options to upload or take a photo
  };

  const handleUploadFile = (event) => {
    const file = event.target.files[0];
    const fileUrl = URL.createObjectURL(file);
    navigate('/results', { state: { file: fileUrl, fileType: file.type } });
  };

  const capturePhoto = () => {
    const imageSrc = webcamRef.current.getScreenshot(); // Get the screenshot
    setPhotoURL(imageSrc);
    navigate('/results', { state: { file: imageSrc, fileType: 'image/png' } });
  };

  // Audio Recording Methods (Same as before)
  const startRecording = async () => {
    setIsRecording(true);
    setAudioChunks([]); 
    setButtonImage("redMic.png");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      const audioChunks = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        console.log("Data available size:", event.data.size); // Log data size to see if it's capturing anything
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        console.log("Recording stopped. Processing WAV file...");

        // Create a blob from the recorded audio chunks
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        // Create a URL for the blob
        const wavUrl = URL.createObjectURL(audioBlob);

        // Create a link to download the WAV file
        const link = document.createElement('a');
        link.href = wavUrl;
        link.download = 'recording.wav';

        // Simulate a click to trigger the download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log("WAV file saved.");
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
        {file && (
          fileType === 'application/pdf' ? (
            <embed src={file} width="600" height="800" title="Embedded PDF" className="pdf-viewer" />
          ) : (
            <img src={file} alt="Uploaded Content" className="uploaded-image" style={{ width: '600px', height: 'auto' }} />
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
          <button onClick={() => document.getElementById('file-upload').click()}>{t('Upload a file')}</button>
          <input id="file-upload" type="file" accept="image/*,application/pdf" style={{ display: 'none' }} onChange={handleUploadFile} />
          <button>{t('Take a photo')}</button>

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
