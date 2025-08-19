import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BoardStatus = () => {
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('http://localhost:5000/board-status');
        setStatus(response.data.data);
      } catch (error) {
        console.error('Error fetching board status:', error);
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
          <div className="spinner-border"></div>
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap' }}>{status}</pre>
        )}
      </div>
    </div>
  );
};

export default BoardStatus;