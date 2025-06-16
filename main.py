from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import os
import asyncio
import shutil
import uuid
from ml_models import interview_models
import requests
import traceback
from gtts import gTTS
from vosk import Model, KaldiRecognizer
import wave
import threading
import time
import subprocess

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:praSAD000%40%40%40@db.coyaezvojwljttxuamvo.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=7)

# Initialize Database
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def __repr__(self):
        return f'<User {self.email}>'

# Create all database tables
with app.app_context():
    db.create_all()

AUDIO_PROMPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'myaudio.wav'))

def generate_tts_audio(text):
    # Use gTTS to generate TTS audio (female voice by default)
    tts = gTTS(text=text, lang='en', slow=False, tld='co.in')  # tld='co.in' is Indian English, female by default
    unique_name = f"tts_{uuid.uuid4().hex}.mp3"
    save_path = os.path.join('data', 'tts_audio', unique_name)
    tts.save(save_path)
    print('[TTS DEBUG] gTTS saved audio to:', save_path)
    return save_path

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session.permanent = True
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user']).first()
    return render_template('dashboard.html', user=user)

@app.route('/interview')
def interview():
    if 'user' not in session:
        flash('Please login to access the interview', 'error')
        return redirect(url_for('login'))
    
    job_role = request.args.get('jobRole', '')
    difficulty = request.args.get('difficulty', '')
    
    # Get user's name
    user = User.query.filter_by(email=session['user']).first()
    intro_message = f"Hi, I'm Pehvi, your AI mock interviewer. Can you tell me about yourself?"
    
    return render_template('interview.html', 
                         job_role=job_role, 
                         difficulty=difficulty,
                         intro_message=intro_message,
                         is_intro=True)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'user' not in session:
        return jsonify({'error': 'Please login to submit answers'}), 401
    
    question = request.form.get('question')
    user_answer = request.form.get('answer')
    job_role = request.form.get('jobRole')
    difficulty = request.form.get('difficulty')
    
    if not question or not user_answer or not job_role or not difficulty:
        return jsonify({'error': 'Question, answer, job role and difficulty are required'}), 400
    
    # Get context for the selected job role and difficulty
    context = interview_models.get_context(job_role, difficulty)
    if not context:
        return jsonify({'error': 'No context available for this job role and difficulty'}), 400
    
    # Generate model answer and evaluate asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Generate model answer with only the question
    model_answer = loop.run_until_complete(interview_models.generate_answer(question))
    
    # Evaluate user's answer
    evaluation = loop.run_until_complete(interview_models.evaluate_answer(user_answer, model_answer))
    loop.close()
    
    return jsonify(evaluation)

@app.route('/next_question')
def next_question():
    if 'user' not in session:
        return jsonify({'error': 'Please login'}), 401
        
    job_role = request.args.get('jobRole', '')
    difficulty = request.args.get('difficulty', '')
    
    # Get context for the selected job role and difficulty
    context = interview_models.get_context(job_role, difficulty)
    if not context:
        return jsonify({'error': 'No questions available'}), 400
        
    # Generate question asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    question = loop.run_until_complete(interview_models.generate_questions(context))
    loop.close()
    
    return jsonify({'question': question})

def delayed_delete(path, delay=10):
    def delete_file():
        time.sleep(delay)
        try:
            os.remove(path)
            print(f'[TTS] Deleted audio file after delay: {path}')
        except Exception as e:
            print(f'[TTS] Error deleting audio file after delay: {e}')
    threading.Thread(target=delete_file, daemon=True).start()

@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text')
    if not text:
        print('[TTS] No text provided')
        return jsonify({'error': 'No text provided'}), 400
    try:
        audio_path = generate_tts_audio(text)
    except Exception as e:
        print('[TTS] Error in generate_tts_audio:', e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    print(f'[TTS] Requested text: {text}')
    print(f'[TTS] Audio path returned: {audio_path}')
    if not os.path.exists(audio_path):
        print('[TTS] Audio file not found:', audio_path)
        return jsonify({'error': 'Audio file not found'}), 404
    if os.path.getsize(audio_path) == 0:
        print('[TTS] Audio file is empty:', audio_path)
        return jsonify({'error': 'Audio file is empty'}), 500
    print('[TTS] Serving audio file:', audio_path)
    response = send_file(audio_path, mimetype='audio/mp3')
    delayed_delete(audio_path, delay=10)  # 10 seconds delay
    return response

# Initialize Vosk Model
vosk_model_dir = os.path.join(os.path.dirname(__file__), 'vosk-model-small-en-us-0.15')
if not os.path.exists(vosk_model_dir):
    print('Downloading Vosk model from Google Drive...')
    subprocess.run(['gdown', '--folder', 'https://drive.google.com/drive/folders/10t5gLQzQgPlwm8-1yWyYNl22tA0HbZtx?usp=drive_link', '-O', vosk_model_dir], check=True)
vosk_model = Model(vosk_model_dir)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        audio_file = request.files['audio']
        audio_path = os.path.join('data', 'uploaded_audio.wav')
        audio_file.save(audio_path)

        # Process audio with Vosk
        wf = wave.open(audio_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            return jsonify({"error": "Audio format not supported"}), 400

        rec = KaldiRecognizer(vosk_model, wf.getframerate())
        rec.SetWords(True)

        result_text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = rec.Result()
                result_text += result

        wf.close()

        # Compare with expected answer
        feedback = interview_models.compare_answer(result_text)
        return jsonify({"transcription": result_text, "feedback": feedback})

    except Exception as e:
        print("Error processing audio:", e)
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT not set
    app.run(host="0.0.0.0", port=port, debug=True)
