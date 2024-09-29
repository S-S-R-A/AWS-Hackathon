import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useSound from 'use-sound';
import ReactWebcam from 'react-webcam';
import './styles/ResultsPage.css';
import lamejs from 'lamejs';
import AWS from 'aws-sdk';
import TranscribeService from 'aws-sdk/clients/transcribeservice';

const ResultsPage = () => {
  const { t, i18n } = useTranslation();
  const { state } = useLocation();
  const [play] = useSound('/audio.mp3');
  const navigate = useNavigate();
  const { fileUrl, lang, predicted_label, confidence, mp3_url } = state || {};
  const [showOptions, setShowOptions] = useState(false);
  const [showWebcam, setShowWebcam] = useState(false); // New state to toggle webcam
  const [photoURL, setPhotoURL] = useState(null);
  const webcamRef = useRef(null);  // React Webcam ref

  AWS.config.update({
    region: AWS_REGION, // e.g., 'us-east-1'
    accessKeyId: AWS_ACCESS_KEY_ID,
    secretAccessKey: AWS_SECRET_ACCESS_KEY,
  });


  
  const s3 = new AWS.S3();
  const bucketName = 'polly-wav';

  // Audio Recording Hooks
  const [isRecording, setIsRecording] = useState(false); // Whether it's recording
  const mediaRecorderRef = useRef(null); // MediaRecorder reference for recording
  const [audioChunks, setAudioChunks] = useState([]); // To store audio data chunks
  const [buttonImage, setButtonImage] = useState("/microphoneIcon.png");

  const selectedlanguage = lang || localStorage.getItem('selectedLanguage') || 'en';
  let language;

  if(selectedlanguage === 'es') {
      language = 'es-ES'
  }
  else if(selectedlanguage === 'zh') {
    language = 'zh-CN'
  }
  else{
    language = 'en-US'
  }

  useEffect(() => {
    i18n.changeLanguage(selectedlanguage);
  }, [i18n, selectedlanguage, state]); // Include selectedLanguage in the dependency array

  // State for MP3 URL
  const [mp3Url, setMp3Url] = useState(mp3_url || null);
  const audioRef = useRef(null); // Ref for the audio element

  // Automatically play the audio when mp3Url is set
  useEffect(() => {
    if (mp3Url && audioRef.current) {
      audioRef.current.play().catch(error => {
        console.error("Error playing audio:", error);
      });
    }
  }, [mp3Url]);

  // Polling for MP3 URL if not available initially
  useEffect(() => {
    const fetchMp3Url = async () => {
      try {
        const response = await fetch('http://localhost:8080/get-mp3-url'); // Replace with your backend URL
        if (response.ok) {
          const data = await response.json();
          if (data.mp3_url) {
            setMp3Url(data.mp3_url);
          }
        }
      } catch (error) {
        console.error("Error fetching MP3 URL:", error);
      }
    };

    if (!mp3Url) {
      const interval = setInterval(() => {
        fetchMp3Url();
      }, 5000); // Poll every 5 seconds

      return () => clearInterval(interval);
    }
  }, [mp3Url]);

  const handleCameraClick = () => {
    setShowOptions(true); // Show options to upload or take a photo
  };

  const handleUploadFile = (event) => {
    const file = event.target.files[0];
    const fileUrl = URL.createObjectURL(file);
    navigate('/results', { state: { fileUrl, fileType: file.type, predicted_label, confidence } });
    setShowOptions(false);
    setShowWebcam(false);  // Turn off the webcam after capturing the photo
  };

  const capturePhoto = () => {
    const imageSrc = webcamRef.current.getScreenshot(); // Get the screenshot
    setPhotoURL(imageSrc);
    navigate('/results', { state: { fileUrl: imageSrc, fileType: 'image/png', predicted_label, confidence } });
    setShowOptions(false);
    setShowWebcam(false);  // Turn off the webcam after capturing the photo
  };

  // Audio Recording Methods
  const startRecording = async () => {
    setIsRecording(true);
    setAudioChunks([]);
    setButtonImage("redMic.png");
  
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      const localAudioChunks = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        console.log("Data available size:", event.data.size); // Log data size to see if it's capturing anything
        if (event.data.size > 0) {
          localAudioChunks.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        console.log("Recording stopped. Processing WAV file...");

        // Create a blob from the recorded audio chunks
        const audioBlob = new Blob(localAudioChunks, { type: 'audio/wav' });

        try {
          // Upload the WAV file to S3
          const s3Url = await uploadToS3(audioBlob);
          console.log("WAV file uploaded to S3:", s3Url);

          // Start transcription after upload is complete
          await startTranscription(s3Url, language);
        } catch (error) {
          console.error("Error during upload and transcription:", error);
        }
      };

      mediaRecorderRef.current.start();
      console.log("Recording started...");
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };
  
  // Upload function to send the WAV file to S3
  const uploadToS3 = async (audioBlob) => {
    const fileName = `audio_${Date.now()}.wav`; // Create a unique file name
    const langFileName = `language_${Date.now()}.json`; // File name for the language data

    const params = {
      Bucket: bucketName,
      Key: `input/audio/${fileName}`,
      Body: audioBlob,
      ContentType: 'audio/wav'
    };
    
    // Prepare the language data as a JSON object
    const langData = {
      LanguageCode: language,
    };

    const langParams = {
      Bucket: bucketName,
      Key: `input/audio/${langFileName}`,
      Body: JSON.stringify(langData), // Convert langData to a JSON string
      ContentType: 'application/json', // Set content type to JSON
    };
    
    try {
      const uploadResult = await s3.upload(params).promise();
      const uploadLang = await s3.upload(langParams).promise();

      console.log('Audio file uploaded successfully:', uploadResult.Location);
      console.log('Language data uploaded successfully:', uploadLang.Location);

      return uploadResult.Location;  // Return the URL of the uploaded file
    } catch (error) {
      console.error('Error uploading file to S3:', error);
      throw error;
    }
  };
  
  // Stops the mic from recording
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
    
  const transcribe = new AWS.TranscribeService();
  
  const startTranscription = async (fileUrl, language) => {
    console.log("language: " + language)
    const uniqueJobName = `TranscriptionJob_${Date.now()}`;
    const params = {
      TranscriptionJobName: uniqueJobName, // Unique job name
      LanguageCode: language, // Set the language
      Media: {
        MediaFileUri: fileUrl, // S3 URI for the audio files
      },
      MediaFormat: 'wav', // Format of your audio file
      OutputBucketName: bucketName, // Optional: where to store the transcription output
    };
  
    try {
      const response = await transcribe.startTranscriptionJob(params).promise();
      console.log('Transcription Job Started:', response);
    } catch (error) {
      console.error('Error starting transcription job:', error);
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
          <h3>{t('Select an option')}</h3>
        </button>
        
        <button onClick={() => document.getElementById('file-upload').click()}>{t('Upload a file')}</button>
        <input id="file-upload" type="file" accept="image/*,application/pdf" style={{ display: 'none' }} onChange={handleUploadFile} />
        <button onClick={capturePhoto}>{t('Take a photo')}</button>

        {/* React Webcam Component */}
        {showWebcam && (
          <div className="camera-preview">
            <ReactWebcam ref={webcamRef} screenshotFormat="image/png" style={{ width: '600px', height: 'auto' }} />
            <button className="capture-button" onClick={capturePhoto}>{t('Capture Photo')}</button>
          </div>
        )}
      </div>

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

      {/* Audio Player for the MP3 */}
      {mp3Url && (
        <div className="audio-player">
          <h3>{t('Translation Audio')}</h3>
          <audio ref={audioRef} controls src={mp3Url}>
            Your browser does not support the audio element.
          </audio>
        </div>
      )}

      {/* Loading Indicator for MP3 */}
      {!mp3Url && (
        <div className="loading-spinner">
          <p>{t('Loading translation audio...')}</p>
          {/* You can add a spinner or animation here */}
        </div>
      )}
    </div>
  );
};

export default ResultsPage;
