from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import time
import random

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return "Vikas AI Editor Flask Backend Running!"


# Upload media route
@app.route('/upload-media', methods=['POST'])
def upload_media():
    if 'media' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['media']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded', 'filename': filename}), 200

    return jsonify({'error': 'Invalid file type'}), 400


# Apply effect api (simulate processing)
@app.route('/process-media', methods=['POST'])
def process_media():
    data = request.json
    filename = data.get('filename')
    start = data.get('startTime')
    end = data.get('endTime')
    effect = data.get('effect')

    if not filename or not effect:
        return jsonify({'error': 'Missing data'}), 400

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    # Simulate processing by renaming
    new_filename = f"vikas_{int(time.time())}_{random.randint(1000,9999)}_{filename}"
    output_path = os.path.join(PROCESSED_FOLDER, new_filename)

    # Just copy for now (replace with real processing later)
    with open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            f_out.write(f_in.read())

    return jsonify({
        'message': f'{effect} applied successfully using Vikas Feature',
        'outputFile': new_filename
    })


# Route to download the processed file
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    print("🚀 Vikas Feature Editor Backend Started!")
    app.run(host='0.0.0.0', port=5000, debug=True)