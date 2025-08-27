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
        self.last_used = time.time()
        
    def mark_used(self):
        """Mark the connection as recently used"""
        self.last_used = time.time()
        
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
        
        try:
            # Clear any leftover text in the buffer first
            print("Clearing buffer...")
            self.tn.read_very_eager()
            time.sleep(0.5)
            
            # Wait for the prompt to ensure we're ready
            try:
                self.tn.read_until(b"MA5683T>", timeout=2)
            except:
                pass  # If no prompt found, continue anyway
            
            # Send the command with proper line ending
            print(f"Sending command: '{command}'")
            self.tn.write(command.encode('ascii') + b"\r\n")
            time.sleep(wait_time)
            
            # Read the output
            output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Raw output: {repr(output)}")
            
            # Check if we got a prompt asking for input (like display version)
            if "{" in output and "}" in output and ":" in output:
                # Send Enter to continue
                print("Sending Enter to continue...")
                self.tn.write(b"\r\n")
                time.sleep(1)
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                output += additional_output
                print(f"Additional output: {repr(additional_output)}")
            
            # Clean output by removing command echo and prompt
            lines = output.split('\r\n')
            cleaned_lines = []
            command_found = False
            
            for line in lines:
                if not command_found and command.strip() in line:
                    command_found = True
                    continue
                if line.strip() and not line.strip().startswith('MA5683T>'):
                    cleaned_lines.append(line)
            
            cleaned_output = '\n'.join(cleaned_lines)
            print(f"Cleaned output: {repr(cleaned_output)}")
            return cleaned_output.strip()
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def register_ont(self, sn, desc):
        """Legacy ONT registration method - kept for backward compatibility"""
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

    def register_ont_complete(self, board_id, port_id, ont_id, serial_number, description="test", line_profile_id=10, service_profile_id=10):
        """Complete ONT registration flow with detailed logging"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Validate inputs
        if not re.match(r'^\d+/\d+$', board_id):
            return "Invalid board format. Use format like '0/0'"
        
        if not serial_number or len(serial_number) < 8:
            return "Invalid serial number. Must be at least 8 characters."
        
        if not ont_id.isdigit() or int(ont_id) < 1 or int(ont_id) > 128:
            return "Invalid ONT ID. Must be between 1 and 128."
        
        if not port_id.isdigit() or int(port_id) < 1 or int(port_id) > 16:
            return "Invalid Port ID. Must be between 1 and 16."
        
        results = []
        results.append("=== ONT Registration Process Started ===")
        results.append(f"Board ID: {board_id}")
        results.append(f"Port ID: {port_id}")
        results.append(f"ONT ID: {ont_id}")
        results.append(f"Serial Number: {serial_number}")
        results.append(f"Description: {description}")
        results.append(f"Line Profile ID: {line_profile_id}")
        results.append(f"Service Profile ID: {service_profile_id}")
        results.append("")
        
        try:
            # Step 1: Check current mode and enter enable mode if needed
            results.append("Step 1: Checking current mode and entering enable mode...")
            
            # Clear any existing output
            self.tn.read_very_eager()
            time.sleep(1)
            
            # Send a simple command to check current prompt
            self.tn.write(b"\r\n")
            time.sleep(1)
            current_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Current prompt check: {repr(current_output)}")
            
            # Check if we're already in enable mode
            if "MA5683T#" in current_output:
                results.append("✅ Already in enable mode")
                enable_result = "Already in enable mode"
            else:
                # Enter enable mode
                self.tn.write(b"enable\r\n")
                time.sleep(2)
                enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                if "Error" in enable_output or "Unknown command" in enable_output:
                    results.append(f"❌ Failed to enter enable mode: {enable_output}")
                    return "\n".join(results)
                results.append("✅ Entered enable mode successfully")
                enable_result = enable_output
            
            # Step 2: Enter config mode
            results.append("Step 2: Entering configuration mode...")
            self.tn.write(b"config\r\n")
            time.sleep(2)
            config_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            if "Error" in config_output or "Unknown command" in config_output:
                results.append(f"❌ Failed to enter config mode: {config_output}")
                return "\n".join(results)
            results.append("✅ Entered configuration mode successfully")
            
            # Step 3: Configure GPON interface
            results.append(f"Step 3: Configuring GPON interface {board_id}...")
            gpon_command = f"interface gpon {board_id}"
            self.tn.write(gpon_command.encode('ascii') + b"\r\n")
            time.sleep(2)
            gpon_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            if "Error" in gpon_output or "Unknown command" in gpon_output:
                results.append(f"❌ Failed to configure GPON interface: {gpon_output}")
                return "\n".join(results)
            results.append(f"✅ GPON interface {board_id} configured successfully")
            
            # Step 4: Add ONT with proper MA5683T command format
            results.append(f"Step 4: Adding ONT {ont_id} on port {port_id}...")
            
            # Correct MA5683T ONT add command format
            command = f"ont add {port_id} {ont_id} sn-auth {serial_number} omci ont-lineprofile-id {line_profile_id} ont-srvprofile-id {service_profile_id} desc {description}"
            results.append(f"Executing command: {command}")
            
            self.tn.write(command.encode('ascii') + b"\r\n")
            time.sleep(5)  # Increased wait time for ONT registration
            
            # Read the output
            ont_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            results.append(f"Command output: {ont_output}")
            
            # Check for success indicators
            if "Error" in ont_output or "Unknown command" in ont_output or "Failed" in ont_output:
                results.append(f"❌ ONT registration failed: {ont_output}")
                return "\n".join(results)
            elif "successfully" in ont_output.lower() or "ok" in ont_output.lower():
                results.append(f"✅ ONT {ont_id} registered successfully on port {port_id}")
            else:
                results.append(f"⚠️ ONT registration completed (check output for details)")
            
            # Step 5: Exit config mode (multiple quits to get back to main prompt)
            results.append("Step 5: Exiting configuration mode...")
            for i in range(4):  # Usually need 4 quits to get back to main prompt
                self.tn.write(b"quit\r\n")
                time.sleep(1)
                quit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                results.append(f"Exit {i+1}: {quit_output}")
                
                # Check if we're back to main prompt
                if "MA5683T>" in quit_output:
                    results.append("✅ Back to main prompt")
                    break
            
            # Step 6: Verify ONT registration
            results.append("Step 6: Verifying ONT registration...")
            verification_result = self.verify_ont_registration(board_id, port_id, ont_id, serial_number)
            if verification_result and "SUCCESS" in verification_result:
                results.append("✅ ONT verification successful")
                results.append("🎉 ONT registration and verification completed successfully!")
            else:
                results.append("⚠️ ONT verification failed or incomplete")
                results.append("Note: ONT may be registered but verification failed")
            
            results.append("")
            results.append("=== ONT Registration Process Completed ===")
            
        except Exception as e:
            results.append(f"❌ Registration process failed with exception: {str(e)}")
            results.append("=== ONT Registration Process Failed ===")
        
        return "\n".join(results)

    def verify_ont_registration(self, board_id, port_id, ont_id, serial_number):
        """Verify ONT registration by checking if the ONT exists with correct details"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Validate inputs
        if not re.match(r'^\d+/\d+$', board_id):
            return "Invalid board format. Use format like '0/0'"
        
        results = []
        results.append("=== ONT Registration Verification ===")
        
        try:
            # Clear any existing output
            self.tn.read_very_eager()
            time.sleep(1)
            
            # Step 1: Enter enable mode
            results.append("Step 1: Entering enable mode...")
            self.tn.write(b"enable\r\n")
            time.sleep(2)
            enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            if "Error" in enable_output:
                results.append(f"❌ Failed to enter enable mode: {enable_output}")
                return "\n".join(results)
            results.append("✅ Entered enable mode successfully")
            
            # Step 2: Enter config mode
            results.append("Step 2: Entering configuration mode...")
            self.tn.write(b"config\r\n")
            time.sleep(2)
            config_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            if "Error" in config_output:
                results.append(f"❌ Failed to enter config mode: {config_output}")
                return "\n".join(results)
            results.append("✅ Entered configuration mode successfully")
            
            # Step 3: Enter GPON interface context
            results.append(f"Step 3: Entering GPON interface {board_id}...")
            gpon_command = f"interface gpon {board_id}"
            self.tn.write(gpon_command.encode('ascii') + b"\r\n")
            time.sleep(2)
            gpon_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            if "Error" in gpon_output:
                results.append(f"❌ Failed to enter GPON interface: {gpon_output}")
                return "\n".join(results)
            results.append("✅ Entered GPON interface successfully")
            
            # Step 4: Display all ONT info to find our ONT
            results.append("Step 4: Retrieving ONT information...")
            
            # Try different commands to get ONT information
            commands_to_try = [
                "display ont info",
                "display ont summary",
                "display ont autofind all",
                "show ont info",
                "show ont summary"
            ]
            
            ont_output = ""
            command_worked = False
            
            for cmd in commands_to_try:
                results.append(f"Trying command: {cmd}")
                self.tn.write(cmd.encode('ascii') + b"\r\n")
                time.sleep(3)
                
                # Read the output
                cmd_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                
                # Check if command worked (no parameter error)
                if "Parameter error" not in cmd_output and "Unknown command" not in cmd_output:
                    ont_output = cmd_output
                    command_worked = True
                    results.append(f"✅ Command '{cmd}' worked successfully")
                    break
                else:
                    results.append(f"❌ Command '{cmd}' failed: {cmd_output[:100]}...")
            
            if not command_worked:
                results.append("❌ All ONT display commands failed")
                results.append("ONT Status Details:")
                results.append("Unable to retrieve ONT information - all commands failed")
                return "\n".join(results)
            
            results.append("✅ ONT status retrieved successfully")
            
            # Step 5: Parse the output to find our ONT
            ont_found = False
            serial_found = False
            port_found = False
            
            # Look for ONT ID in the output (multiple possible formats)
            ont_id_patterns = [
                f"ONTID :{ont_id}",
                f"ONTID : {ont_id}",
                f"ONT ID :{ont_id}",
                f"ONT ID : {ont_id}",
                f"Number : {ont_id}",
                f"Number :{ont_id}"
            ]
            
            for pattern in ont_id_patterns:
                if pattern in ont_output:
                    ont_found = True
                    results.append(f"✅ ONT ID {ont_id} found in output (pattern: {pattern})")
                    break
            
            if not ont_found:
                results.append(f"⚠️ ONT ID {ont_id} not found in output")
            
            # Look for serial number in the output (multiple possible formats)
            serial_patterns = [
                serial_number,
                f"({serial_number})",
                f"Ont SN : {serial_number}",
                f"Ont SN :{serial_number}",
                f"Serial : {serial_number}",
                f"Serial :{serial_number}"
            ]
            
            for pattern in serial_patterns:
                if pattern in ont_output:
                    serial_found = True
                    results.append(f"✅ Serial number {serial_number} found in output (pattern: {pattern})")
                    break
            
            if not serial_found:
                results.append(f"⚠️ Serial number {serial_number} not found in ONT status")
            
            # Look for port information (multiple possible formats)
            port_patterns = [
                f"PortID :{port_id}",
                f"PortID : {port_id}",
                f"Port ID :{port_id}",
                f"Port ID : {port_id}",
                f"F/S/P : 0/1/{port_id}",
                f"F/S/P :0/1/{port_id}"
            ]
            
            for pattern in port_patterns:
                if pattern in ont_output:
                    port_found = True
                    results.append(f"✅ Port {port_id} information found in output (pattern: {pattern})")
                    break
            
            if not port_found:
                results.append(f"⚠️ Port {port_id} information not found in ONT status")
            
            # Step 6: Exit configuration mode
            results.append("Step 5: Exiting configuration mode...")
            for i in range(4):
                self.tn.write(b"quit\r\n")
                time.sleep(1)
                quit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                if "MA5683T>" in quit_output:
                    results.append("✅ Back to main prompt")
                    break
            
            # Step 7: Overall verification result
            if ont_found and serial_found and port_found:
                results.append("")
                results.append("🎉 ONT Registration Verification: SUCCESS")
                results.append(f"✅ ONT {ont_id} is properly registered on port {port_id}")
                results.append(f"✅ Serial number {serial_number} is confirmed")
            else:
                results.append("")
                results.append("⚠️ ONT Registration Verification: PARTIAL SUCCESS")
                if not ont_found:
                    results.append(f"❌ ONT ID {ont_id} not found")
                if not serial_found:
                    results.append(f"❌ Serial number {serial_number} not found")
                if not port_found:
                    results.append(f"❌ Port {port_id} information not found")
            
            results.append("")
            results.append("ONT Status Details:")
            results.append(ont_output[:500] + "..." if len(ont_output) > 500 else ont_output)
            
        except Exception as e:
            results.append(f"❌ Verification failed with exception: {str(e)}")
        
        results.append("=== Verification Completed ===")
        return "\n".join(results)
    
    def get_board_status(self):
        if not self.logged_in:
            return "Not logged in to OLT"
        return self.execute_command(f"display board {self.config['board']}", 3)
    
    def get_all_boards(self):
        """Get all boards using 'display board 0' command"""
        if not self.logged_in:
            return "Not logged in to OLT"
        return self.execute_command("display board 0", 3)
    

    
    def get_board_detail(self, board_id):
        """Get detailed status for a specific board with pagination handling"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Validate board ID format (0/0, 0/1, etc.)
        if not re.match(r'^\d+/\d+$', board_id):
            return "Invalid board format. Use format like '0/0'"
        
        # Clear any existing output first
        self.tn.read_very_eager()
        
        # Execute the command directly and handle pagination manually
        command = f"display board {board_id}"
        full_output = ""
        
        print(f"Executing command: {command}")
        
        # Send the initial command
        self.tn.write(command.encode('ascii') + b"\r\n")
        time.sleep(3)  # Increased wait time
        
        # Read initial output
        initial_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        full_output += initial_output
        
        print(f"Initial output length: {len(initial_output)}")
        print(f"Contains 'More' prompt: {'---- More ( Press \'Q\' to break ) ----' in initial_output}")
        
        # Continue reading if there are "More" prompts
        max_continues = 10
        for i in range(max_continues):
            if "---- More ( Press 'Q' to break ) ----" in full_output:
                print(f"More prompt detected on iteration {i + 1}, continuing...")
                
                # Send space to continue
                self.tn.write(b" ")
                time.sleep(3)  # Increased wait time
                
                # Read additional output
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                full_output += additional_output
                
                print(f"Continue {i + 1}, additional output length: {len(additional_output)}")
                
                # Check if we've reached the end
                if "---- More ( Press 'Q' to break ) ----" not in additional_output:
                    print("Reached end of output")
                    break
            else:
                print("No more prompts found, stopping")
                break
        
        print(f"Total output length: {len(full_output)}")
        print(f"Output preview: {full_output[:200]}...")
        return full_output

    def ensure_main_prompt(self):
        """Ensure we're at the main MA5683T prompt"""
        try:
            # Try to read until we get the main prompt
            self.tn.read_until(b"MA5683T>", timeout=2)
            return True
        except:
            # If we don't get the prompt, try sending a few quits to get back
            for i in range(3):
                try:
                    self.tn.write(b"quit\r\n")
                    time.sleep(1)
                    self.tn.read_very_eager()
                except:
                    pass
            return False

    def test_command_sending(self, command):
        """Test method to verify command sending works correctly"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        try:
            print(f"Testing command: '{command}'")
            print(f"Command bytes: {command.encode('ascii')}")
            
            # Clear buffer
            self.tn.read_very_eager()
            time.sleep(1)
            
            # Send command
            self.tn.write(command.encode('ascii') + b"\r\n")
            time.sleep(2)
            
            # Read response
            output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Test output: {repr(output)}")
            
            return output
        except Exception as e:
            return f"Test error: {str(e)}"

    def display_ont_autofind_all(self):
        """Display all automatically found ONTs with proper output handling"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Ensure we're at the main prompt first
        print("Ensuring we're at main prompt...")
        self.ensure_main_prompt()
        
        # Clear any existing output first
        self.tn.read_very_eager()
        time.sleep(1)  # Wait for buffer to clear
        
        # Step 1: Enter enable mode first
        print("Step 1: Entering enable mode...")
        self.tn.write(b"enable\r\n")
        time.sleep(2)
        
        # Clear any enable mode output and verify we're in enable mode
        enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Enable mode output: {repr(enable_output)}")
        
        # Check if we're in enable mode (should see MA5683T# prompt)
        if "MA5683T#" not in enable_output:
            print("Warning: May not be in enable mode, trying to verify...")
            # Send a test command to check mode
            self.tn.write(b"show version\r\n")
            time.sleep(1)
            test_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Mode test output: {repr(test_output)}")
        
        # Step 2: Enter config mode
        print("Step 2: Entering configuration mode...")
        self.tn.write(b"config\r\n")
        time.sleep(2)
        
        # Clear any config mode output and verify we're in config mode
        config_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Config mode output: {repr(config_output)}")
        
        # Check if we're in config mode (should see MA5683T(config)# prompt)
        if "MA5683T(config)#" not in config_output:
            print("Warning: May not be in config mode, trying to verify...")
        
        # Step 3: Enter GPON interface context
        print("Step 3: Entering GPON interface context...")
        gpon_command = f"interface gpon {self.config['board']}"
        print(f"GPON command: '{gpon_command}'")
        self.tn.write(gpon_command.encode('ascii') + b"\r\n")
        time.sleep(2)
        
        # Clear any interface entry output and verify we're in GPON interface mode
        interface_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Interface entry output: {repr(interface_output)}")
        
        # Check if we're in GPON interface mode (should see MA5683T(config-if-gpon-0/0)# prompt)
        if "MA5683T(config-if-gpon" not in interface_output:
            print("Warning: May not be in GPON interface mode, trying to verify...")
            # Try to get current prompt
            self.tn.write(b"\r\n")
            time.sleep(1)
            prompt_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Current prompt: {repr(prompt_output)}")
        
        # Step 4: Execute the autofind command within the GPON interface context
        # Clear buffer again before sending command
        self.tn.read_very_eager()
        time.sleep(1)
        
        # Try the command with proper spacing and verification
        command = "display ont autofind all"  # This IS the correct command
        full_output = ""
        
        print(f"Step 4: Executing command: '{command}'")
        print(f"Command bytes: {command.encode('ascii')}")
        
        # Send the command with explicit line ending and flush
        command_bytes = command.encode('ascii') + b"\r\n"
        print(f"Sending command bytes: {command_bytes}")
        print(f"Command length: {len(command_bytes)}")
        
        # Send command with proper spacing
        self.tn.write(command_bytes)
        self.tn.sock.settimeout(5)  # Set socket timeout
        time.sleep(3)  # Wait for response
        
        # Read initial output
        initial_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        full_output += initial_output
        
        print(f"Initial output: {repr(initial_output)}")
        print(f"Initial output length: {len(initial_output)}")
        print(f"Contains 'More' prompt: {'---- More ( Press \'Q\' to break ) ----' in initial_output}")
        
        # Check if we got an error
        if "Unknown command" in initial_output or "error" in initial_output.lower() or "Parameter error" in initial_output:
            print("Command error detected, trying alternative approach...")
            
            # Clear buffer and try again with step-by-step approach
            self.tn.read_very_eager()
            time.sleep(1)
            
            # Try sending the command with a different approach - send each word separately
            print("Trying step-by-step command approach...")
            self.tn.write(b"display\r\n")
            time.sleep(1)
            self.tn.read_very_eager()  # Clear any response
            
            self.tn.write(b"ont\r\n")
            time.sleep(1)
            self.tn.read_very_eager()  # Clear any response
            
            self.tn.write(b"autofind\r\n")
            time.sleep(1)
            self.tn.read_very_eager()  # Clear any response
            
            self.tn.write(b"all\r\n")
            time.sleep(3)
            
            # Read the output again
            alternative_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            full_output += alternative_output
            print(f"Alternative output: {repr(alternative_output)}")
        
        # Continue reading if there are "More" prompts
        max_continues = 10
        for i in range(max_continues):
            if "---- More ( Press 'Q' to break ) ----" in full_output:
                print(f"More prompt detected on iteration {i + 1}, continuing...")
                
                # Send space to continue
                self.tn.write(b" ")
                time.sleep(2)  # Wait for additional output
                
                # Read additional output
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                full_output += additional_output
                
                print(f"Continue {i + 1}, additional output: {repr(additional_output)}")
                print(f"Continue {i + 1}, additional output length: {len(additional_output)}")
                
                # Check if we've reached the end
                if "---- More ( Press 'Q' to break ) ----" not in additional_output:
                    print("Reached end of output")
                    break
            else:
                print("No more prompts found, stopping")
                break
        
        # Step 5: Exit back to main prompt (multiple quits needed)
        print("Step 5: Exiting configuration mode...")
        for i in range(4):  # Need more quits to get back to main prompt from enable mode
            self.tn.write(b"quit\r\n")
            time.sleep(1)
            exit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Exit {i+1} output: {repr(exit_output)}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in exit_output:
                print("Back to main prompt")
                break
        
        print(f"Total output length: {len(full_output)}")
        print(f"Total output: {repr(full_output)}")
        
        # Clean up the output by removing command echo and prompt
        lines = full_output.split('\r\n')
        cleaned_lines = []
        command_found = False
        
        for line in lines:
            if not command_found and command.strip() in line:
                command_found = True
                continue
            if line.strip() and not line.strip().startswith('MA5683T>') and not line.strip().startswith('MA5683T(config-if-gpon'):
                cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        print(f"Cleaned output: {repr(cleaned_output)}")
        return cleaned_output.strip()

    def display_ont_autofind_simple(self):
        """Display all automatically found ONTs - simple approach from enable mode"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Ensure we're at the main prompt first
        print("Ensuring we're at main prompt...")
        self.ensure_main_prompt()
        
        # Clear any existing output first
        self.tn.read_very_eager()
        time.sleep(1)
        
        # Step 1: Enter enable mode first
        print("Step 1: Entering enable mode...")
        self.tn.write(b"enable\r\n")
        time.sleep(2)
        
        # Clear any enable mode output
        enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Enable mode output: {repr(enable_output)}")
        
        # Step 2: Execute the command directly from enable mode
        print("Step 2: Executing display ont autofind all from enable mode...")
        command = "display ont autofind all"  # This IS the correct command
        full_output = ""
        
        print(f"Executing command: '{command}'")
        print(f"Command bytes: {command.encode('ascii')}")
        
        # Send the command
        command_bytes = command.encode('ascii') + b"\r\n"
        self.tn.write(command_bytes)
        time.sleep(3)
        
        # Read output
        initial_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        full_output += initial_output
        
        print(f"Initial output: {repr(initial_output)}")
        
        # Check if we got an error
        if "Unknown command" in initial_output or "error" in initial_output.lower() or "Parameter error" in initial_output:
            print("Command failed from enable mode, trying with GPON interface context...")
            
            # Clear buffer
            self.tn.read_very_eager()
            time.sleep(1)
            
            # Try entering GPON interface context
            print("Entering GPON interface context...")
            gpon_command = f"interface gpon {self.config['board']}"
            self.tn.write(gpon_command.encode('ascii') + b"\r\n")
            time.sleep(2)
            
            # Clear interface output
            self.tn.read_very_eager()
            
            # Try the command again
            print("Trying command again from GPON interface context...")
            self.tn.write(command_bytes)
            time.sleep(3)
            
            # Read output
            interface_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            full_output += interface_output
            print(f"Interface context output: {repr(interface_output)}")
        
        # Continue reading if there are "More" prompts
        max_continues = 10
        for i in range(max_continues):
            if "---- More ( Press 'Q' to break ) ----" in full_output:
                print(f"More prompt detected on iteration {i + 1}, continuing...")
                
                # Send space to continue
                self.tn.write(b" ")
                time.sleep(2)
                
                # Read additional output
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                full_output += additional_output
                
                print(f"Continue {i + 1}, additional output: {repr(additional_output)}")
                
                # Check if we've reached the end
                if "---- More ( Press 'Q' to break ) ----" not in additional_output:
                    print("Reached end of output")
                    break
            else:
                print("No more prompts found, stopping")
                break
        
        # Exit back to main prompt
        print("Exiting to main prompt...")
        for i in range(3):  # enable -> main prompt
            self.tn.write(b"quit\r\n")
            time.sleep(1)
            exit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Exit {i+1} output: {repr(exit_output)}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in exit_output:
                print("Back to main prompt")
                break
        
        print(f"Total output length: {len(full_output)}")
        
        # Clean up the output
        lines = full_output.split('\r\n')
        cleaned_lines = []
        command_found = False
        
        for line in lines:
            if not command_found and command.strip() in line:
                command_found = True
                continue
            if line.strip() and not line.strip().startswith('MA5683T>') and not line.strip().startswith('MA5683T(config-if-gpon'):
                cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        print(f"Cleaned output: {repr(cleaned_output)}")
        return cleaned_output.strip()

    def display_ont_info_by_desc(self, description):
        """Display ONT information by description with proper output handling"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Clear any existing output first
        self.tn.read_very_eager()
        
        # Step 1: Enter enable mode first
        print("Step 1: Entering enable mode...")
        self.tn.write(b"enable\r\n")
        time.sleep(2)
        
        # Clear any enable mode output
        enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Enable mode output: {repr(enable_output)}")
        
        # Step 2: Enter config mode
        print("Step 2: Entering configuration mode...")
        self.tn.write(b"config\r\n")
        time.sleep(2)
        
        # Clear any config mode output
        config_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Config mode output: {repr(config_output)}")
        
        # Step 3: Enter GPON interface context
        print("Step 3: Entering GPON interface context...")
        gpon_command = f"interface gpon {self.config['board']}"
        self.tn.write(gpon_command.encode('ascii') + b"\r\n")
        time.sleep(2)
        
        # Clear any interface entry output
        self.tn.read_very_eager()
        
        # Step 4: Execute the command within the GPON interface context
        command = f"display ont info by-desc {description}"
        full_output = ""
        
        print(f"Step 4: Executing command: {command}")
        
        # Send the initial command
        self.tn.write(command.encode('ascii') + b"\r\n")
        time.sleep(3)  # Wait for response
        
        # Read initial output
        initial_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        full_output += initial_output
        
        print(f"Initial output length: {len(initial_output)}")
        print(f"Contains 'More' prompt: {'---- More ( Press \'Q\' to break ) ----' in initial_output}")
        
        # Continue reading if there are "More" prompts
        max_continues = 10
        for i in range(max_continues):
            if "---- More ( Press 'Q' to break ) ----" in full_output:
                print(f"More prompt detected on iteration {i + 1}, continuing...")
                
                # Send space to continue
                self.tn.write(b" ")
                time.sleep(2)  # Wait for additional output
                
                # Read additional output
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                full_output += additional_output
                
                print(f"Continue {i + 1}, additional output length: {len(additional_output)}")
                
                # Check if we've reached the end
                if "---- More ( Press 'Q' to break ) ----" not in additional_output:
                    print("Reached end of output")
                    break
            else:
                print("No more prompts found, stopping")
                break
        
        # Step 5: Exit back to main prompt (multiple quits needed)
        print("Step 5: Exiting configuration mode...")
        for i in range(4):  # Need more quits to get back to main prompt from enable mode
            self.tn.write(b"quit\r\n")
            time.sleep(1)
            exit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Exit {i+1} output: {repr(exit_output)}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in exit_output:
                print("Back to main prompt")
                break
        
        print(f"Total output length: {len(full_output)}")
        print(f"Output preview: {full_output[:200]}...")
        
        # Clean up the output by removing command echo and prompt
        lines = full_output.split('\r\n')
        cleaned_lines = []
        command_found = False
        
        for line in lines:
            if not command_found and command.strip() in line:
                command_found = True
                continue
            if line.strip() and not line.strip().startswith('MA5683T>') and not line.strip().startswith('MA5683T(config-if-gpon'):
                cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        return cleaned_output.strip()

    def enter_config_mode(self):
        """Enter configuration mode (enable -> config)"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # First check if we're already in enable mode
        print("Checking current mode...")
        self.tn.read_very_eager()  # Clear any existing output
        
        # Send a simple command to check current prompt
        self.tn.write(b"\r\n")
        time.sleep(1)
        current_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Current prompt check: {repr(current_output)}")
        
        # Check if we're already in enable mode
        if "MA5683T#" in current_output:
            print("Already in enable mode, proceeding to config mode...")
            enable_result = "Already in enable mode"
        else:
            # Step 1: Enter enable mode first
            print("Entering enable mode...")
            enable_result = self.execute_command("enable", 2)
            if "Error" in enable_result or "Unknown command" in enable_result:
                return f"Failed to enter enable mode: {enable_result}"
        
        # Step 2: Enter config mode
        print("Entering config mode...")
        config_result = self.execute_command("config", 2)
        if "Error" in config_result or "Unknown command" in config_result:
            return f"Failed to enter config mode: {config_result}"
        
        return f"Enable mode: {enable_result}\nConfig mode: {config_result}"

    def configure_gpon_interface(self, board_id):
        """Enter GPON interface configuration mode"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Validate board ID format (0/0, 0/1, etc.)
        if not re.match(r'^\d+/\d+$', board_id):
            return "Invalid board format. Use format like '0/0'"
        
        return self.execute_command(f"interface gpon {board_id}", 2)

    def add_ont(self, port_id, ont_id, serial_number, line_profile_id=10, service_profile_id=10, description="test"):
        """Add an ONT to the GPON interface"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Construct the ONT add command based on the terminal output
        command = f"ont add {port_id} {ont_id} sn-auth {serial_number} omci ont-lineprofile-id {line_profile_id} ont-srvprofile-id {service_profile_id} desc {description}"
        
        return self.execute_command(command, 3)

    def exit_config_mode(self):
        """Exit configuration mode (send multiple quits to get back to main prompt)"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        results = []
        
        # Need multiple quits to get back to main prompt from enable mode
        for i in range(4):  # config -> enable -> main prompt
            result = self.execute_command("quit", 1)
            results.append(f"Exit {i+1}: {result}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in result:
                break
        
        return "\n".join(results)

    def get_ont_status(self, board_id, ont_id):
        """Get ONT status information with proper output handling"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Validate board ID format
        if not re.match(r'^\d+/\d+$', board_id):
            return "Invalid board format. Use format like '0/0'"
        
        # Clear any existing output first
        self.tn.read_very_eager()
        
        # Step 1: Enter enable mode first
        print("Step 1: Entering enable mode...")
        self.tn.write(b"enable\r\n")
        time.sleep(2)
        
        # Clear any enable mode output
        enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Enable mode output: {repr(enable_output)}")
        
        # Step 2: Enter config mode
        print("Step 2: Entering configuration mode...")
        self.tn.write(b"config\r\n")
        time.sleep(2)
        
        # Clear any config mode output
        config_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Config mode output: {repr(config_output)}")
        
        # Step 3: Enter GPON interface context
        print("Step 3: Entering GPON interface context...")
        gpon_command = f"interface gpon {board_id}"
        self.tn.write(gpon_command.encode('ascii') + b"\r\n")
        time.sleep(2)
        
        # Clear any interface entry output
        self.tn.read_very_eager()
        
        # Step 4: Execute the command within the GPON interface context
        command = f"display ont info {ont_id}"
        full_output = ""
        
        print(f"Step 4: Executing command: {command}")
        
        # Send the initial command
        self.tn.write(command.encode('ascii') + b"\r\n")
        time.sleep(3)  # Wait for response
        
        # Read initial output
        initial_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        full_output += initial_output
        
        print(f"Initial output length: {len(initial_output)}")
        print(f"Contains 'More' prompt: {'---- More ( Press \'Q\' to break ) ----' in initial_output}")
        
        # Continue reading if there are "More" prompts
        max_continues = 10
        for i in range(max_continues):
            if "---- More ( Press 'Q' to break ) ----" in full_output:
                print(f"More prompt detected on iteration {i + 1}, continuing...")
                
                # Send space to continue
                self.tn.write(b" ")
                time.sleep(2)  # Wait for additional output
                
                # Read additional output
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                full_output += additional_output
                
                print(f"Continue {i + 1}, additional output length: {len(additional_output)}")
                
                # Check if we've reached the end
                if "---- More ( Press 'Q' to break ) ----" not in additional_output:
                    print("Reached end of output")
                    break
            else:
                print("No more prompts found, stopping")
                break
        
        # Step 5: Exit back to main prompt (multiple quits needed)
        print("Step 5: Exiting configuration mode...")
        for i in range(4):  # Need more quits to get back to main prompt from enable mode
            self.tn.write(b"quit\r\n")
            time.sleep(1)
            exit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Exit {i+1} output: {repr(exit_output)}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in exit_output:
                print("Back to main prompt")
                break
        
        print(f"Total output length: {len(full_output)}")
        print(f"Output preview: {full_output[:200]}...")
        
        # Clean up the output by removing command echo and prompt
        lines = full_output.split('\r\n')
        cleaned_lines = []
        command_found = False
        
        for line in lines:
            if not command_found and command.strip() in line:
                command_found = True
                continue
            if line.strip() and not line.strip().startswith('MA5683T>') and not line.strip().startswith('MA5683T(config-if-gpon'):
                cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        return cleaned_output.strip()

    def get_onts_in_port(self, board_id):
        """Get all ONTs in a specific port with proper output handling"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Validate board ID format
        if not re.match(r'^\d+/\d+$', board_id):
            return "Invalid board format. Use format like '0/0'"
        
        # Clear any existing output first
        self.tn.read_very_eager()
        
        # Step 1: Enter enable mode first
        print("Step 1: Entering enable mode...")
        self.tn.write(b"enable\r\n")
        time.sleep(2)
        
        # Clear any enable mode output
        enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Enable mode output: {repr(enable_output)}")
        
        # Step 2: Enter config mode
        print("Step 2: Entering configuration mode...")
        self.tn.write(b"config\r\n")
        time.sleep(2)
        
        # Clear any config mode output
        config_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Config mode output: {repr(config_output)}")
        
        # Step 3: Enter GPON interface context
        print("Step 3: Entering GPON interface context...")
        gpon_command = f"interface gpon {board_id}"
        self.tn.write(gpon_command.encode('ascii') + b"\r\n")
        time.sleep(2)
        
        # Clear any interface entry output
        self.tn.read_very_eager()
        
        # Step 4: Execute the command within the GPON interface context
        command = "display ont info"
        full_output = ""
        
        print(f"Step 4: Executing command: {command}")
        
        # Send the initial command
        self.tn.write(command.encode('ascii') + b"\r\n")
        time.sleep(3)  # Wait for response
        
        # Read initial output
        initial_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        full_output += initial_output
        
        print(f"Initial output length: {len(initial_output)}")
        print(f"Contains 'More' prompt: {'---- More ( Press \'Q\' to break ) ----' in initial_output}")
        
        # Continue reading if there are "More" prompts
        max_continues = 10
        for i in range(max_continues):
            if "---- More ( Press 'Q' to break ) ----" in full_output:
                print(f"More prompt detected on iteration {i + 1}, continuing...")
                
                # Send space to continue
                self.tn.write(b" ")
                time.sleep(2)  # Wait for additional output
                
                # Read additional output
                additional_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
                full_output += additional_output
                
                print(f"Continue {i + 1}, additional output length: {len(additional_output)}")
                
                # Check if we've reached the end
                if "---- More ( Press 'Q' to break ) ----" not in additional_output:
                    print("Reached end of output")
                    break
            else:
                print("No more prompts found, stopping")
                break
        
        # Step 5: Exit back to main prompt (multiple quits needed)
        print("Step 5: Exiting configuration mode...")
        for i in range(4):  # Need more quits to get back to main prompt from enable mode
            self.tn.write(b"quit\r\n")
            time.sleep(1)
            exit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Exit {i+1} output: {repr(exit_output)}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in exit_output:
                print("Back to main prompt")
                break
        
        print(f"Total output length: {len(full_output)}")
        print(f"Output preview: {full_output[:200]}...")
        
        # Clean up the output by removing command echo and prompt
        lines = full_output.split('\r\n')
        cleaned_lines = []
        command_found = False
        
        for line in lines:
            if not command_found and command.strip() in line:
                command_found = True
                continue
            if line.strip() and not line.strip().startswith('MA5683T>') and not line.strip().startswith('MA5683T(config-if-gpon'):
                cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        return cleaned_output.strip()
    
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

    def display_ont_autofind_alternative(self):
        """Try alternative ONT discovery commands for MA5683T"""
        if not self.logged_in:
            return "Not logged in to OLT"
        
        # Ensure we're at the main prompt first
        print("Ensuring we're at main prompt...")
        self.ensure_main_prompt()
        
        # Clear any existing output first
        self.tn.read_very_eager()
        time.sleep(1)
        
        # Step 1: Enter enable mode first
        print("Step 1: Entering enable mode...")
        self.tn.write(b"enable\r\n")
        time.sleep(2)
        
        # Clear any enable mode output
        enable_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"Enable mode output: {repr(enable_output)}")
        
        # Step 2: Try different ONT discovery commands
        commands_to_try = [
            "display ont autofind",
            "display ont info",
            "display ont summary",
            "display ont autofind all",
            "show ont autofind",
            "show ont info"
        ]
        
        full_output = ""
        
        for i, command in enumerate(commands_to_try):
            print(f"Trying command {i+1}: '{command}'")
            
            # Clear buffer
            self.tn.read_very_eager()
            time.sleep(1)
            
            # Send command
            command_bytes = command.encode('ascii') + b"\r\n"
            self.tn.write(command_bytes)
            time.sleep(3)
            
            # Read output
            output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Command '{command}' output: {repr(output)}")
            
            # Check if command worked (no error messages)
            if ("Unknown command" not in output and 
                "error" not in output.lower() and 
                "Parameter error" not in output and
                len(output.strip()) > 0):
                print(f"Command '{command}' worked!")
                full_output = output
                break
            else:
                print(f"Command '{command}' failed, trying next...")
                full_output += f"\n--- Command '{command}' failed ---\n{output}\n"
        
        # Exit back to main prompt
        print("Exiting to main prompt...")
        for i in range(3):  # enable -> main prompt
            self.tn.write(b"quit\r\n")
            time.sleep(1)
            exit_output = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print(f"Exit {i+1} output: {repr(exit_output)}")
            
            # Check if we're back to main prompt
            if "MA5683T>" in exit_output:
                print("Back to main prompt")
                break
        
        print(f"Total output length: {len(full_output)}")
        return full_output.strip()

        