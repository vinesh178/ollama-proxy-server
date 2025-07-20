import http.server
import socketserver
import urllib.request
import urllib.error
import json
import sys
import traceback
import io
import os

# Configuration
PROXY_PORT = int(os.environ.get("PROXY_PORT", 8000))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

class OllamaProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to provide more detailed logging
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format % args))
    
    def do_OPTIONS(self):
        print(f"OPTIONS request to {self.path}")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        print(f"GET request to {self.path}")
        try:
            # Forward the request to Ollama
            ollama_url = f"{OLLAMA_URL}{self.path}"
            print(f"Forwarding to {ollama_url}")
            
            req = urllib.request.Request(ollama_url, method="GET")
            with urllib.request.urlopen(req) as response:
                # Get the response data
                data = response.read()
                
                # Log response info
                print(f"Response status: {response.status}")
                print(f"Response headers: {response.getheaders()}")
                print(f"Response data (first 100 bytes): {data[:100]}")
                
                # Send response to client
                self.send_response(response.status)
                self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(data)
                
        except urllib.error.URLError as e:
            print(f"URLError: {e}")
            # Send error response with CORS headers
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            error_response = json.dumps({"error": f"Error connecting to Ollama: {e}"})
            self.wfile.write(error_response.encode('utf-8'))
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            # Send error response with CORS headers
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            error_response = json.dumps({"error": f"Unexpected error: {e}"})
            self.wfile.write(error_response.encode('utf-8'))
    
    def do_POST(self):
        print(f"POST request to {self.path}")
        try:
            # Get the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Log request info
            print(f"Request headers: {self.headers}")
            print(f"Request data (first 100 bytes): {post_data[:100]}")
            
            # Check if this is a generate request
            if self.path == '/api/generate':
                self.handle_generate_request(post_data)
            else:
                # Forward other POST requests normally
                self.forward_post_request(post_data)
                
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            # Send error response with CORS headers
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            error_response = json.dumps({"error": f"Unexpected error: {e}"})
            self.wfile.write(error_response.encode('utf-8'))
    
    def handle_generate_request(self, post_data):
        """Special handling for /api/generate to collect the entire streamed response"""
        try:
            # Forward the request to Ollama
            ollama_url = f"{OLLAMA_URL}/api/generate"
            print(f"Forwarding to {ollama_url} with special handling")
            
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(ollama_url, data=post_data, headers=headers, method="POST")
            
            # Variables to collect the full response
            full_text = ""
            model_name = ""
            created_at = ""
            
            try:
                with urllib.request.urlopen(req) as response:
                    # Read the response line by line
                    print("Reading response from Ollama...")
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        
                        # Decode the line
                        line_str = line.decode('utf-8')
                        
                        # Try to parse the JSON
                        try:
                            json_response = json.loads(line_str)
                            
                            # Extract information from the response
                            if not model_name and 'model' in json_response:
                                model_name = json_response['model']
                                print(f"Model: {model_name}")
                            
                            if not created_at and 'created_at' in json_response:
                                created_at = json_response['created_at']
                                print(f"Created at: {created_at}")
                            
                            # Append the response text
                            if 'response' in json_response:
                                response_text = json_response['response']
                                full_text += response_text
                                print(f"Response chunk: {response_text}", end="")
                            
                            # Check if this is the last chunk
                            if json_response.get('done', False):
                                print("\nGeneration complete")
                            
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {line_str}")
                
                print(f"\nFull text length: {len(full_text)}")
                
                # Create a single JSON response with the full text
                complete_response = {
                    "model": model_name,
                    "created_at": created_at,
                    "response": full_text,
                    "done": True
                }
                
                # Send the complete response to the client
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                # Convert the response to JSON and send it
                response_json = json.dumps(complete_response)
                print(f"Sending complete response: {response_json[:100]}...")
                self.wfile.write(response_json.encode('utf-8'))
                print("Response sent to client")
                
            except urllib.error.URLError as e:
                print(f"URLError: {e}")
                # Send error response with CORS headers
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                error_response = json.dumps({"error": f"Error connecting to Ollama: {e}"})
                self.wfile.write(error_response.encode('utf-8'))
                
        except Exception as e:
            print(f"Unexpected error in handle_generate_request: {e}")
            traceback.print_exc()
            # Send error response with CORS headers
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            error_response = json.dumps({"error": f"Unexpected error: {e}"})
            self.wfile.write(error_response.encode('utf-8'))
    
    def forward_post_request(self, post_data):
        """Forward a regular POST request to Ollama"""
        try:
            # Forward the request to Ollama
            ollama_url = f"{OLLAMA_URL}{self.path}"
            print(f"Forwarding to {ollama_url}")
            
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(ollama_url, data=post_data, headers=headers, method="POST")
            
            with urllib.request.urlopen(req) as response:
                # Get the response data
                data = response.read()
                
                # Log response info
                print(f"Response status: {response.status}")
                print(f"Response headers: {response.getheaders()}")
                print(f"Response data (first 100 bytes): {data[:100]}")
                
                # Send response to client
                self.send_response(response.status)
                self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(data)
                
        except urllib.error.URLError as e:
            print(f"URLError: {e}")
            # Send error response with CORS headers
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            error_response = json.dumps({"error": f"Error connecting to Ollama: {e}"})
            self.wfile.write(error_response.encode('utf-8'))

def run_server():
    handler = OllamaProxyHandler
    
    # Allow socket reuse to avoid "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PROXY_PORT), handler) as httpd:
        print(f"Starting Ollama proxy server on http://localhost:{PROXY_PORT}")
        print(f"Forwarding requests to {OLLAMA_URL}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped by user")
            sys.exit(0)

if __name__ == "__main__":
    run_server() 