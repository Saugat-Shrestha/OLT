import React, { useState, useEffect } from 'react';
import axios from 'axios';

const OntRegister = () => {
  const [autofindResult, setAutofindResult] = useState('');
  const [parsedOnts, setParsedOnts] = useState([]);
  const [ontInfo, setOntInfo] = useState('');
  const [ontStatus, setOntStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingAutofind, setLoadingAutofind] = useState(false);
  const [loadingRegister, setLoadingRegister] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [loadingVerify, setLoadingVerify] = useState(false);
  const [error, setError] = useState('');
  const [errorAutofind, setErrorAutofind] = useState('');
  const [errorRegister, setErrorRegister] = useState('');
  const [errorInfo, setErrorInfo] = useState('');
  const [errorStatus, setErrorStatus] = useState('');
  const [errorVerify, setErrorVerify] = useState('');
  const [errorTest, setErrorTest] = useState('');

  // Registration form state
  const [formData, setFormData] = useState({
    boardId: '0/0',
    portId: '5',
    ontId: '1',
    serialNumber: '',
    description: 'test',
    lineProfileId: '10',
    serviceProfileId: '10'
  });

  // Status check form state
  const [statusFormData, setStatusFormData] = useState({
    boardId: '0/0',
    ontId: '1'
  });

  // Info check form state
  const [infoFormData, setInfoFormData] = useState({
    description: 'test'
  });

  // Verification form state
  const [verifyFormData, setVerifyFormData] = useState({
    boardId: '0/0',
    portId: '5',
    ontId: '1',
    serialNumber: ''
  });

  // Test command form state
  const [testFormData, setTestFormData] = useState({
    command: 'display board 0'
  });

  // Registration results
  const [registrationLog, setRegistrationLog] = useState('');
  const [verificationLog, setVerificationLog] = useState('');
  const [testLog, setTestLog] = useState('');

  // Parse ONT autofind results
  const parseOntAutofind = (output) => {
    const lines = output.split('\n');
    const ontList = [];
    let currentOnt = {};
    let inOntSection = false;
    
    console.log("Parsing ONT autofind output:", output);
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      console.log("Processing line:", trimmedLine);
      
      // Look for ONT section start (dashed line)
      if (trimmedLine.match(/^-+$/)) {
        if (currentOnt.number) {
          ontList.push(currentOnt);
        }
        currentOnt = {};
        inOntSection = true;
        continue;
      }
      
      // Parse Number
      if (trimmedLine.match(/^Number\s*:\s*(\d+)$/)) {
        currentOnt.number = trimmedLine.match(/^Number\s*:\s*(\d+)$/)[1];
        console.log("Found ONT number:", currentOnt.number);
      }
      // Parse F/S/P
      else if (trimmedLine.match(/^F\/S\/P\s*:\s*(.+)$/)) {
        currentOnt.fsp = trimmedLine.match(/^F\/S\/P\s*:\s*(.+)$/)[1];
        console.log("Found F/S/P:", currentOnt.fsp);
      }
      // Parse Serial Number
      else if (trimmedLine.match(/^Ont SN\s*:\s*(.+)$/)) {
        const snMatch = trimmedLine.match(/^Ont SN\s*:\s*(.+)$/);
        if (snMatch) {
          // Extract just the serial number part (before the space and parentheses)
          const fullSn = snMatch[1];
          const snParts = fullSn.split(' ');
          currentOnt.serialNumber = snParts[0]; // Take the first part (the actual SN)
          console.log("Found Serial Number:", currentOnt.serialNumber);
        }
      }
      // Parse Password
      else if (trimmedLine.match(/^Password\s*:\s*(.+)$/)) {
        currentOnt.password = trimmedLine.match(/^Password\s*:\s*(.+)$/)[1];
        console.log("Found Password:", currentOnt.password);
      }
      // Parse Vendor ID
      else if (trimmedLine.match(/^VendorID\s*:\s*(.+)$/)) {
        currentOnt.vendorId = trimmedLine.match(/^VendorID\s*:\s*(.+)$/)[1];
        console.log("Found Vendor ID:", currentOnt.vendorId);
      }
      // Parse Ont Version
      else if (trimmedLine.match(/^Ont Version\s*:\s*(.+)$/)) {
        currentOnt.version = trimmedLine.match(/^Ont Version\s*:\s*(.+)$/)[1];
        console.log("Found Ont Version:", currentOnt.version);
      }
      // Parse Software Version
      else if (trimmedLine.match(/^Ont SoftwareVersion\s*:\s*(.+)$/)) {
        currentOnt.softwareVersion = trimmedLine.match(/^Ont SoftwareVersion\s*:\s*(.+)$/)[1];
        console.log("Found Software Version:", currentOnt.softwareVersion);
      }
      // Parse Equipment ID
      else if (trimmedLine.match(/^Ont EquipmentID\s*:\s*(.+)$/)) {
        currentOnt.equipmentId = trimmedLine.match(/^Ont EquipmentID\s*:\s*(.+)$/)[1];
        console.log("Found Equipment ID:", currentOnt.equipmentId);
      }
      // Parse autofind time
      else if (trimmedLine.match(/^Ont autofind time\s*:\s*(.+)$/)) {
        currentOnt.autofindTime = trimmedLine.match(/^Ont autofind time\s*:\s*(.+)$/)[1];
        console.log("Found autofind time:", currentOnt.autofindTime);
      }
      // Check for end of ONT section (another dashed line or summary)
      else if (trimmedLine.match(/^The number of GPON autofind ONT is \d+$/) || 
               (trimmedLine.match(/^-+$/) && currentOnt.number)) {
        inOntSection = false;
      }
    }
    
    // Add the last ONT if exists
    if (currentOnt.number) {
      ontList.push(currentOnt);
    }
    
    console.log("Parsed ONT list:", ontList);
    return ontList;
  };

  const handleFormChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleStatusFormChange = (e) => {
    setStatusFormData({
      ...statusFormData,
      [e.target.name]: e.target.value
    });
  };

  const handleInfoFormChange = (e) => {
    setInfoFormData({
      ...infoFormData,
      [e.target.name]: e.target.value
    });
  };

  const handleVerifyFormChange = (e) => {
    setVerifyFormData({
      ...verifyFormData,
      [e.target.name]: e.target.value
    });
  };

  const handleTestFormChange = (e) => {
    setTestFormData({
      ...testFormData,
      [e.target.name]: e.target.value
    });
  };

  const handleTestCommand = async (e) => {
    e.preventDefault();
    setErrorTest('');
    setTestLog('');

    try {
      const response = await axios.post('http://localhost:5000/test-command', testFormData, {
        withCredentials: true
      });
      
      if (response.data.status === 'success') {
        setTestLog(response.data.data);
      } else {
        setErrorTest(response.data.message || 'Failed to test command');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setErrorTest(err.response.data.message || 'Request failed');
      } else {
        setErrorTest('Connection error. Please try again.');
      }
    }
  };

  const handleAutofind = async () => {
    setLoadingAutofind(true);
    setErrorAutofind('');
    setAutofindResult('');
    setParsedOnts([]);

    try {
      console.log('Sending ONT autofind request...');
      const response = await axios.get('http://localhost:5000/ont-autofind', {
        withCredentials: true
      });
      
      console.log('ONT autofind response received:', response);
      console.log('Response data:', response.data);
      
      if (response.data.status === 'success') {
        console.log('Setting autofind result:', response.data.data);
        setAutofindResult(response.data.data);
        
        // Parse the ONT data
        const parsed = parseOntAutofind(response.data.data);
        setParsedOnts(parsed);
        console.log('Parsed ONTs:', parsed);
        
        // Auto-fill the first ONT's data if available
        if (parsed.length > 0) {
          const firstOnt = parsed[0];
          console.log("Auto-filling with first ONT:", firstOnt);
          
          // Extract port ID from F/S/P format
          let portId = '5'; // default
          if (firstOnt.fsp) {
            const fspParts = firstOnt.fsp.split('/');
            if (fspParts.length >= 3) {
              portId = fspParts[2]; // Third part is the port
            }
          }
          
          setFormData(prev => ({
            ...prev,
            serialNumber: firstOnt.serialNumber || '',
            portId: portId,
            ontId: firstOnt.number || '1'
          }));
          
          // Also auto-fill verification form
          setVerifyFormData(prev => ({
            ...prev,
            serialNumber: firstOnt.serialNumber || '',
            portId: portId,
            ontId: firstOnt.number || '1'
          }));
          
          console.log("Auto-filled forms with:", {
            serialNumber: firstOnt.serialNumber,
            portId: portId,
            ontId: firstOnt.number
          });
        }
      } else {
        console.error('ONT autofind failed:', response.data.message);
        setErrorAutofind(response.data.message || 'Failed to get autofind results');
      }
    } catch (err) {
      console.error('ONT autofind error:', err);
      if (err.response && err.response.data) {
        console.error('Error response data:', err.response.data);
        setErrorAutofind(err.response.data.message || 'Request failed');
      } else {
        console.error('Network error:', err.message);
        setErrorAutofind('Connection error. Please try again.');
      }
    } finally {
      setLoadingAutofind(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoadingRegister(true);
    setErrorRegister('');
    setRegistrationLog('');

    try {
      const response = await axios.post('http://localhost:5000/ont-register', formData, {
        withCredentials: true
      });
      
      if (response.data.status === 'success') {
        setRegistrationLog(response.data.data);
        alert('ONT registration completed successfully! Check the log below for details.');
        
        // Auto-fill verification form with same data
        setVerifyFormData({
          boardId: formData.boardId,
          portId: formData.portId,
          ontId: formData.ontId,
          serialNumber: formData.serialNumber
        });
      } else {
        setRegistrationLog(response.data.data || '');
        setErrorRegister(response.data.message || 'Failed to register ONT');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setErrorRegister(err.response.data.message || 'Request failed');
        if (err.response.data.data) {
          setRegistrationLog(err.response.data.data);
        }
      } else {
        setErrorRegister('Connection error. Please try again.');
      }
    } finally {
      setLoadingRegister(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoadingVerify(true);
    setErrorVerify('');
    setVerificationLog('');

    try {
      const response = await axios.post('http://localhost:5000/ont-verify', verifyFormData, {
        withCredentials: true
      });
      
      if (response.data.status === 'success') {
        setVerificationLog(response.data.data);
      } else {
        setErrorVerify(response.data.message || 'Failed to verify ONT');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setErrorVerify(err.response.data.message || 'Request failed');
      } else {
        setErrorVerify('Connection error. Please try again.');
      }
    } finally {
      setLoadingVerify(false);
    }
  };

  const handleGetInfo = async (e) => {
    e.preventDefault();
    setLoadingInfo(true);
    setErrorInfo('');
    setOntInfo('');

    try {
      const response = await axios.get(`http://localhost:5000/ont-info/${encodeURIComponent(infoFormData.description)}`, {
        withCredentials: true
      });
      
      if (response.data.status === 'success') {
        setOntInfo(response.data.data);
      } else {
        setErrorInfo(response.data.message || 'Failed to get ONT info');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setErrorInfo(err.response.data.message || 'Request failed');
      } else {
        setErrorInfo('Connection error. Please try again.');
      }
    } finally {
      setLoadingInfo(false);
    }
  };

  const handleGetStatus = async (e) => {
    e.preventDefault();
    setLoadingStatus(true);
    setErrorStatus('');
    setOntStatus('');

    try {
      const response = await axios.get(`http://localhost:5000/ont-status/${statusFormData.boardId}/${statusFormData.ontId}`, {
        withCredentials: true
      });
      
      if (response.data.status === 'success') {
        setOntStatus(response.data.data);
      } else {
        setErrorStatus(response.data.message || 'Failed to get ONT status');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setErrorStatus(err.response.data.message || 'Request failed');
      } else {
        setErrorStatus('Connection error. Please try again.');
      }
    } finally {
      setLoadingStatus(false);
    }
  };

  const handleUseOnt = (ont) => {
    console.log("Using ONT data:", ont);
    
    // Extract port ID from F/S/P format (e.g., "0/1/11" -> port = "11")
    let portId = '5'; // default
    if (ont.fsp) {
      const fspParts = ont.fsp.split('/');
      if (fspParts.length >= 3) {
        portId = fspParts[2]; // Third part is the port
        console.log("Extracted port ID:", portId);
      }
    }
    
    setFormData(prev => ({
      ...prev,
      serialNumber: ont.serialNumber || '',
      portId: portId,
      ontId: ont.number || '1'
    }));
    
    // Also update verification form
    setVerifyFormData(prev => ({
      ...prev,
      serialNumber: ont.serialNumber || '',
      portId: portId,
      ontId: ont.number || '1'
    }));
    
    console.log("Updated form data with ONT:", {
      serialNumber: ont.serialNumber,
      portId: portId,
      ontId: ont.number
    });
  };

  return (
    <div>
      {/* ONT Autofind Section */}
      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h5>ONT Autofind</h5>
        </div>
        <div className="card-body">
          <p className="text-muted">Discover automatically found ONTs on the OLT</p>
          <button 
            className="btn btn-primary"
            onClick={handleAutofind}
            disabled={loadingAutofind}
          >
            {loadingAutofind ? (
              <span className="spinner-border spinner-border-sm" role="status"></span>
            ) : (
              'Display ONT Autofind All'
            )}
          </button>

          {errorAutofind && (
            <div className="alert alert-danger mt-3">{errorAutofind}</div>
          )}

          {/* Parsed ONT Table */}
          {parsedOnts.length > 0 && (
            <div className="mt-4">
              <h6>Discovered ONTs:</h6>
              <div className="table-responsive">
                <table className="table table-bordered table-sm">
                  <thead className="thead-light">
                    <tr>
                      <th>Number</th>
                      <th>F/S/P</th>
                      <th>Serial Number</th>
                      <th>Vendor ID</th>
                      <th>Version</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsedOnts.map((ont, index) => (
                      <tr key={index}>
                        <td>{ont.number}</td>
                        <td>{ont.fsp}</td>
                        <td>
                          <code>{ont.serialNumber}</code>
                        </td>
                        <td>{ont.vendorId}</td>
                        <td>{ont.version}</td>
                        <td>
                          <button 
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => handleUseOnt(ont)}
                          >
                            Use This ONT
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Raw Output */}
          {autofindResult && (
            <div className="mt-3">
              <h6>Raw Output:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output">{autofindResult}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ONT Registration Section */}
      <div className="card mb-4">
        <div className="card-header bg-success text-white">
          <h5>ONT Registration</h5>
        </div>
        <div className="card-body">
          <form onSubmit={handleRegister}>
            <div className="row">
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>Board ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="boardId"
                    value={formData.boardId}
                    onChange={handleFormChange}
                    placeholder="0/0"
                    required
                  />
                </div>
              </div>
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>Port ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="portId"
                    value={formData.portId}
                    onChange={handleFormChange}
                    placeholder="5"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>ONT ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="ontId"
                    value={formData.ontId}
                    onChange={handleFormChange}
                    placeholder="1"
                    required
                  />
                </div>
              </div>
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>Serial Number</label>
                  <input
                    type="text"
                    className="form-control"
                    name="serialNumber"
                    value={formData.serialNumber}
                    onChange={handleFormChange}
                    placeholder="45485443BA058ED8"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>Description</label>
                  <input
                    type="text"
                    className="form-control"
                    name="description"
                    value={formData.description}
                    onChange={handleFormChange}
                    placeholder="test"
                    required
                  />
                </div>
              </div>
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>Line Profile ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="lineProfileId"
                    value={formData.lineProfileId}
                    onChange={handleFormChange}
                    placeholder="10"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label>Service Profile ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="serviceProfileId"
                    value={formData.serviceProfileId}
                    onChange={handleFormChange}
                    placeholder="10"
                    required
                  />
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              className="btn btn-success"
              disabled={loadingRegister}
            >
              {loadingRegister ? (
                <span className="spinner-border spinner-border-sm" role="status"></span>
              ) : (
                'Register ONT'
              )}
            </button>
          </form>

          {errorRegister && (
            <div className="alert alert-danger mt-3">{errorRegister}</div>
          )}

          {/* Registration Log */}
          {registrationLog && (
            <div className="mt-3">
              <h6>Registration Process Log:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output" style={{ maxHeight: '400px', overflowY: 'auto' }}>{registrationLog}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ONT Verification Section */}
      <div className="card mb-4">
        <div className="card-header bg-warning text-dark">
          <h5>ONT Verification</h5>
        </div>
        <div className="card-body">
          <form onSubmit={handleVerify}>
            <div className="row">
              <div className="col-md-3">
                <div className="form-group mb-3">
                  <label>Board ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="boardId"
                    value={verifyFormData.boardId}
                    onChange={handleVerifyFormChange}
                    placeholder="0/0"
                    required
                  />
                </div>
              </div>
              <div className="col-md-3">
                <div className="form-group mb-3">
                  <label>Port ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="portId"
                    value={verifyFormData.portId}
                    onChange={handleVerifyFormChange}
                    placeholder="5"
                    required
                  />
                </div>
              </div>
              <div className="col-md-3">
                <div className="form-group mb-3">
                  <label>ONT ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="ontId"
                    value={verifyFormData.ontId}
                    onChange={handleVerifyFormChange}
                    placeholder="1"
                    required
                  />
                </div>
              </div>
              <div className="col-md-3">
                <div className="form-group mb-3">
                  <label>Serial Number</label>
                  <input
                    type="text"
                    className="form-control"
                    name="serialNumber"
                    value={verifyFormData.serialNumber}
                    onChange={handleVerifyFormChange}
                    placeholder="45485443BA058ED8"
                    required
                  />
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              className="btn btn-warning"
              disabled={loadingVerify}
            >
              {loadingVerify ? (
                <span className="spinner-border spinner-border-sm" role="status"></span>
              ) : (
                'Verify ONT Registration'
              )}
            </button>
          </form>

          {errorVerify && (
            <div className="alert alert-danger mt-3">{errorVerify}</div>
          )}

          {/* Verification Log */}
          {verificationLog && (
            <div className="mt-3">
              <h6>Verification Results:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output" style={{ maxHeight: '400px', overflowY: 'auto' }}>{verificationLog}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ONT Info Section */}
      <div className="card mb-4">
        <div className="card-header bg-info text-white">
          <h5>ONT Information</h5>
        </div>
        <div className="card-body">
          <form onSubmit={handleGetInfo}>
            <div className="row">
              <div className="col-md-8">
                <div className="form-group mb-3">
                  <label>Description</label>
                  <input
                    type="text"
                    className="form-control"
                    name="description"
                    value={infoFormData.description}
                    onChange={handleInfoFormChange}
                    placeholder="test"
                    required
                  />
                </div>
              </div>
              <div className="col-md-4">
                <button 
                  type="submit" 
                  className="btn btn-info mt-4"
                  disabled={loadingInfo}
                >
                  {loadingInfo ? (
                    <span className="spinner-border spinner-border-sm" role="status"></span>
                  ) : (
                    'Get ONT Info'
                  )}
                </button>
              </div>
            </div>
          </form>

          {errorInfo && (
            <div className="alert alert-danger mt-3">{errorInfo}</div>
          )}

          {ontInfo && (
            <div className="mt-3">
              <h6>ONT Information:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output">{ontInfo}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ONT Status Section */}
      <div className="card">
        <div className="card-header bg-secondary text-white">
          <h5>ONT Status</h5>
        </div>
        <div className="card-body">
          <form onSubmit={handleGetStatus}>
            <div className="row">
              <div className="col-md-4">
                <div className="form-group mb-3">
                  <label>Board ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="boardId"
                    value={statusFormData.boardId}
                    onChange={handleStatusFormChange}
                    placeholder="0/0"
                    required
                  />
                </div>
              </div>
              <div className="col-md-4">
                <div className="form-group mb-3">
                  <label>ONT ID</label>
                  <input
                    type="text"
                    className="form-control"
                    name="ontId"
                    value={statusFormData.ontId}
                    onChange={handleStatusFormChange}
                    placeholder="1"
                    required
                  />
                </div>
              </div>
              <div className="col-md-4">
                <button 
                  type="submit" 
                  className="btn btn-secondary mt-4"
                  disabled={loadingStatus}
                >
                  {loadingStatus ? (
                    <span className="spinner-border spinner-border-sm" role="status"></span>
                  ) : (
                    'Get ONT Status'
                  )}
                </button>
              </div>
            </div>
          </form>

          {errorStatus && (
            <div className="alert alert-danger mt-3">{errorStatus}</div>
          )}

          {ontStatus && (
            <div className="mt-3">
              <h6>ONT Status:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output">{ontStatus}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Test Command Section */}
      <div className="card mt-4">
        <div className="card-header bg-dark text-white">
          <h5>Test Command</h5>
        </div>
        <div className="card-body">
          <form onSubmit={handleTestCommand}>
            <div className="form-group mb-3">
              <label>Command</label>
              <input
                type="text"
                className="form-control"
                name="command"
                value={testFormData.command}
                onChange={handleTestFormChange}
                placeholder="display board 0"
                required
              />
            </div>
            <button 
              type="submit" 
              className="btn btn-dark"
              disabled={loading}
            >
              {loading ? (
                <span className="spinner-border spinner-border-sm" role="status"></span>
              ) : (
                'Send Test Command'
              )}
            </button>
          </form>

          {errorTest && (
            <div className="alert alert-danger mt-3">{errorTest}</div>
          )}

          {/* Test Log */}
          {testLog && (
            <div className="mt-3">
              <h6>Test Command Output:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output" style={{ maxHeight: '400px', overflowY: 'auto' }}>{testLog}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OntRegister; 