import telnetlib
import time
import re
from enum import Enum

class OLTLoginResult(Enum):
    SUCCESS = 1
    INVALID_CREDENTIALS = 2
    TIMEOUT = 3
    CONNECTION_ERROR = 4
    LOCKOUT = 5

class OLTClient:
    def __init__(self, config):
        self.config = config
        self.tn = None
        self.logged_in = False
        
    def connect(self, username, password):
        try:
            print(f"Attempting to connect to {self.config['host']}:{self.config['port']}")
            self.tn = telnetlib.Telnet(
                self.config['host'], 
                self.config['port'], 
                timeout=self.config['timeout']
            )
            
            # Handle username prompt
            try:
                print("Waiting for username prompt...")
                self.tn.read_until(b">>User name:", timeout=3)
            except EOFError:
                print("Connection error: Could not find username prompt")
                return OLTLoginResult.CONNECTION_ERROR
                
            print(f"Sending username: {username}")
            self.tn.write(username.encode('ascii') + b"\r\n")
            
            # Handle password prompt
            try:
                print("Waiting for password prompt...")
                self.tn.read_until(b">>User password:", timeout=3)
            except EOFError:
                print("Connection error: Could not find password prompt")
                return OLTLoginResult.CONNECTION_ERROR
                
            # Send password with proper line ending and delay
            print("Sending password...")
            self.tn.write(password.encode('ascii') + b"\r\n")
            time.sleep(1)  # Increased delay after password
            
            # Wait longer for the complete login sequence
            print("Waiting for login response...")
            time.sleep(3)
            
            # Try reading multiple times to get all output
            output = ""
            for i in range(5):  # Increased attempts
                try:
                    chunk = self.tn.read_very_eager().decode('ascii', errors='ignore')
                    output += chunk
                    time.sleep(0.5)
                except:
                    break
            
            print(f"Login output received: {repr(output)}")
            
            # Check for various success indicators
            if "Username or password invalid" in output or "Invalid" in output:
                print("Login failed: Invalid credentials detected")
                return OLTLoginResult.INVALID_CREDENTIALS
            elif "Reenter times have reached the upper limit" in output:
                print("Login failed: OLT is locked due to too many failed attempts")
                return OLTLoginResult.LOCKOUT
            elif "MA5683T>" in output:
                print("Login successful: Found MA5683T prompt")
                self.logged_in = True
                return OLTLoginResult.SUCCESS
            elif "Huawei Integrated Access Software" in output and "MA5683T>" in output:
                print("Login successful: Found Huawei banner and MA5683T prompt")
                self.logged_in = True
                return OLTLoginResult.SUCCESS
            elif ">>User name:" in output and "MA5683T>" not in output:
                print("Login failed: Returned to username prompt")
                return OLTLoginResult.INVALID_CREDENTIALS
            else:
                print(f"Login failed: Unknown response - {repr(output)}")
                return OLTLoginResult.CONNECTION_ERROR
                
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return OLTLoginResult.CONNECTION_ERROR
    
    def execute_command(self, command, wait_time=1):
        if not self.logged_in:
            return "Not logged in to OLT"
            
        self.tn.write(command.encode('ascii') + b"\n")
        time.sleep(wait_time)
        output = self.tn.read_very_eager().decode('ascii')
        
        # Clean output by removing command echo
        cleaned = re.sub(r'^.*?' + re.escape(command) + r'\s*\r\n', '', output, 1)
        return cleaned.strip()
    
    def register_ont(self, sn, desc):
        if not self.logged_in:
            return "Not logged in to OLT"
            
        commands = [
            "enable",
            "config",
            f"interface gpon {self.config['board']}",
            f"ont add {self.config['board']} sn-auth {sn} omci ont-lineprofile-id 1 ont-srvprofile-id 1 desc {desc}",
            "quit",
            "quit",
            "quit"
        ]
        
        output = ""
        for cmd in commands:
            output += self.execute_command(cmd)
            
        return output
    
    def get_board_status(self):
        if not self.logged_in:
            return "Not logged in to OLT"
        return self.execute_command(f"display board {self.config['board']}", 3)
    
    def quit_olt(self):
        """Send quit command and handle confirmation"""
        print("=== QUIT_OLT METHOD CALLED ===")
        if not self.logged_in:
            print("Not logged in to OLT")
            return {"status": "error", "message": "Not logged in to OLT"}
            
        try:
            print("Sending quit command to OLT...")
            # Send quit command
            self.tn.write(b"quit\n")
            time.sleep(1)
            
            # Read the response
            output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Quit command response: {repr(output)}")
            
            # Check if confirmation is needed
            if "Y/N" in output or "y/n" in output or "yes/no" in output:
                print("Confirmation needed detected")
                return {"status": "confirmation_needed", "message": "Confirm logout?", "output": output}
            else:
                # No confirmation needed, logout successful
                print("No confirmation needed, logout successful")
                self.logged_in = False
                return {"status": "success", "message": "Logged out successfully", "output": output}
                
        except Exception as e:
            print(f"Error during quit: {str(e)}")
            return {"status": "error", "message": f"Error during logout: {str(e)}"}
    
    def confirm_quit(self, confirm=True):
        """Confirm the quit command"""
        if not self.logged_in:
            return {"status": "error", "message": "Not logged in to OLT"}
            
        try:
            # Send yes or no
            response = "Y" if confirm else "N"
            self.tn.write(response.encode('ascii') + b"\n")
            time.sleep(1)
            
            # Read the final response
            output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Confirm quit response: {repr(output)}")
            
            if confirm:
                self.logged_in = False
                return {"status": "success", "message": "Logged out successfully", "output": output}
            else:
                return {"status": "cancelled", "message": "Logout cancelled", "output": output}
                
        except Exception as e:
            print(f"Error during confirm quit: {str(e)}")
            return {"status": "error", "message": f"Error during logout confirmation: {str(e)}"}
    
    def close(self):
        if self.tn:
            try:
                self.tn.write(b"quit\n")
            except:
                pass
            self.tn.close()
        self.logged_in = False