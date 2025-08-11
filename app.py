# app.py - Professional Video Cutter with Vikas Features
from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import uuid
from datetime import datetime
import subprocess
import shutil
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Vikas Feature: Enhanced configuration settings
app.config['UPLOAD_FOLDER'] = 'vikas_uploads'
app.config['PROCESSED_FOLDER'] = 'vikas_processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
app.config['MAX_FILE_AGE'] = 3600  # 1 hour in seconds

# Vikas Feature: Create necessary directories with permissions
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Set permissions (works on Unix-like systems)
try:
    os.chmod(app.config['UPLOAD_FOLDER'], 0o777)
    os.chmod(app.config['PROCESSED_FOLDER'], 0o777)
except:
    pass  # Skip if on Windows or permission change fails

# Vikas Feature: Configure logging
logging.basicConfig(filename='vikas_video_cutter.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Vikas Feature: Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Vikas Feature: Cleanup old files
def cleanup_old_files():
    try:
        now = datetime.now().timestamp()
        for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = now - os.path.getctime(file_path)
                    if file_age > app.config['MAX_FILE_AGE']:
                        os.remove(file_path)
                        logging.info(f"Vikas Cleanup: Removed old file {filename}")
    except Exception as e:
        logging.error(f"Vikas Cleanup Error: {str(e)}")

# Vikas Feature: Main route
@app.route('/')
def index():
    cleanup_old_files()  # Cleanup before serving
    return render_template('index.html', 
                           current_year=datetime.now().year,
                           video_file=None,
                           error=None)

# Vikas Feature: Video processing route
@app.route('/process', methods=['POST'])
def process_video():
    cleanup_old_files()  # Cleanup before processing
    
    # Check if file was uploaded
    if 'video' not in request.files:
        return render_template('index.html', 
                               error="❌ कोई फाइल अपलोड नहीं हुई!",
                               current_year=datetime.now().year)
    
    video_file = request.files['video']
    
    # Check if file is selected
    if video_file.filename == '':
        return render_template('index.html', 
                               error="❌ फाइल का नाम खाली है!",
                               current_year=datetime.now().year)
    
    # Check if file is allowed
    if not (video_file and allowed_file(video_file.filename)):
        return render_template('index.html', 
                               error="❌ गलत फाइल प्रकार! केवल MP4, MOV, AVI, MKV, WEBM स्वीकार्य हैं।",
                               current_year=datetime.now().year)
    
    try:
        # Generate unique filename with Vikas prefix
        original_filename = secure_filename(video_file.filename)
        filename = f"vikas_{uuid.uuid4().hex}_{original_filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(upload_path)
        
        # Get start and end times
        start_time = float(request.form['start_time'])
        end_time = float(request.form['end_time'])
        
        # Validate times
        if start_time < 0 or end_time < 0:
            return render_template('index.html', 
                                   error="❌ समय ऋणात्मक नहीं हो सकता!",
                                   current_year=datetime.now().year)
        
        if start_time >= end_time:
            return render_template('index.html', 
                                   error="❌ अंत समय शुरू समय से अधिक होना चाहिए!",
                                   current_year=datetime.now().year)
        
        # Process video
        output_filename = f"vikas_trimmed_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Vikas Feature: Video trimming using FFmpeg (more reliable)
        try:
            # First try with moviepy if available
            try:
                from moviepy.editor import VideoFileClip
                with VideoFileClip(upload_path) as video:
                    if end_time > video.duration:
                        end_time = video.duration
                    trimmed = video.subclip(start_time, end_time)
                    trimmed.write_videofile(output_path, codec='libx264', audio_codec='aac')
            except ImportError:
                # Fallback to FFmpeg if moviepy not available
                cmd = [
                    'ffmpeg',
                    '-i', upload_path,
                    '-ss', str(start_time),
                    '-to', str(end_time),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    output_path
                ]
                subprocess.run(cmd, check=True)
            
            logging.info(f"Vikas Success: Processed {original_filename} ({start_time}-{end_time}s)")
            return render_template('index.html', 
                                   video_file=output_filename,
                                   current_year=datetime.now().year)
        
        except Exception as e:
            logging.error(f"Vikas Processing Error: {str(e)}")
            return render_template('index.html', 
                                   error=f"⚠️ वीडियो प्रोसेसिंग में त्रुटि: {str(e)}",
                                   current_year=datetime.now().year)
    
    except Exception as e:
        logging.error(f"Vikas System Error: {str(e)}")
        return render_template('index.html', 
                               error=f"⚠️ सिस्टम त्रुटि: {str(e)}",
                               current_year=datetime.now().year)

# Vikas Feature: Download route
@app.route('/download/<filename>')
def download_file(filename):
    try:
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            return render_template('index.html', 
                                   error="❌ फाइल नहीं मिली!",
                                   current_year=datetime.now().year)
    except Exception as e:
        logging.error(f"Vikas Download Error: {str(e)}")
        return render_template('index.html', 
                               error=f"⚠️ डाउनलोड त्रुटि: {str(e)}",
                               current_year=datetime.now().year)

# Vikas Feature: Cleanup route
@app.route('/cleanup', methods=['GET'])
def cleanup():
    try:
        # Remove all files in upload and processed folders
        for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        # Recreate folders
        shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
        shutil.rmtree(app.config['PROCESSED_FOLDER'], ignore_errors=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
        
        return "✅ विकास सफाई सफल: सभी फाइलें हटा दी गईं!"
    except Exception as e:
        logging.error(f"Vikas Cleanup Error: {str(e)}")
        return f"❌ विकास सफाई विफल: {str(e)}", 500

if __name__ == '__main__':
    # Vikas Feature: Check if FFmpeg is available
    try:
        ffmpeg_check = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if "ffmpeg version" in ffmpeg_check.stdout:
            logging.info("Vikas System: FFmpeg is available")
        else:
            logging.warning("Vikas System: FFmpeg not found, using fallback methods")
    except:
        logging.warning("Vikas System: FFmpeg check failed")
    
    # Run the app
    app.run(host='0.0.0.0', port=8080, debug=True)