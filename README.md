# ONT Registration System for MA5683T OLT

A complete ONT (Optical Network Terminal) registration system for Huawei MA5683T OLT devices with web-based interface and detailed logging.

## Features

- 🔍 **ONT Discovery**: Automatic discovery of ONTs using autofind
- 📝 **ONT Registration**: Complete registration flow with validation
- ✅ **Verification**: Post-registration verification and status checking
- 📊 **Real-time Monitoring**: Board status and ONT information
- 🔐 **Secure Authentication**: Session-based OLT login
- 📋 **Detailed Logging**: Step-by-step process logging
- 🎯 **User-friendly Interface**: Modern React-based web interface

## System Requirements

- Python 3.8+
- Node.js 14+
- Access to MA5683T OLT device
- Network connectivity to OLT

## Installation

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OLT-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install flask flask-cors flask-sqlalchemy paramiko
   ```

4. **Configure OLT settings**
   Edit `config.py` with your OLT details:
   ```python
   OLT_CONFIG = {
       "host": "your_olt_ip",
       "port": 3212,
       "board": "0/0",
       "prompt": "MA5683T>",
       "timeout": 10
   }
   ```

5. **Start the backend server**
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the frontend development server**
   ```bash
   npm start
   ```
   The web interface will be available at `http://localhost:3000`

## Usage

### 1. Login to OLT
- Open the web interface
- Enter your OLT credentials
- Click "Login to OLT"

### 2. ONT Discovery
- Navigate to "ONT Registration" tab
- Click "Display ONT Autofind All"
- Review discovered ONTs
- Click "Use This ONT" to auto-fill registration form

### 3. ONT Registration
- Fill in registration parameters:
  - Board ID: e.g., "0/0"
  - Port ID: 1-16
  - ONT ID: 1-128
  - Serial Number: ONT serial number
  - Description: ONT description
- Click "Register ONT"
- Review registration log

### 4. Verification
- Use the verification form with same parameters
- Click "Verify ONT Registration"
- Review verification results

## API Endpoints

### Authentication
- `POST /olt-login` - Login to OLT
- `POST /olt-logout` - Logout from OLT
- `POST /olt-quit` - Quit OLT session

### ONT Operations
- `GET /ont-autofind` - Discover ONTs
- `POST /ont-register` - Register ONT
- `POST /ont-verify` - Verify ONT registration
- `GET /ont-info/{description}` - Get ONT info
- `GET /ont-status/{board_id}/{ont_id}` - Get ONT status

### Board Operations
- `GET /all-boards` - Get all boards
- `GET /board-detail/{board_id}` - Get board details
- `GET /board-status` - Get board status

## Configuration

### OLT Configuration
Edit `config.py` to match your OLT setup:

```python
OLT_CONFIG = {
    "host": "103.160.82.34",  # Your OLT IP address
    "port": 3212,             # Telnet port
    "board": "0/0",           # Default board
    "prompt": "MA5683T>",     # OLT prompt
    "timeout": 10             # Connection timeout
}
```

### Validation Rules
- **Board ID**: Format `X/Y` (e.g., 0/0, 0/1)
- **Port ID**: 1-16
- **ONT ID**: 1-128
- **Serial Number**: Minimum 8 characters
- **Description**: Any text string

## Testing

Run the test suite to verify system functionality:

```bash
python test_ont_registration.py
```

**Note**: Update the test credentials in the script before running.

## Troubleshooting

### Common Issues

1. **"Not logged in to OLT"**
   - Ensure you're logged in to the OLT
   - Check session status

2. **"Connection timeout"**
   - Verify OLT network connectivity
   - Check firewall settings
   - Confirm OLT is operational

3. **"Invalid board format"**
   - Use correct format: X/Y (e.g., 0/0)
   - Check board ID validation

4. **"ONT registration failed"**
   - Verify serial number format
   - Check if ONT ID is already in use
   - Review detailed error log

### Debug Information
- All API calls are logged in backend console
- Frontend shows detailed error messages
- Registration logs provide step-by-step information
- Verification results show detailed status

## Security Considerations

- Session-based authentication
- Input validation on frontend and backend
- Secure error handling
- Connection pooling and cleanup
- Timeout mechanisms

## Performance Features

- Connection pooling for OLT sessions
- Board status caching (30 seconds)
- Efficient output parsing
- Automatic resource cleanup
- Non-blocking API operations

## File Structure

```
OLT-backend/
├── app.py                 # Flask API server
├── olt_client.py         # OLT telnet client
├── config.py             # Configuration settings
├── test_ont_registration.py  # Test suite
├── ONT_REGISTRATION_GUIDE.md # Detailed guide
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js
│   │   │   ├── OntRegister.js
│   │   │   ├── BoardExplorer.js
│   │   │   └── BoardStatus.js
│   │   └── App.js
│   └── package.json
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the detailed guide in `ONT_REGISTRATION_GUIDE.md`
- Run the test suite to verify functionality
- Check backend console logs for detailed error information

## Changelog

### Version 1.0.0
- Initial release
- Complete ONT registration system
- Web-based interface
- Detailed logging and verification
- Board management features
