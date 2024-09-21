import React from 'react';
import './styles/HomePage.css';


const HomePage = () => {
  return (
    <div className="container">
      <div className="flags">
        <button className="flag-item">
          <img
            src="https://upload.wikimedia.org/wikipedia/en/a/a4/Flag_of_the_United_States.svg"
            alt="English"
          />
          <p>English</p>
        </button>
        <button className="flag-item">
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/f/fc/Flag_of_Mexico.svg"
            alt="Español"
          />
          <p>Español</p>
        </button>
        <button className="flag-item">
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Flag_of_the_People%27s_Republic_of_China.svg"
            alt="Chinese"
          />
          <p>中文</p>
        </button>
      </div>
      
      
      <div className="docuvoice">
        <button>
        <img 
          src="/cameraIcon.png" 
          alt="DocuVoice Camera"/>
        </button>
      </div>

      <div className = "docuvoice">
        <p>DocuVoice</p>
      </div>


      <div className="question">
        <button>
            <p>?</p>
        </button>
      </div>
    </div>
  );
};

export default HomePage;
