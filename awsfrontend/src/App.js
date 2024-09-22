// File: ./awsfrontend/src/App.js

import React from 'react';
import HomePage from './HomePage';
import ResultsPage from './ResultsPage';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
 
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />  {/* HomePage is the default route */}
        <Route path="/results" element={<ResultsPage />}  />  {/* Route to ResultsPage */}
      </Routes>
    </Router>
  );
}

export default App;
