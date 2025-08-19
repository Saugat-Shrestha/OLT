import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import OLTLogin from './components/OLTLogin';
import Dashboard from './components/Dashboard';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [isOLTLoggedIn, setIsOLTLoggedIn] = useState(false);

  const handleLogin = (status) => {
    setIsOLTLoggedIn(status);
  };

  const handleLogout = () => {
    setIsOLTLoggedIn(false);
  };

  return (
    <Router>
      <Routes>
        <Route 
          path="/" 
          element={isOLTLoggedIn ? 
            <Navigate to="/dashboard" /> : 
            <OLTLogin onLogin={handleLogin} />} 
        />
        <Route 
          path="/dashboard" 
          element={
            isOLTLoggedIn ? 
              <Dashboard isOLTLoggedIn={isOLTLoggedIn} handleLogout={handleLogout} /> : 
              <Navigate to="/" />
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;