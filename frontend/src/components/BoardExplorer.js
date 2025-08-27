import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BoardExplorer = () => {
  const [allBoards, setAllBoards] = useState('');
  const [boardId, setBoardId] = useState('');
  const [boardDetail, setBoardDetail] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState('');
  const [errorDetail, setErrorDetail] = useState('');
  const [availableBoards, setAvailableBoards] = useState([]);
  const [boardData, setBoardData] = useState([]);

  // Parse board data from the raw output
  const parseBoardData = (output) => {
    const lines = output.split('\n');
    const boardList = [];
    
    for (const line of lines) {
      // Match lines that contain board information
      const match = line.match(/^\s*(\d+)\s+(\S+)\s+(\S+)/);
      if (match) {
        const slotId = match[1];
        const boardName = match[2];
        const status = match[3];
        
        if (boardName && boardName !== '-') {
          boardList.push({
            slotId,
            boardName,
            status,
            boardId: `0/${slotId}`
          });
        }
      }
    }
    
    return boardList;
  };

  // Fetch all boards on component mount
  useEffect(() => {
    const fetchAllBoards = async () => {
      try {
        const response = await axios.get('http://localhost:5000/all-boards', {
          withCredentials: true
        });
        
        if (response.data.status === 'success') {
          setAllBoards(response.data.data);
          
          // Parse board data and set available boards
          const parsedData = parseBoardData(response.data.data);
          setBoardData(parsedData);
          
          if (parsedData.length > 0) {
            setAvailableBoards(parsedData.map(b => b.boardId));
            setBoardId(parsedData[0].boardId);
          }
        } else {
          setError(response.data.message || 'Failed to get board information');
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
    
    fetchAllBoards();
  }, []);

  const fetchBoardDetail = async () => {
    if (!boardId) return;

    setLoadingDetail(true);
    setErrorDetail('');
    setBoardDetail(''); // Clear previous detail

    try {
      const response = await axios.get(`http://localhost:5000/board-detail/${boardId}`, {
        withCredentials: true
      });
      
      if (response.data.status === 'success') {
        setBoardDetail(response.data.data);
      } else {
        setErrorDetail(response.data.message || 'Failed to get board detail');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setErrorDetail(err.response.data.message || 'Request failed');
      } else {
        setErrorDetail('Connection error. Please try again.');
      }
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleBoardChange = (e) => {
    setBoardId(e.target.value);
  };

  return (
    <div>
      <div className="card mb-4">
        <div className="card-header bg-info text-white">
          <h5>All Boards (display board 0)</h5>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="text-center">
              <div className="spinner-border text-primary"></div>
              <p>Loading board information...</p>
            </div>
          ) : error ? (
            <div className="alert alert-danger">{error}</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-bordered table-sm">
                <thead className="thead-light">
                  <tr>
                    <th>Slot ID</th>
                    <th>Board Name</th>
                    <th>Status</th>
                    <th>Board ID</th>
                  </tr>
                </thead>
                <tbody>
                  {boardData.map(board => (
                    <tr key={board.boardId}>
                      <td>{board.slotId}</td>
                      <td>{board.boardName}</td>
                      <td>{board.status}</td>
                      <td>{board.boardId}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header bg-info text-white">
          <h5>Board Detail Explorer</h5>
        </div>
        <div className="card-body">
          <div className="form-group">
            <label>Select Board</label>
            <div className="d-flex gap-2 mb-3">
              <select 
                className="form-control"
                value={boardId}
                onChange={handleBoardChange}
                disabled={loading || availableBoards.length === 0}
              >
                {availableBoards.map(board => (
                  <option key={board} value={board}>
                    {board}
                  </option>
                ))}
              </select>
              <button 
                className="btn btn-primary"
                onClick={fetchBoardDetail}
                disabled={!boardId || loadingDetail}
              >
                {loadingDetail ? (
                  <span className="spinner-border spinner-border-sm" role="status"></span>
                ) : (
                  'Fetch Detail'
                )}
              </button>
            </div>
          </div>

          {errorDetail && (
            <div className="alert alert-danger">{errorDetail}</div>
          )}

          {boardDetail && (
            <div className="mt-3">
              <h6>Board {boardId} Detail:</h6>
              <div className="card">
                <div className="card-body">
                  <pre className="olt-output">{boardDetail}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BoardExplorer;