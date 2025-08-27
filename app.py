from flask import Flask, request, jsonify, session
from flask_cors import CORS
from olt_client import OLTClient, OLTLoginResult
import config
import re
import threading
import time
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # Session lasts 8 hours
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
CORS(app, supports_credentials=True)

# Global connection pool to reuse OLT connections
olt_connections = {}
connection_lock = threading.Lock()

# Simple cache for board status to prevent too frequent requests
board_status_cache = {}
cache_lock = threading.Lock()
CACHE_DURATION = 30  # Cache for 30 seconds

def get_olt_connection(username, password):
    """Get or create an OLT connection from the pool"""
    connection_key = f"{username}_{password}"
    
    with connection_lock:
        if connection_key in olt_connections:
            conn = olt_connections[connection_key]
            # Check if connection is still valid
            try:
                # Try a simple command to test connection - use a command that doesn't require input
                test_result = conn.execute_command("display board 0/0", 1)
                if test_result and "Not logged in" not in test_result and "Error" not in test_result:
                    return conn
                else:
                    # Connection is invalid, remove it
                    del olt_connections[connection_key]
            except:
                # Connection failed, remove it
                del olt_connections[connection_key]
        
        # Create new connection
        olt = OLTClient(config.OLT_CONFIG)
        login_result = olt.connect(username, password)
        
        if login_result == OLTLoginResult.SUCCESS:
            olt_connections[connection_key] = olt
            return olt
        else:
            return None

def cleanup_connections():
    """Clean up old connections periodically"""
    while True:
        time.sleep(300)  # Clean up every 5 minutes
        with connection_lock:
            current_time = time.time()
            keys_to_remove = []
            for key, conn in olt_connections.items():
                # Remove connections older than 10 minutes
                if hasattr(conn, 'last_used') and current_time - conn.last_used > 600:
                    keys_to_remove.append(key)
                    try:
                        conn.close()
                    except:
                        pass
            
            for key in keys_to_remove:
                del olt_connections[key]

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_connections, daemon=True)
cleanup_thread.start()

def format_board_status(raw_output):
    """Parse and format board status from raw OLT output"""
    formatted = []
    in_table = False
    
    for line in raw_output.split('\n'):
        if re.match(r'^\s*(\d+/){3}\d+\s+', line):
            in_table = True
            formatted.append(line.strip())
        elif in_table and not line.strip():
            break
    
    return '\n'.join(formatted) if formatted else raw_output

def format_board_detail(raw_output):
    """Format board detail output - return complete output without filtering"""
    # Clean up the output by removing escape sequences and formatting issues
    cleaned_output = raw_output
    
    # Remove ANSI escape sequences
    import re
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    cleaned_output = ansi_escape.sub('', cleaned_output)
    
    # Remove the "More" prompts and error messages
    cleaned_output = re.sub(r'---- More \( Press \'Q\' to break \) ----.*', '', cleaned_output, flags=re.DOTALL)
    cleaned_output = re.sub(r'^\s*\^\s*$', '', cleaned_output, flags=re.MULTILINE)
    cleaned_output = re.sub(r'^\s*% Unknown command.*$', '', cleaned_output, flags=re.MULTILINE)
    cleaned_output = re.sub(r'^\s*% The error locates at.*$', '', cleaned_output, flags=re.MULTILINE)
    
    # Remove command echo and prompt
    cleaned_output = re.sub(r'^display board \d+/\d+\r?\n', '', cleaned_output, flags=re.MULTILINE)
    cleaned_output = re.sub(r'MA5683T>.*$', '', cleaned_output, flags=re.MULTILINE)
    
    # Remove any remaining command artifacts
    cleaned_output = re.sub(r'^\s*[A-Za-z0-9_]+>.*$', '', cleaned_output, flags=re.MULTILINE)
    
    # Clean up extra whitespace and empty lines, but preserve structure
    lines = cleaned_output.split('\n')
    cleaned_lines = []
    for line in lines:
        # Keep lines with content, but clean up excessive whitespace
        if line.strip():
            cleaned_lines.append(line.rstrip())
        elif cleaned_lines and cleaned_lines[-1].strip():  # Keep one empty line between sections
            cleaned_lines.append('')
    
    # Remove leading/trailing empty lines
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)

def cleanup_user_connections(username, password):
    """Clean up connections for a specific user"""
    connection_key = f"{username}_{password}"
    with connection_lock:
        if connection_key in olt_connections:
            try:
                olt_connections[connection_key].close()
            except:
                pass
            del olt_connections[connection_key]

@app.route('/olt-login', methods=['POST'])
def olt_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        response = jsonify({"status": "error", "message": "Username and password required"}), 400
        print(f"OLT Login Response: {response[0].get_json()}")
        return response
    
    olt = OLTClient(config.OLT_CONFIG)
    login_result = olt.connect(username, password)
    
    if login_result == OLTLoginResult.SUCCESS:
        # Store connection in session (in real app, use server-side session storage)
        session.permanent = True  # Make session persistent
        session['olt_credentials'] = {
            'username': username,
            'password': password
        }
        response = jsonify({"status": "success", "message": "Logged in to OLT"})
        print(f"OLT Login Response: {response.get_json()}")
        return response
    elif login_result == OLTLoginResult.INVALID_CREDENTIALS:
        response = jsonify({"status": "error", "message": "Invalid username or password"}), 401
        print(f"OLT Login Response: {response[0].get_json()}")
        return response
    elif login_result == OLTLoginResult.LOCKOUT:
        response = jsonify({"status": "error", "message": "OLT is temporarily locked due to too many failed login attempts. Please wait 15-30 minutes and try again."}), 423
        print(f"OLT Login Response: {response[0].get_json()}")
        return response
    elif login_result == OLTLoginResult.TIMEOUT:
        response = jsonify({"status": "error", "message": "Login timed out"}), 408
        print(f"OLT Login Response: {response[0].get_json()}")
        return response
    else:
        response = jsonify({"status": "error", "message": "Connection failed"}), 500
        print(f"OLT Login Response: {response[0].get_json()}")
        return response

@app.route('/register-ont', methods=['POST'])
def register_ont():
    # Check if logged in
    if 'olt_credentials' not in session:
        response = jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        print(f"Register ONT Response: {response[0].get_json()}")
        return response
        
    data = request.json
    credentials = session['olt_credentials']
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        response = jsonify({"status": "error", "message": "OLT login expired"}), 401
        print(f"Register ONT Response: {response[0].get_json()}")
        return response
    
    try:
        olt.mark_used()  # Mark connection as used
        result = olt.register_ont(data['sn'], data['description'])
        response = jsonify({"status": "success", "output": result})
        print(f"Register ONT Response: {response.get_json()}")
        return response
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)})
        print(f"Register ONT Response: {response.get_json()}")
        return response

@app.route('/board-status', methods=['GET'])
def board_status():
    # Check if logged in
    if 'olt_credentials' not in session:
        response = jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        print(f"Board Status Response: {response[0].get_json()}")
        return response
        
    credentials = session['olt_credentials']
    cache_key = f"{credentials['username']}_{credentials['password']}"
    
    # Check cache first
    current_time = time.time()
    with cache_lock:
        if cache_key in board_status_cache:
            cached_data, cache_time = board_status_cache[cache_key]
            if current_time - cache_time < CACHE_DURATION:
                print("Returning cached board status")
                response = jsonify({"status": "success", "data": cached_data})
                return response
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        response = jsonify({"status": "error", "message": "OLT login expired"}), 401
        print(f"Board Status Response: {response[0].get_json()}")
        return response
    
    try:
        olt.mark_used()  # Mark connection as used
        raw_status = olt.get_board_status()
        formatted = format_board_status(raw_status)
        
        # Cache the result
        with cache_lock:
            board_status_cache[cache_key] = (formatted, current_time)
        
        response = jsonify({"status": "success", "data": formatted})
        print(f"Board Status Response: {response.get_json()}")
        return response
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)})
        print(f"Board Status Response: {response.get_json()}")
        return response

@app.route('/olt-logout', methods=['POST'])
def olt_logout():
    session.pop('olt_credentials', None)
    response = jsonify({"status": "success", "message": "Logged out from OLT"})
    print(f"OLT Logout Response: {response.get_json()}")
    return response

@app.route('/olt-quit', methods=['POST'])
def olt_quit():
    print("=== OLT QUIT ENDPOINT CALLED ===")
    # Check if logged in
    if 'olt_credentials' not in session:
        print("No OLT credentials in session")
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    # Clean up connections for this user
    credentials = session['olt_credentials']
    cleanup_user_connections(credentials['username'], credentials['password'])
    
    # Clear the session
    session.pop('olt_credentials', None)
    print("Session cleared - logged out from OLT")
    
    response = jsonify({"status": "success", "message": "Logged out successfully"})
    print(f"OLT Quit Response: {response.get_json()}")
    return response

@app.route('/all-boards', methods=['GET'])
def all_boards():
    """Get output of 'display board 0' command"""
    print("=== ALL BOARDS ENDPOINT CALLED ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    credentials = session['olt_credentials']
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        raw_status = olt.get_all_boards()
        print(f"All Boards Response: {raw_status}")
        return jsonify({"status": "success", "data": raw_status})
    except Exception as e:
        print(f"All Boards Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/board-detail/<path:board_id>', methods=['GET'])
def board_detail(board_id):
    """Get detailed status for a specific board"""
    print(f"=== BOARD DETAIL ENDPOINT CALLED for {board_id} ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    credentials = session['olt_credentials']
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        raw_status = olt.get_board_detail(board_id)
        formatted = format_board_detail(raw_status)
        print(f"Board Detail Response for {board_id}: {formatted}")
        return jsonify({"status": "success", "data": formatted, "board_id": board_id})
    except Exception as e:
        print(f"Board Detail Error for {board_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/ont-autofind', methods=['GET'])
def ont_autofind():
    """Display all automatically found ONTs"""
    print("=== ONT AUTOFIND ENDPOINT CALLED ===")
    if 'olt_credentials' not in session:
        print("No OLT credentials in session")
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    credentials = session['olt_credentials']
    print(f"Using credentials for user: {credentials['username']}")
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        print("Failed to get OLT connection")
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        print("Calling display_ont_autofind_simple() with correct command...")
        olt.mark_used()  # Mark connection as used
        result = olt.display_ont_autofind_simple()
        print(f"ONT Autofind result: {repr(result)}")
        print(f"ONT Autofind result length: {len(result) if result else 0}")
        
        if not result or result.strip() == "":
            print("Empty result received")
            return jsonify({"status": "error", "message": "No output received from OLT"})
        
        response = jsonify({"status": "success", "data": result})
        print(f"ONT Autofind Response: {response.get_json()}")
        return response
        
    except Exception as e:
        print(f"ONT Autofind Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/ont-register', methods=['POST'])
def ont_register():
    """Register an ONT using the complete flow with detailed logging"""
    print("=== ONT REGISTER ENDPOINT CALLED ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    data = request.json
    credentials = session['olt_credentials']
    
    # Validate required fields
    required_fields = ['boardId', 'portId', 'ontId', 'serialNumber']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        
        # Extract parameters with defaults
        board_id = data.get('boardId', '0/0')
        port_id = data.get('portId', '5')
        ont_id = data.get('ontId', '1')
        serial_number = data.get('serialNumber')
        description = data.get('description', 'test')
        line_profile_id = data.get('lineProfileId', '10')
        service_profile_id = data.get('serviceProfileId', '10')
        
        print(f"Starting ONT registration: Board={board_id}, Port={port_id}, ONT={ont_id}, SN={serial_number}")
        
        result = olt.register_ont_complete(
            board_id=board_id,
            port_id=port_id,
            ont_id=ont_id,
            serial_number=serial_number,
            description=description,
            line_profile_id=line_profile_id,
            service_profile_id=service_profile_id
        )
        
        print(f"ONT Register Response: {result}")
        
        # Check if registration was successful
        if "❌" in result or "Failed" in result:
            return jsonify({"status": "error", "data": result, "message": "ONT registration failed"})
        else:
            return jsonify({"status": "success", "data": result, "message": "ONT registration completed"})
            
    except Exception as e:
        print(f"ONT Register Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/ont-verify', methods=['POST'])
def ont_verify():
    """Verify ONT registration"""
    print("=== ONT VERIFY ENDPOINT CALLED ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    data = request.json
    credentials = session['olt_credentials']
    
    # Validate required fields
    required_fields = ['boardId', 'portId', 'ontId', 'serialNumber']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        
        # Extract parameters
        board_id = data.get('boardId')
        port_id = data.get('portId')
        ont_id = data.get('ontId')
        serial_number = data.get('serialNumber')
        
        print(f"Verifying ONT: Board={board_id}, Port={port_id}, ONT={ont_id}, SN={serial_number}")
        
        result = olt.verify_ont_registration(
            board_id=board_id,
            port_id=port_id,
            ont_id=ont_id,
            serial_number=serial_number
        )
        
        print(f"ONT Verify Response: {result}")
        return jsonify({"status": "success", "data": result})
        
    except Exception as e:
        print(f"ONT Verify Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/ont-info/<path:description>', methods=['GET'])
def ont_info(description):
    """Get ONT information by description"""
    print(f"=== ONT INFO ENDPOINT CALLED for {description} ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    credentials = session['olt_credentials']
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        result = olt.display_ont_info_by_desc(description)
        print(f"ONT Info Response for {description}: {result}")
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        print(f"ONT Info Error for {description}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/ont-status/<path:board_id>/<path:ont_id>', methods=['GET'])
def ont_status(board_id, ont_id):
    """Get ONT status information"""
    print(f"=== ONT STATUS ENDPOINT CALLED for {board_id}/{ont_id} ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    credentials = session['olt_credentials']
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        result = olt.get_ont_status(board_id, ont_id)
        print(f"ONT Status Response for {board_id}/{ont_id}: {result}")
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        print(f"ONT Status Error for {board_id}/{ont_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/check-session', methods=['GET'])
def check_session():
    """Check if user is currently logged in"""
    if 'olt_credentials' in session:
        return jsonify({"status": "success", "logged_in": True})
    else:
        return jsonify({"status": "success", "logged_in": False})

@app.route('/test-command', methods=['POST'])
def test_command():
    """Test command sending to OLT"""
    print("=== TEST COMMAND ENDPOINT CALLED ===")
    if 'olt_credentials' not in session:
        return jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        
    data = request.json
    credentials = session['olt_credentials']
    
    if 'command' not in data:
        return jsonify({"status": "error", "message": "Command parameter required"}), 400
    
    # Get connection from pool
    olt = get_olt_connection(credentials['username'], credentials['password'])
    
    if not olt:
        return jsonify({"status": "error", "message": "OLT login expired"}), 401
    
    try:
        olt.mark_used()  # Mark connection as used
        command = data['command']
        print(f"Testing command: {command}")
        
        result = olt.test_command_sending(command)
        print(f"Test command result: {result}")
        return jsonify({"status": "success", "data": result})
        
    except Exception as e:
        print(f"Test command error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)