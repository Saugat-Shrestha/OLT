import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import OLTLogin from './components/OLTLogin';
import Dashboard from './components/Dashboard';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [isOLTLoggedIn, setIsOLTLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check session status on app load
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await axios.get('http://localhost:5000/check-session', {
          withCredentials: true
        });
        
        if (response.data.status === 'success' && response.data.logged_in) {
          setIsOLTLoggedIn(true);
        }
      } catch (error) {
        console.error('Session check failed:', error);
        // If session check fails, assume not logged in
        setIsOLTLoggedIn(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkSession();
  }, []);

  const handleLogin = (status) => {
    setIsOLTLoggedIn(status);
  };

  const handleLogout = () => {
    setIsOLTLoggedIn(false);
  };

  // Show loading spinner while checking session
  if (isLoading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

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