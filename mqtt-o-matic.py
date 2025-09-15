#!/usr/bin/env python3
"""
MQTT-O-Matic - Professional MQTT Scanner and Authentication Tester
Created by a1c3venom
"""

import socket
import paho.mqtt.client as mqtt
import threading
import time
import argparse
import json
import csv
import sys
from datetime import datetime

# ASCII Banner
BANNER = """
███╗   ███╗ ██████╗ ████████╗████████╗   ██████╗ ███╗   ███╗ █████╗ ████████╗██╗ ██████╗
████╗ ████║██╔═══██╗╚══██╔══╝╚══██╔══╝   ██╔══██╗████╗ ████║██╔══██╗╚══██╔══╝██║██╔════╝
██╔████╔██║██║   ██║   ██║      ██║█████╗██████╔╝██╔████╔██║███████║   ██║   ██║██║     
██║╚██╔╝██║██║   ██║   ██║      ██║╚════╝██╔═══╝ ██║╚██╔╝██║██╔══██║   ██║   ██║██║     
██║ ╚═╝ ██║╚██████╔╝   ██║      ██║      ██║     ██║ ╚═╝ ██║██║  ██║   ██║   ██║╚██████╗
╚═╝     ╚═╝ ╚═════╝    ╚═╝      ╚═╝      ╚═╝     ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝
                                                                                        
                            by a1c3venom
"""

DEFAULT_CREDENTIALS = [
    ('admin', 'admin'),
    ('root', 'root'),
    ('mqtt', 'mqtt'),
    ('user', 'user'),
    ('guest', 'guest'),
    ('test', 'test'),
    ('', ''),  # Empty credentials
    ('anonymous', ''),  # Anonymous access
]

class MQTTChecker:
    def __init__(self, timeout=5, verbose=False):
        self.timeout = timeout
        self.verbose = verbose
        self.results = {}
        self.conn_result = None  # Needed for tracking connection result in each try_connect
        self.lock = threading.Lock()

    def log(self, message, level="info"):
        """Log messages based on verbosity level"""
        if self.verbose or level == "important":
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def is_mqtt_broker(self, ip, port=1883):
        """Check if the IP is running an MQTT broker on the specified port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception as e:
            if self.verbose:
                self.log(f"Socket error for {ip}:{port} - {str(e)}", "debug")
            return False

    def try_connect(self, ip, port=1883, username=None, password=None):
        """Attempt to connect to the MQTT broker with given credentials."""
        self.conn_result = None
        client = mqtt.Client()
        if username is not None and password is not None:
            client.username_pw_set(username, password)
        client.on_connect = self.on_connect

        try:
            client.connect(ip, port, self.timeout)
            client.loop_start()
            start_time = time.time()
            while time.time() - start_time < self.timeout and self.conn_result is None:
                time.sleep(0.1)
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            if self.verbose:
                self.log(f"Connection error for {ip}:{port} - {str(e)}", "debug")
            return None
        return self.conn_result

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server."""
        self.conn_result = rc

    def test_ip(self, ip, port=1883):
        """Test a single IP address for MQTT and authentication."""
        if self.verbose:
            self.log(f"Testing {ip}:{port}")

        if not self.is_mqtt_broker(ip, port):
            with self.lock:
                self.results[f"{ip}:{port}"] = {
                    "status": "Not an MQTT broker or unreachable",
                    "credentials": None
                }
            if self.verbose:
                self.log(f"{ip}:{port} - Not an MQTT broker or unreachable")
            return


        rc = self.try_connect(ip, port)
        if rc == 0:
            with self.lock:
                self.results[f"{ip}:{port}"] = {
                    "status": "Unauthenticated access allowed",
                    "credentials": ("", "")
                }
            if self.verbose:
                self.log(f"{ip}:{port} - Unauthenticated access allowed", "important")
            return


        for username, password in DEFAULT_CREDENTIALS:
            rc = self.try_connect(ip, port, username, password)
            if rc == 0:
                with self.lock:
                    self.results[f"{ip}:{port}"] = {
                        "status": "Login successful",
                        "credentials": (username, password)
                    }
                if self.verbose:
                    self.log(f"{ip}:{port} - Login successful with {username}:{password}", "important")
                return

        with self.lock:
            self.results[f"{ip}:{port}"] = {
                "status": "No default credentials worked",
                "credentials": None
            }
        if self.verbose:
            self.log(f"{ip}:{port} - No default credentials worked")

def read_targets(target_input):
    """Read targets from file or direct input"""
    targets = []
    

    try:
        with open(target_input, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                  
                    if ':' in line:
                        ip, port = line.split(':', 1)
                        targets.append((ip, int(port)))
                    else:
                        targets.append((line, 1883))  
        return targets
    except (FileNotFoundError, IOError):
        pass
    
   
    if ',' in target_input:
        for item in target_input.split(','):
            item = item.strip()
            if ':' in item:
                ip, port = item.split(':', 1)
                targets.append((ip, int(port)))
            else:
                targets.append((item, 1883))
        return targets
    
   
    if ':' in target_input:
        ip, port = target_input.split(':', 1)
        targets.append((ip, int(port)))
        return targets
    
   
    targets.append((target_input, 1883))
    return targets

def save_results(results, output_file, format_type):
    """Save results in the specified format"""
    if format_type == "txt":
        with open(output_file, 'w') as f:
            f.write("MQTT-O-Matic Scan Results\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            for target, result in results.items():
                f.write(f"Target: {target}\n")
                f.write(f"Status: {result['status']}\n")
                if result['credentials']:
                    username, password = result['credentials']
                    f.write(f"Credentials: {username}:{password}\n")
                f.write("-" * 30 + "\n")
    
    elif format_type == "json":
        
        json_results = {}
        for target, result in results.items():
            json_results[target] = {
                "status": result["status"],
                "credentials": {
                    "username": result["credentials"][0] if result["credentials"] else None,
                    "password": result["credentials"][1] if result["credentials"] else None
                }
            }
        
        with open(output_file, 'w') as f:
            json.dump({
                "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "results": json_results
            }, f, indent=4)
    
    elif format_type == "csv":
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Target", "Status", "Username", "Password"])
            for target, result in results.items():
                username = result['credentials'][0] if result['credentials'] else ""
                password = result['credentials'][1] if result['credentials'] else ""
                writer.writerow([target, result['status'], username, password])

def main():
    print(BANNER)
    
    parser = argparse.ArgumentParser(
        description='MQTT-O-Matic - Professional MQTT Scanner and Authentication Tester',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -t targets.txt -o results.txt -f txt
  %(prog)s -t 192.168.1.1,192.168.1.2:1884 -o results.json -f json -v
  %(prog)s -t 192.168.1.0/24 -o results.csv -f csv
        '''
    )
    
    parser.add_argument('-t', '--target', required=True, 
                       help='Target(s) to scan. Can be: IP, IP:PORT, comma-separated list, or file containing targets')
    parser.add_argument('-o', '--output', required=True, 
                       help='Output file to save results')
    parser.add_argument('-f', '--format', choices=['txt', 'json', 'csv'], default='txt',
                       help='Output format (default: txt)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('-T', '--timeout', type=int, default=5,
                       help='Connection timeout in seconds (default: 5)')
    
    args = parser.parse_args()
    
   
    try:
        targets = read_targets(args.target)
    except Exception as e:
        print(f"Error reading targets: {e}")
        sys.exit(1)
    
    if not targets:
        print("No valid targets found")
        sys.exit(1)
    
    print(f"[*] Loaded {len(targets)} target(s) to scan")
    if args.verbose:
        for target in targets:
            print(f"    {target[0]}:{target[1]}")
    
   
    checker = MQTTChecker(timeout=args.timeout, verbose=args.verbose)
    threads = []
    
    print("[*] Starting scan...")
    start_time = time.time()
    
   
    for ip, port in targets:
        thread = threading.Thread(target=checker.test_ip, args=(ip, port))
        threads.append(thread)
        thread.start()
    
    
    for thread in threads:
        thread.join()
    
    
    duration = time.time() - start_time
    

    try:
        save_results(checker.results, args.output, args.format)
        print(f"[*] Results saved to {args.output} in {args.format} format")
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)
    
    
    print(f"[*] Scan completed in {duration:.2f} seconds")
    print("[*] Summary:")
    
    status_counts = {}
    for result in checker.results.values():
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"    {status}: {count}")
    
   
    vulnerable_targets = {k: v for k, v in checker.results.items() 
                         if "Unauthenticated" in v['status'] or "successful" in v['status']}
    
    if vulnerable_targets:
        print("\n[!] VULNERABLE TARGETS FOUND:")
        for target, result in vulnerable_targets.items():
            creds = ""
            if result['credentials']:
                username, password = result['credentials']
                creds = f" ({username}:{password})"
            print(f"    {target} - {result['status']}{creds}")

if __name__ == "__main__":
    main()
