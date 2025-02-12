import dxcam
import websockets
import asyncio
import numpy as np
import cv2
import socket
import time

# Replace with your AWS WebSocket server URL
SERVER_URL = "ws://192.168.1.20:5000/stream"

# Adjustable frame rate (Lower = smoother, Higher = lower bandwidth usage)
FRAME_RATE = 0.1  # 0.1 sec delay ~ 10 FPS

# Initialize DXGI-based screen capture
camera = dxcam.create(output_idx=0)  # Default to primary screen
camera.start(target_fps=10)  # Start capture at 10 FPS

# Function to check internet connectivity
def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# Function to capture screen using DirectX (flicker-free)
def capture_screen():
    frame = camera.get_latest_frame()  # Get latest frame (non-blocking)
    if frame is not None:
        return np.array(frame)  # Convert to NumPy array
    return None

async def send_screens():
    while True:
        while not is_internet_available():
            print("❌ No internet connection. Retrying in 5 seconds...")
            time.sleep(5)

        try:
            async with websockets.connect(SERVER_URL) as ws:
                print("✅ Connected to server. Streaming started.")
                while True:
                    frame = capture_screen()
                    if frame is not None:
                        # Convert to JPEG format with compression
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

                        # Send frame to server
                        await ws.send(buffer.tobytes())

                    await asyncio.sleep(FRAME_RATE)  # Control FPS

        except Exception as e:
            print(f"⚠️ Connection lost. Retrying... ({e})")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    asyncio.run(send_screens())
