# app.py - Python backend with Vikas features
from flask import Flask, render_template, request, send_file, redirect, url_for
import os
from moviepy.editor import VideoFileClip
import uuid
from datetime import datetime

app = Flask(__name__)

# Vikas Feature: Configuration settings
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv'}
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Vikas Feature: Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Vikas Feature: Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Vikas Feature: Main route
@app.route('/')
def index():
    return render_template('index.html', 
                           current_year=datetime.now().year,
                           video_file=None)

# Vikas Feature: Video processing route
@app.route('/process', methods=['POST'])
def process_video():
    # Check if file was uploaded
    if 'video' not in request.files:
        return redirect(request.url)
    
    video_file = request.files['video']
    
    # Check if file is selected
    if video_file.filename == '':
        return redirect(request.url)
    
    # Check if file is allowed
    if video_file and allowed_file(video_file.filename):
        # Generate unique filename
        filename = f"vikas_{uuid.uuid4().hex}_{video_file.filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(upload_path)
        
        # Get start and end times
        start_time = float(request.form['start_time'])
        end_time = float(request.form['end_time'])
        
        # Process video
        output_filename = f"vikas_trimmed_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Vikas Feature: Video trimming
        try:
            with VideoFileClip(upload_path) as video:
                trimmed = video.subclip(start_time, end_time)
                trimmed.write_videofile(output_path, codec='libx264', audio_codec='aac')
        except Exception as e:
            return f"Vikas Error: Video processing failed - {str(e)}"
        
        return render_template('index.html', 
                               video_file=output_filename,
                               current_year=datetime.now().year)
    
    return redirect(request.url)

# Vikas Feature: Download route
@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename),
                     as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)