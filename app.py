from flask import Flask, request, jsonify, session
from flask_cors import CORS
from olt_client import OLTClient, OLTLoginResult
import config
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production
CORS(app, supports_credentials=True)

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
    
    olt = OLTClient(config.OLT_CONFIG)
    login_result = olt.connect(credentials['username'], credentials['password'])
    
    if login_result != OLTLoginResult.SUCCESS:
        response = jsonify({"status": "error", "message": "OLT login expired"}), 401
        print(f"Register ONT Response: {response[0].get_json()}")
        return response
    
    try:
        result = olt.register_ont(data['sn'], data['description'])
        response = jsonify({"status": "success", "output": result})
        print(f"Register ONT Response: {response.get_json()}")
        return response
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)})
        print(f"Register ONT Response: {response.get_json()}")
        return response
    finally:
        olt.close()

@app.route('/board-status', methods=['GET'])
def board_status():
    # Check if logged in
    if 'olt_credentials' not in session:
        response = jsonify({"status": "error", "message": "Not logged in to OLT"}), 401
        print(f"Board Status Response: {response[0].get_json()}")
        return response
        
    credentials = session['olt_credentials']
    
    olt = OLTClient(config.OLT_CONFIG)
    login_result = olt.connect(credentials['username'], credentials['password'])
    
    if login_result != OLTLoginResult.SUCCESS:
        response = jsonify({"status": "error", "message": "OLT login expired"}), 401
        print(f"Board Status Response: {response[0].get_json()}")
        return response
    
    try:
        raw_status = olt.get_board_status()
        formatted = format_board_status(raw_status)
        response = jsonify({"status": "success", "data": formatted})
        print(f"Board Status Response: {response.get_json()}")
        return response
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)})
        print(f"Board Status Response: {response.get_json()}")
        return response
    finally:
        olt.close()

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
        
    # For now, let's just clear the session and logout
    # The OLT will automatically logout inactive sessions
    session.pop('olt_credentials', None)
    print("Session cleared - logged out from OLT")
    
    response = jsonify({"status": "success", "message": "Logged out successfully"})
    print(f"OLT Quit Response: {response.get_json()}")
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)