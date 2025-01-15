import os
import subprocess
from flask import Flask, send_from_directory

# Initialize Flask app
app = Flask(__name__)

# Define HLS output directory
HLS_DIR = "hls"
os.makedirs(HLS_DIR, exist_ok=True)

# FFmpeg command to generate low-latency HLS stream
ffmpeg_command = [
    'ffmpeg',
    '-f', 'pulse',  # Audio input from PulseAudio
    '-i', 'alsa_output.usb-VIA_Technologies_Inc._VIA_USB_Device-00.analog-stereo.monitor',  # Update as needed
    '-f', 'v4l2',  # Video input from video4linux2
    '-i', '/dev/video0',  # Your OBS virtual camera device
    '-c:v', 'libx264',  # Encode video with H.264
    '-preset', 'ultrafast',  # Faster encoding for real-time
    '-tune', 'zerolatency',  # Optimize for low latency
    '-c:a', 'aac',  # Encode audio with AAC
    '-f', 'hls',  # Output format as HLS
    '-hls_time', '0.5',  # 0.5-second segments for low latency
    '-hls_list_size', '2',  # Keep the last 5 segments in the playlist
    '-hls_flags', 'delete_segments+append_list',  # Delete old segments and update the playlist dynamically
    os.path.join(HLS_DIR, 'stream.m3u8')  # Output HLS playlist
]

# Start FFmpeg process
subprocess.Popen(ffmpeg_command)


# Serve the HLS stream files
@app.route('/hls/<path:filename>')
def serve_hls(filename):
    return send_from_directory(HLS_DIR, filename)


# Main route for testing
@app.route('/')
def index():
    # Simple HTML page to display the video stream
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Low-Latency Camera Streaming Server</title>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    </head>
    <body>
        <h1>Low-Latency Camera Streaming Server</h1>
        <video id="video" autoplay muted controls style="max-width: 100%;">
            Your browser does not support the video tag.
        </video>
        <script>
            var video = document.getElementById('video');
            if (Hls.isSupported()) {
                var hls = new Hls({
                    lowLatencyMode: true,
                    maxLiveSyncPlaybackRate: 2.0
                });
                hls.loadSource('/hls/stream.m3u8');
                hls.attachMedia(video);

                hls.on(Hls.Events.MANIFEST_PARSED, function () {
                    video.play();
                });
                hls.on(Hls.Events.FRAG_BUFFERED, function () {
                    hls.latencyController.setLiveEdge();
                });
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = '/hls/stream.m3u8';
                video.addEventListener('loadedmetadata', function () {
                    video.currentTime = video.duration;
                    video.play();
                });
            }
        </script>
    </body>
    </html>
    '''


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
