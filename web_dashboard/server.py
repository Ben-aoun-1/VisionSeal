#!/usr/bin/env python3
"""
Simple web server for VisionSeal dashboard with authentication
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path
from urllib.parse import urlparse

class AuthHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that redirects root to auth page"""
    
    def do_GET(self):
        # Redirect root to auth page
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', '/auth.html')
            self.end_headers()
            return
        
        # Serve files normally
        super().do_GET()

def serve_dashboard(port=8080):
    """Serve the VisionSeal dashboard"""
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    print(f"🌐 VisionSeal Dashboard Server")
    print(f"=" * 35)
    print(f"🚀 Starting server on port {port}...")
    print(f"📁 Serving from: {dashboard_dir}")
    print(f"🔗 Auth URL: http://localhost:{port}/auth.html")
    print(f"🔗 Dashboard URL: http://localhost:{port}/dashboard.html")
    print(f"🔗 Guest Access: http://localhost:{port}/index.html")
    print()
    
    # Create HTTP server with custom handler
    handler = AuthHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Server running at http://localhost:{port}")
            print(f"💼 Displaying African tender opportunities from Supabase")
            print(f"🔍 Features: Search, filter, real-time data")
            print()
            print(f"Press Ctrl+C to stop the server")
            print("-" * 50)
            
            # Try to open browser automatically
            try:
                webbrowser.open(f"http://localhost:{port}")
                print(f"🌐 Opened dashboard in browser")
            except:
                print(f"📝 Manually open: http://localhost:{port}")
            
            # Serve forever
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use")
            print(f"💡 Try a different port: python server.py --port 8081")
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionSeal Dashboard Server")
    parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    
    args = parser.parse_args()
    serve_dashboard(args.port)