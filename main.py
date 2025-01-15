import cv2
import subprocess
from flask import Flask, Response

# Initialize Flask app
app = Flask(__name__)

# Define the command to use FFmpeg for streaming
ffmpeg_command = [
    'ffmpeg',
    '-f', 'pulse',  # Use ALSA for audio on Linux
    '-i', 'alsa_output.usb-VIA_Technologies_Inc._VIA_USB_Device-00.analog-stereo.monitor',  # Use the identified device (change as needed)
    '-f', 'v4l2',  # Use video4linux2 for video input
    '-i', '/dev/video0',  # Replace with your actual video device
    '-f', 'mpegts',
    'udp://localhost:1234'  # Stream to local UDP port
]

# Start the FFmpeg process
subprocess.Popen(ffmpeg_command)


# Function to generate frames from FFmpeg stream
def generate_frames():
    cap = cv2.VideoCapture('udp://localhost:1234')
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Encode the frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Yield the frame as a byte stream
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# Route for the video stream
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Main route for testing
@app.route('/')
def index():
    return "Camera Streaming Server. Go to /video_feed to view the stream."


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
