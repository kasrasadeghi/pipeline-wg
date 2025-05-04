"""
thanks gemini:

can you make a webserver written in python that allows you to download a single file if you type in a 6 digit code and then shuts down the server
how do we get my LAN ip in python in a way that works on linux and mac

small modifications afterwards made by me
"""

#!/usr/bin/env python3
import http.server
import socketserver
import os
import random
import string
import threading
import urllib.parse
import sys
import time
from functools import partial
import argparse
import socket

argparser = argparse.ArgumentParser()
argparser.add_argument("--port", type=int, default=8000)
argparser.add_argument("--file", type=str, default="output/client.conf")
argparser.add_argument("--code-length", type=int, default=6)
args = argparser.parse_args()

# --- Configuration ---
PORT = args.port
# !!! IMPORTANT: Change this to the actual path of the file you want to serve !!!
FILE_TO_SERVE = args.file
# Name the file should have when downloaded
DOWNLOAD_FILENAME = os.path.basename(FILE_TO_SERVE)
CODE_LENGTH = args.code_length
# --- End Configuration ---

# Global event to signal server shutdown
shutdown_event = threading.Event()

class FileDownloadHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom request handler to serve a file after code verification
    and then trigger server shutdown.
    """
    def __init__(self, *args, correct_code, file_path, download_filename, shutdown_event_ref, **kwargs):
        # Store custom arguments before calling super().__init__
        self.correct_code = correct_code
        self.file_path = file_path
        self.download_filename = download_filename
        self.shutdown_event_ref = shutdown_event_ref
        # Call the superclass constructor
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handles GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path == '/':
            # Serve the HTML form to enter the code
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            error_message = ""
            if 'error' in query_params and query_params['error'][0] == '1':
                error_message = "<p style='color: red;'>Invalid code. Please try again.</p>"

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Enter Code to Download</title>
                <style>
                    body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f4; }}
                    .container {{ background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                    input[type="text"] {{ padding: 10px; margin-right: 5px; border: 1px solid #ccc; border-radius: 4px; }}
                    button {{ padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                    button:hover {{ background-color: #0056b3; }}
                    p {{ margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Enter Code to Download File</h2>
                    {error_message}
                    <form action="/download" method="get">
                        <input type="text" name="code" placeholder="6-digit code" maxlength="{CODE_LENGTH}" required pattern="\\d{{{CODE_LENGTH}}}" title="Enter the {CODE_LENGTH}-digit code">
                        <button type="submit">Download</button>
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))

        elif parsed_path.path == '/download':
            # Handle the download attempt
            entered_code = query_params.get('code', [None])[0]

            if entered_code != self.correct_code:
                print(f"Incorrect code '{entered_code}' received.")
                # Redirect back to the form with an error flag
                self.send_response(302) # Found (Redirect)
                self.send_header('Location', '/?error=1')
                self.end_headers()
                return

            print(f"Correct code '{entered_code}' received. Preparing download...")
            if not os.path.isfile(self.file_path):
                print(f"Error: File not found at path: {self.file_path}")
                self.send_error(404, "File not found on server.")
                # Signal shutdown because the attempt was made with the correct code
                self.shutdown_event_ref.set()
                return

            try:
                self.send_response(200)
                self.send_header("Content-Type", 'application/octet-stream')
                # Use the configured download filename
                self.send_header("Content-Disposition", f'attachment; filename="{self.download_filename}"')
                with open(self.file_path, 'rb') as f:
                    fs = os.fstat(f.fileno())
                    self.send_header("Content-Length", str(fs.st_size))
                    self.end_headers()

                    # Stream the file
                    self.copyfile(f, self.wfile)

                print(f"File '{self.file_path}' sent successfully.")
                print("Signaling server shutdown...")
                # Signal the main thread to shut down the server AFTER sending the file
                self.shutdown_event_ref.set()


            except Exception as e:
                print(f"Error sending file: {e}")
                self.send_error(500, f"Error serving file: {e}")
                # Still signal shutdown even if file sending failed after starting
                self.shutdown_event_ref.set()
                    
        else:
            # Handle other paths
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        """Optionally suppress standard logging"""
        # Uncomment the next line to suppress GET/POST logging
        # return
        super().log_message(format, *args)


def generate_code(length):
    """Generates a random numeric code."""
    return ''.join(random.choices(string.digits, k=length))

def get_lan_ip():
    """
    Finds the local LAN IP address of the machine.
    Works on Linux and macOS by connecting to an external address.
    Returns the IP address as a string, or '127.0.0.1' if unable to determine.
    """
    s = None
    try:
        # Create a UDP socket (SOCK_DGRAM)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set a timeout to avoid hanging indefinitely if the network is down
        s.settimeout(0.1)
        # Connect to a known external server (doesn't actually send data)
        # Using Google's public DNS server IP on port 80
        s.connect(("8.8.8.8", 80))
        # Get the socket's own address
        ip_address = s.getsockname()[0]
        return ip_address
    except Exception as e:
        print(f"Warning: Could not automatically determine LAN IP: {e}. Falling back to localhost.")
        # Fallback if detection fails
        return "127.0.0.1"
    finally:
        if s:
            s.close()


def run_server(port, file_path, download_filename, code, event):
    """Sets up and runs the HTTP server."""
    # Assert that the file exists and is a file
    assert os.path.isfile(file_path), f"File to serve not found at '{file_path}'. Please check the --file in the script."

    # Use functools.partial to pass arguments to the handler's constructor
    handler = partial(FileDownloadHandler,
                      correct_code=code,
                      file_path=file_path,
                      download_filename=download_filename,
                      shutdown_event_ref=event)

    # Use ThreadingTCPServer for better handling of shutdown
    lan_ip = get_lan_ip()
    with socketserver.ThreadingTCPServer((lan_ip, port), handler) as httpd:
        print(f"\n--- Single File Download Server ---")
        print(f"Serving file: {file_path}")
        print(f"Download requires code: {code}")
        print(f"Server started on http://{lan_ip}:{port}")
        print(f"-----------------------------------\n")
        print("Waiting for connection...")

        # Start the server loop (will block here until shutdown)
        httpd.serve_forever()

        # This part executes after httpd.shutdown() is called
        print("\nServer loop exited.")


if __name__ == "__main__":
    # Generate the secret code
    secret_code = generate_code(CODE_LENGTH)

    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, args=(PORT, FILE_TO_SERVE, DOWNLOAD_FILENAME, secret_code, shutdown_event))
    server_thread.daemon = True # Allows main thread to exit even if server thread is running (though we wait)
    server_thread.start()

    # Wait in the main thread until the shutdown event is set by the handler
    shutdown_event.wait()

    print("Shutdown event received by main thread. Shutting down server...")

    # The server's `serve_forever` is running in `server_thread`.
    # We need to tell the server object (which lives in that thread's context)
    # to shut down. Since we used ThreadingTCPServer and passed the event,
    # the handler calling event.set() allows this main thread to proceed.
    # We still need to properly shut down the server instance itself.
    # The `with` statement in `run_server` handles `server_close`.
    # We need to call `shutdown` on the server instance, but we don't have
    # a direct reference here. The `shutdown_event.wait()` unblocks us,
    # and the `with` block context manager in `run_server` will handle the shutdown
    # when `serve_forever` returns (which it should after the event).

    # Let's give the server thread a moment to process the shutdown
    time.sleep(0.5)

    print("Server has been shut down.")
    # Optional: Wait for the server thread to finish completely
    # server_thread.join()
    print("Exiting script.")
