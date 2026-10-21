import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "lildistributs_secret_key_2026_secure"

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lildistributs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    songs = db.relationship('Song', backref='owner', lazy=True)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(100), nullable=False)
    song_title = db.Column(db.String(100), nullable=False)
    audio_url = db.Column(db.String(255), nullable=False)
    cover_url = db.Column(db.String(255), nullable=False)
    social_links = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(100), default="Queued for DSP Distribution")
    status_class = db.Column(db.String(20), default="warning")
    est_days = db.Column(db.String(50), default="2 - 5 Business Days")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or Email already registered. Please log in.")
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome back, {user.username}!")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))

# Main App Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_song():
    if 'user_id' not in session:
        flash("Please log in to upload songs.")
        return redirect(url_for('login'))

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

        if "error" in song_title.lower() or "reject" in song_title.lower():
            status = "Action Required: Re-upload Artwork"
            status_class = "danger"
            est_days = "N/A"
        else:
            status = "Queued for DSP Distribution"
            status_class = "warning"
            est_days = "2 - 5 Business Days"

        new_song = Song(
            artist=artist,
            song_title=song_title,
            audio_url=f"/static/uploads/{audio_filename}",
            cover_url=f"/static/uploads/{cover_filename}",
            social_links=social_links if social_links else "Not Provided",
            status=status,
            status_class=status_class,
            est_days=est_days,
            user_id=session['user_id']
        )

        db.session.add(new_song)
        db.session.commit()

        flash("Song uploaded successfully! Initial DSP inspection queued.")
        return redirect(url_for('dashboard'))

    flash("Please fill in all required fields.")
    return redirect(url_for('index'))

@app.route('/update_status/<int:song_id>/<action>', methods=['POST'])
def update_status(song_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    song = Song.query.filter_by(id=song_id, user_id=session['user_id']).first()
    if song:
        if action == "inspect":
            song.status = "Inspecting Metadata & Audio Quality"
            song.status_class = "info"
        elif action == "deliver":
            song.status = "Delivered to DSPs (In Store Pipeline)"
            song.status_class = "primary"
            song.est_days = "1 - 2 Days Until Live"
        elif action == "live":
            song.status = "Live in All Streaming Stores 🚀"
            song.status_class = "success"
            song.est_days = "Live Now!"
        elif action == "flag":
            song.status = "Action Required: Re-upload Artwork"
            song.status_class = "danger"
            song.est_days = "Paused"
        
        db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to view your dashboard.")
        return redirect(url_for('login'))

    user_songs = Song.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', songs=user_songs, username=session.get('username'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
