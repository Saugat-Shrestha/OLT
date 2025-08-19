import React from 'react';
import BoardStatus from './BoardStatus';
import OntRegister from './OntRegister';

const Dashboard = () => {
  return (
    <div className="container mt-3">
      <div className="row">
        <div className="col-md-6">
          <BoardStatus />
        </div>
        <div className="col-md-6">
          <OntRegister />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;