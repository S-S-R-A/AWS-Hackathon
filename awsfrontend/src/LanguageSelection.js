import React from 'react';
import './styles/LanguageSelection.css';

const LanguageSelection = () => {
  return (
    <div className="container">
      <div className="flags">
        <div className="flag-item">
          <img src="https://upload.wikimedia.org/wikipedia/en/a/a4/Flag_of_the_United_States.svg" alt="English" />
          <p>English</p>
        </div>
        <div className="flag-item">
          <img src="https://upload.wikimedia.org/wikipedia/commons/f/fc/Flag_of_Mexico.svg" alt="Español" />
          <p>Español</p>
        </div>
        <div className="flag-item">
          <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Flag_of_the_People%27s_Republic_of_China.svg" alt="Chinese" />
          <p>中文</p>
        </div>
      </div>

      <div className="docuvoice">
        <img src="https://cdn-icons-png.flaticon.com/512/72/72500.png" alt="DocuVoice Camera" />
        <p>DocuVoice</p>
      </div>

      <div className="question">
        <p>?</p>
      </div>
    </div>
  );
};

export default LanguageSelection;
