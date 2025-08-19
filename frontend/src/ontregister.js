import React, { useState } from 'react';
import axios from 'axios';

const OntRegister = () => {
  const [formData, setFormData] = useState({ sn: '', description: '' });
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/register-ont', formData);
      setResult(response.data.output);
    } catch (error) {
      setResult(`Error: ${error.response?.data.message || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header bg-success text-white">
        <h5>ONT Registration</h5>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label>Serial Number</label>
            <input
              type="text"
              className="form-control"
              value={formData.sn}
              onChange={(e) => setFormData({...formData, sn: e.target.value})}
              required
            />
          </div>
          <div className="mb-3">
            <label>Description</label>
            <input
              type="text"
              className="form-control"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              required
            />
          </div>
          <button type="submit" className="btn btn-success w-100" disabled={loading}>
            {loading ? 'Registering...' : 'Register ONT'}
          </button>
        </form>
        {result && (
          <div className="mt-3">
            <h6>Command Output:</h6>
            <pre style={{ whiteSpace: 'pre-wrap' }}>{result}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default OntRegister;