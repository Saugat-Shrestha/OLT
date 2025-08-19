import React, { useState } from 'react';
import BoardStatus from './BoardStatus';
import OntRegister from '../ontregister';
import OLTLogout from './OLTLogout';

const Dashboard = ({ isOLTLoggedIn, handleLogout }) => {
  const [activeTab, setActiveTab] = useState('status');
  
  if (!isOLTLoggedIn) {
    return (
      <div className="container mt-5">
        <div className="alert alert-warning">
          Please login to the OLT first
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-3">
      <OLTLogout handleLogout={handleLogout} />
      
      <ul className="nav nav-tabs mb-3">
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'status' ? 'active' : ''}`}
            onClick={() => setActiveTab('status')}
          >
            Board Status
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'register' ? 'active' : ''}`}
            onClick={() => setActiveTab('register')}
          >
            ONT Registration
          </button>
        </li>
      </ul>
      
      <div className="tab-content">
        {activeTab === 'status' && <BoardStatus />}
        {activeTab === 'register' && <OntRegister />}
      </div>
    </div>
  );
};

export default Dashboard;