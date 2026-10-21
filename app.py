import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "naijamusic_secret_key_2026"

# Folder to temporarily store uploaded files
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Temporary list to store song uploads during session
songs_database = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_song():
    artist = request.form.get('artist')
    song_title = request.form.get('song_title')
    audio_file = request.files.get('audio_file')
    cover_art = request.files.get('cover_art')
    social_links = request.form.get('social_links')

    if audio_file and cover_art and artist and song_title:
        audio_filename = secure_filename(audio_file.filename)
        cover_filename = secure_filename(cover_art.filename)
        
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        cover_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_filename)
        
        audio_file.save(audio_path)
        cover_art.save(cover_path)

        song_data = {
            "artist": artist,
            "song_title": song_title,
            "audio_url": f"/static/uploads/{audio_filename}",
            "cover_url": f"/static/uploads/{cover_filename}",
            "social_links": social_links if social_links else "Not Provided",
            "status": "Queued for DSP Distribution"
        }
        songs_database.append(song_data)
        
        flash("Song uploaded successfully! Deployment queued.")
        return redirect(url_for('dashboard'))

    flash("Please fill in all required fields and select both audio and cover files.")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', songs=songs_database)

if __name__ == '__main__':
    app.run(debug=True)
