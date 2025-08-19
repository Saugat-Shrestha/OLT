import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BoardStatus = () => {
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('http://localhost:5000/board-status', {
          withCredentials: true
        });
        
        if (response.data.status === 'success') {
          setStatus(response.data.data);
        } else {
          setError(response.data.message || 'Failed to get board status');
        }
      } catch (err) {
        if (err.response && err.response.data) {
          setError(err.response.data.message || 'Request failed');
        } else {
          setError('Connection error. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchStatus();
  }, []);

  return (
    <div className="card">
      <div className="card-header bg-info text-white">
        <h5>Board 0/0 Status</h5>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="text-center">
            <div className="spinner-border text-primary"></div>
            <p>Loading board status...</p>
          </div>
        ) : error ? (
          <div className="alert alert-danger">{error}</div>
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{status}</pre>
        )}
      </div>
    </div>
  );
};

export default BoardStatus;