# Server: Flask with WebSockets for live streaming
from flask import Flask, Response, render_template
from flask_sock import Sock
import cv2
import numpy as np
import threading

app = Flask(__name__)
sock = Sock(app)

frame_lock = threading.Lock()  # Ensure thread safety
frame = None  # Store latest frame

@app.route('/')
def index():
    return render_template('index.html')  # Serve the HTML page

@app.route('/better')
def better():
    return render_template('better.html')  # Serve the HTML page


@app.route('/video_feed')
def video_feed():
    def generate():
        global frame
        while True:
            with frame_lock:
                if frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' +
                           buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@sock.route('/stream')
def stream(ws):
    global frame
    while True:
        try:
            data = ws.receive()
            if data is None:
                continue  # Prevent errors when data is None

            np_data = np.frombuffer(data, np.uint8)
            decoded_frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

            if decoded_frame is not None:
                with frame_lock:
                    frame = decoded_frame  # Safely update the frame

        except Exception as e:
            print(f"WebSocket Error: {e}")
            break

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)  # Enable threading
