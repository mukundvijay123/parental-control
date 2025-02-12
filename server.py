# Optimized Flask WebSockets Server for Streaming
from flask import Flask, Response, render_template
from flask_sock import Sock
import cv2
import numpy as np
import threading
import time
import gc  # Garbage Collection

app = Flask(__name__)
sock = Sock(app)

frame_lock = threading.Lock()  # Thread safety for shared frame
frame = None  # Stores latest frame

@app.route('/')
def index():
    return render_template('index.html')  # Serve the main HTML page

@app.route('/better')
def better():
    return render_template('better.html')  # Serve the improved HTML page

@app.route('/video_feed')
def video_feed():
    """Stream video to web clients using MJPEG format."""
    def generate():
        global frame
        while True:
            with frame_lock:
                if frame is not None:
                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])  # Reduce quality for lower memory
                    if success:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' +
                               buffer.tobytes() + b'\r\n')
            time.sleep(0.05)  # Reduce CPU load (adjust as needed)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@sock.route('/stream')
def stream(ws):
    """Receive frames from clients and store the latest frame efficiently."""
    global frame
    while True:
        try:
            data = ws.receive()
            if data is None:
                continue  # Skip empty messages

            np_data = np.frombuffer(data, np.uint8)
            decoded_frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

            if decoded_frame is not None:
                with frame_lock:
                    frame = decoded_frame.copy()  # Ensure previous frame is released
                del np_data, decoded_frame  # Free memory
                gc.collect()  # Force garbage collection to prevent leaks

            time.sleep(0.05)  # Add small delay to prevent overloading

        except Exception as e:
            print(f"WebSocket Error: {e}")
            break

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)  # Enable threading
