# ONT Registration System - Complete Guide

## Overview

This system provides a complete ONT (Optical Network Terminal) registration solution for MA5683T OLT devices. It includes both backend API endpoints and a frontend interface for managing ONT registrations with detailed logging and verification capabilities.

## System Architecture

### Backend Components
- **Flask API** (`app.py`): RESTful API endpoints for OLT operations
- **OLT Client** (`olt_client.py`): Telnet client for MA5683T communication
- **Configuration** (`config.py`): OLT connection settings

### Frontend Components
- **React Dashboard** (`Dashboard.js`): Main application interface
- **ONT Register** (`OntRegister.js`): Complete ONT registration interface
- **Board Explorer** (`BoardExplorer.js`): Board status and management
- **Board Status** (`BoardStatus.js`): Real-time board monitoring

## ONT Registration Flow

### 1. ONT Discovery (Autofind)
```
Command: display ont autofind all
Purpose: Discover automatically found ONTs on the OLT
Location: GPON interface context
```

### 2. ONT Registration Process
The registration follows these steps:

#### Step 1: Enter Enable Mode
```
Command: enable
Purpose: Enter privileged enable mode
```

#### Step 2: Enter Configuration Mode
```
Command: config
Purpose: Enter system configuration mode
```

#### Step 3: Configure GPON Interface
```
Command: interface gpon {board_id}
Purpose: Enter GPON interface configuration context
Example: interface gpon 0/0
```

#### Step 4: Add ONT
```
Command: ont add {port_id} {ont_id} sn-auth {serial_number} omci ont-lineprofile-id {line_profile_id} ont-srvprofile-id {service_profile_id} desc {description}
Purpose: Register ONT with specified parameters
Example: ont add 5 1 sn-auth 45485443BA058ED8 omci ont-lineprofile-id 10 ont-srvprofile-id 10 desc test
```

#### Step 5: Exit Configuration Mode
```
Command: quit (multiple times)
Purpose: Exit configuration mode and return to main prompt
Note: Multiple quits needed: config -> enable -> main prompt
```

#### Step 6: Verification
```
Command: display ont info {ont_id}
Purpose: Verify ONT registration and get status information
```

## API Endpoints

### Authentication
- `POST /olt-login`: Login to OLT
- `POST /olt-logout`: Logout from OLT
- `POST /olt-quit`: Quit OLT session

### ONT Operations
- `GET /ont-autofind`: Discover automatically found ONTs
- `POST /ont-register`: Register a new ONT
- `POST /ont-verify`: Verify ONT registration
- `GET /ont-info/{description}`: Get ONT information by description
- `GET /ont-status/{board_id}/{ont_id}`: Get ONT status

### Board Operations
- `GET /all-boards`: Get all board information
- `GET /board-detail/{board_id}`: Get detailed board status
- `GET /board-status`: Get current board status

## Frontend Features

### 1. ONT Autofind
- Automatic discovery of ONTs
- Parsed display of ONT information
- Auto-fill registration forms with discovered data

### 2. ONT Registration
- Complete registration form with validation
- Real-time progress logging
- Step-by-step process display
- Error handling and user feedback

### 3. ONT Verification
- Post-registration verification
- Status checking
- Detailed verification logs

### 4. ONT Management
- Status monitoring
- Information retrieval
- Board exploration

## Configuration

### OLT Configuration (`config.py`)
```python
OLT_CONFIG = {
    "host": "103.160.82.34",
    "port": 3212,
    "board": "0/0",
    "prompt": "MA5683T>",
    "timeout": 10
}
```

### Validation Rules
- **Board ID**: Format `X/Y` (e.g., 0/0, 0/1)
- **Port ID**: 1-16
- **ONT ID**: 1-128
- **Serial Number**: Minimum 8 characters
- **Description**: Any text string

## Error Handling

### Common Error Scenarios
1. **Invalid Credentials**: OLT login failed
2. **Connection Timeout**: Network or OLT unresponsive
3. **Invalid Parameters**: Incorrect board/port/ONT IDs
4. **ONT Already Exists**: Duplicate registration attempt
5. **Configuration Errors**: Invalid command syntax

### Error Response Format
```json
{
  "status": "error",
  "message": "Error description",
  "data": "Detailed error log"
}
```

## Logging and Monitoring

### Registration Log Format
```
=== ONT Registration Process Started ===
Board ID: 0/0
Port ID: 5
ONT ID: 1
Serial Number: 45485443BA058ED8
Description: test
Line Profile ID: 10
Service Profile ID: 10

Step 1: Entering enable mode...
✅ Enable mode entered successfully
Step 2: Entering configuration mode...
✅ Config mode entered successfully
Step 3: Configuring GPON interface 0/0...
✅ GPON interface 0/0 configured successfully
Step 4: Adding ONT 1 on port 5...
Executing command: ont add 5 1 sn-auth 45485443BA058ED8 omci ont-lineprofile-id 10 ont-srvprofile-id 10 desc test
✅ ONT 1 registered successfully on port 5
Step 5: Exiting configuration mode...
✅ Configuration mode exited successfully
Step 6: Verifying ONT registration...
✅ ONT verification successful

=== ONT Registration Process Completed ===
```

### Verification Log Format
```
=== ONT Registration Verification ===
✅ ONT status retrieved successfully
✅ Serial number 45485443BA058ED8 found in ONT status
✅ Port 5 information found in ONT status

ONT Status Details:
[Detailed ONT status output]

=== Verification Completed ===
```

## Usage Examples

### 1. Basic ONT Registration
1. Login to OLT
2. Navigate to "ONT Registration" tab
3. Fill in registration form:
   - Board ID: 0/0
   - Port ID: 5
   - ONT ID: 1
   - Serial Number: 45485443BA058ED8
   - Description: test
4. Click "Register ONT"
5. Review registration log
6. Verify registration using "ONT Verification" section

### 2. Using Autofind
1. Click "Display ONT Autofind All"
2. Review discovered ONTs
3. Click "Use This ONT" for desired ONT
4. Forms auto-fill with ONT data
5. Adjust parameters if needed
6. Proceed with registration

### 3. Verification Process
1. After registration, use verification form
2. Enter same parameters used for registration
3. Click "Verify ONT Registration"
4. Review verification results
5. Check ONT status for additional details

## Troubleshooting

### Common Issues

1. **"Not logged in to OLT"**
   - Solution: Login to OLT first
   - Check session status

2. **"Invalid board format"**
   - Solution: Use format X/Y (e.g., 0/0, 0/1)
   - Check board ID validation

3. **"ONT registration failed"**
   - Check serial number format
   - Verify ONT ID is not already in use
   - Review detailed error log

4. **"Connection timeout"**
   - Check OLT network connectivity
   - Verify OLT is operational
   - Check firewall settings

### Debug Information
- All API calls are logged in backend console
- Frontend shows detailed error messages
- Registration logs provide step-by-step information
- Verification results show detailed status

## Security Considerations

1. **Session Management**: Secure session handling with cookies
2. **Input Validation**: All inputs validated on both frontend and backend
3. **Error Handling**: No sensitive information exposed in error messages
4. **Connection Pooling**: Efficient connection management
5. **Timeout Handling**: Proper timeout and cleanup mechanisms

## Performance Optimization

1. **Connection Pooling**: Reuse OLT connections
2. **Caching**: Board status caching for 30 seconds
3. **Async Operations**: Non-blocking API calls
4. **Efficient Parsing**: Optimized output parsing
5. **Resource Cleanup**: Automatic connection cleanup

## Future Enhancements

1. **Bulk Operations**: Register multiple ONTs at once
2. **Scheduled Tasks**: Automated ONT management
3. **Advanced Monitoring**: Real-time ONT status monitoring
4. **Configuration Templates**: Predefined ONT configurations
5. **Audit Logging**: Complete operation audit trail 