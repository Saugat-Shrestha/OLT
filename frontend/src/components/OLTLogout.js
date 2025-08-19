import React, { useState } from 'react';
import axios from 'axios';

const OLTLogout = ({ handleLogout }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const initiateLogout = async () => {
    console.log('Logout button clicked - initiating logout...');
    setLoading(true);
    setError('');
    
    try {
      console.log('Sending request to /olt-quit...');
      const response = await axios.post('http://localhost:5000/olt-quit', {}, {
        withCredentials: true
      });
      
      console.log('Response received:', response.data);
      
      if (response.data.status === 'success') {
        console.log('Logout successful, calling handleLogout...');
        handleLogout();
      } else {
        console.log('Logout failed:', response.data.message);
        setError(response.data.message || 'Logout failed');
      }
    } catch (error) {
      console.error('Error during logout:', error);
      if (error.response && error.response.data) {
        setError(error.response.data.message || 'Logout failed');
      } else {
        setError('Connection error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="d-flex justify-content-end mb-3">
      {error && (
        <div className="alert alert-danger me-3" style={{ flex: 1 }}>
          {error}
        </div>
      )}
      
      <button 
        className="btn btn-outline-danger"
        onClick={initiateLogout}
        disabled={loading}
      >
        {loading ? 'Logging out...' : 'Logout from OLT'}
      </button>
    </div>
  );
};

export default OLTLogout;