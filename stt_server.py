import os
import queue
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import json

# Path to your Vosk model directory
MODEL_PATH = r'C:\Users\prasa\Desktop\demo\vosk-model-small-en-us-0.15\vosk-model-small-en-us-0.15'

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load Vosk model
model = Model(MODEL_PATH)

# Audio stream parameters
SAMPLE_RATE = 16000
q = queue.Queue()

# This function will run in a thread to capture audio

def audio_callback(indata, frames, time, status):
    q.put(bytes(indata))

def recognize_audio():
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            result = rec.Result()
            text = json.loads(result).get('text', '')
            if text:
                socketio.emit('stt_result', {'text': text})
        else:
            partial = rec.PartialResult()
            partial_text = json.loads(partial).get('partial', '')
            if partial_text:
                socketio.emit('stt_partial', {'text': partial_text})

@app.route('/')
def index():
    return 'Vosk STT server is running.'

@socketio.on('start_audio')
def start_audio():
    print('Starting audio stream...')
    threading.Thread(target=recognize_audio, daemon=True).start()
    sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', callback=audio_callback).start()
    emit('stt_status', {'status': 'listening'})

@socketio.on('stop_audio')
def stop_audio():
    print('Stopping audio stream...')
    sd.stop()
    emit('stt_status', {'status': 'stopped'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
