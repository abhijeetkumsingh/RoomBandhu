"""
RoomBandhu — Production Flask Application
==========================================
Student room listing platform for Bihar & beyond.
Author: Abhijeet Kumar Singh
"""

import os, uuid, json, random, string
from datetime import datetime, timedelta
from functools import wraps
from math import radians, sin, cos, sqrt, atan2

from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth

# ─────────────────────────────────────────
#  APP & CONFIG
# ─────────────────────────────────────────

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Load .env in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Core
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rb-dev-secret-change-in-prod-2024')
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = (os.environ.get('FLASK_ENV') == 'production')

# Database
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif _db_url.startswith('postgresql://'):
    _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
else:
    _db_url = 'sqlite:///' + os.path.join(basedir, 'roombandhu.db')

app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 300}

# Uploads
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mail
app.config.update(
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS  = True,
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', ''),
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', ''),
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'RoomBandhu <noreply@roombandhu.com>'),
)

# Admin
ADMIN_EMAIL    = os.environ.get('ADMIN_EMAIL', 'admin@roombandhu.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@Secure123')

# Extensions
db    = SQLAlchemy(app)
csrf  = CSRFProtect(app)
mail  = Mail(app)
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id     = os.environ.get('GOOGLE_CLIENT_ID', ''),
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url = 'https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs = {'scope': 'openid email profile'},
)

# ─────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'user'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone       = db.Column(db.String(15), nullable=True)
    password    = db.Column(db.String(256), nullable=True)        # nullable for Google users
    google_id   = db.Column(db.String(128), unique=True, nullable=True)
    avatar_url  = db.Column(db.String(300), nullable=True)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    rooms       = db.relationship('Room',     backref='owner', lazy='select')
    wishlist    = db.relationship('Wishlist', backref='user',  lazy='select')
    reviews     = db.relationship('Review',   backref='user',  lazy='select')


class Room(db.Model):
    __tablename__ = 'room'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    rent         = db.Column(db.Integer,     nullable=False)
    room_type    = db.Column(db.String(20),  nullable=False)
    location     = db.Column(db.String(200), nullable=False)
    area         = db.Column(db.String(100), nullable=True)
    latitude     = db.Column(db.Float, nullable=True)
    longitude    = db.Column(db.Float, nullable=True)
    phone        = db.Column(db.String(15),  nullable=False)
    description  = db.Column(db.Text,        nullable=True)
    facilities   = db.Column(db.Text,        nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images       = db.relationship('RoomImage', backref='room', lazy='select',
                                   cascade='all, delete-orphan')
    reviews      = db.relationship('Review',    backref='room', lazy='select',
                                   cascade='all, delete-orphan')
    wishlisted   = db.relationship('Wishlist',  backref='room', lazy='select',
                                   cascade='all, delete-orphan')

    def avg_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.stars for r in self.reviews) / len(self.reviews), 1)

    def facilities_list(self):
        try:
            return json.loads(self.facilities or '[]')
        except Exception:
            return []


class RoomImage(db.Model):
    __tablename__ = 'room_image'
    id         = db.Column(db.Integer, primary_key=True)
    room_id    = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    filename   = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)


class Review(db.Model):
    __tablename__ = 'review'
    id         = db.Column(db.Integer, primary_key=True)
    room_id    = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stars      = db.Column(db.Integer, nullable=False)
    text       = db.Column(db.Text,    nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)


class OTPToken(db.Model):
    """6-digit OTP for password reset — expires in 10 minutes."""
    __tablename__ = 'otp_token'
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), nullable=False)
    otp        = db.Column(db.String(6),   nullable=False)
    expires_at = db.Column(db.DateTime,    nullable=False)
    used       = db.Column(db.Boolean, default=False)

    @property
    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def safe_image(fs):
    """Magic-byte check to reject non-images despite extension."""
    header = fs.read(8)
    fs.seek(0)
    return (header[:3] == b'\xff\xd8\xff' or   # JPEG
            header[:4] == b'\x89PNG' or          # PNG
            header[:4] == b'RIFF')               # WebP

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    uid = session.get('user_id')
    if uid:
        return db.session.get(User, uid)
    return None

def send_otp_email(email, otp):
    try:
        msg = Message(
            subject='🔐 RoomBandhu — Password Reset OTP',
            recipients=[email],
            html=f"""
            <div style="font-family:sans-serif;max-width:460px;margin:auto;
                        padding:32px;background:#fff;border-radius:12px;border:1px solid #eee">
              <h2 style="color:#e05c2c;margin-bottom:4px">🏠 RoomBandhu</h2>
              <p style="color:#555">Your one-time OTP to reset your password:</p>
              <div style="font-size:40px;font-weight:900;letter-spacing:10px;
                          color:#e05c2c;padding:20px 0;text-align:center">{otp}</div>
              <p style="color:#888;font-size:13px">
                This OTP expires in <strong>10 minutes</strong>.<br>
                If you didn't request this, ignore this email.
              </p>
            </div>"""
        )
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f'Mail error: {e}')
        return False

def gen_otp():
    return ''.join(random.choices(string.digits, k=6))


# ─────────────────────────────────────────
#  CONTEXT PROCESSOR
# ─────────────────────────────────────────

@app.context_processor
def globals():
    count = 0
    if 'user_id' in session:
        count = Wishlist.query.filter_by(user_id=session['user_id']).count()
    return {'wishlist_count': count}


# ─────────────────────────────────────────
#  AUTH ROUTES
# ─────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip().lower()
        phone   = request.form.get('phone', '').strip()
        pw      = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not name or not email or not pw:
            flash('Please fill all required fields', 'error')
            return redirect(url_for('register'))
        if len(pw) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('register'))
        if pw != confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('login'))

        user = User(name=name, email=email, phone=phone,
                    password=generate_password_hash(pw, method='pbkdf2:sha256'))
        db.session.add(user)
        db.session.commit()
        session.permanent = True
        session['user_id']   = user.id
        session['user_name'] = user.name
        flash(f'Welcome to RoomBandhu, {user.name}! 🎉', 'success')
        return redirect(url_for('dashboard'))

    return render_template('auth.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')

        user = User.query.filter(db.func.lower(User.email) == email).first()
        if not user:
            flash('No account found. Please register first.', 'error')
            return redirect(url_for('register'))
        if user.google_id and not user.password:
            flash('This account uses Google Sign-In. Please use the Google button.', 'error')
            return redirect(url_for('login'))
        if not user.password or not check_password_hash(user.password, pw):
            flash('Incorrect password. Try again.', 'error')
            return redirect(url_for('login'))
        if not user.is_active:
            flash('Your account has been suspended. Contact support.', 'error')
            return redirect(url_for('login'))

        session.clear()
        session.permanent = True
        session['user_id']   = user.id
        session['user_name'] = user.name
        flash(f'Welcome back, {user.name}! 👋', 'success')
        return redirect(url_for('dashboard'))

    return render_template('auth.html', mode='login')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))


# ── Google OAuth ──────────────────────────────────────────────────

@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    try:
        token     = google.authorize_access_token()
        info      = token.get('userinfo') or {}
        email     = info.get('email', '').lower()
        google_id = info.get('sub', '')
        name      = info.get('name', email.split('@')[0])
        avatar    = info.get('picture', '')

        if not email:
            flash('Google login failed — no email returned.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id  = user.google_id or google_id
            user.avatar_url = avatar
            db.session.commit()
        else:
            user = User(name=name, email=email, google_id=google_id,
                        avatar_url=avatar, password=None)
            db.session.add(user)
            db.session.commit()

        session.clear()
        session.permanent = True
        session['user_id']   = user.id
        session['user_name'] = user.name
        flash(f'Welcome, {user.name}! 🎉', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f'Google OAuth error: {e}')
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))


# ── Forgot / Reset Password (OTP Flow) ───────────────────────────

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()

        if user and user.is_active:
            OTPToken.query.filter_by(email=email, used=False).update({'used': True})
            db.session.commit()
            otp   = gen_otp()
            token = OTPToken(email=email, otp=otp,
                             expires_at=datetime.utcnow() + timedelta(minutes=10))
            db.session.add(token)
            db.session.commit()
            sent = send_otp_email(email, otp)
            if not sent and os.environ.get('FLASK_ENV') != 'production':
                flash(f'[DEV] OTP: {otp}', 'success')

        flash('If that email is registered, an OTP was sent to it.', 'success')
        session['_reset_email'] = email
        return redirect(url_for('verify_otp'))

    return render_template('forgot_password.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('_reset_email')
    if not email:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        token = (OTPToken.query
                 .filter_by(email=email, otp=entered, used=False)
                 .order_by(OTPToken.id.desc()).first())
        if not token or not token.is_valid:
            flash('Invalid or expired OTP. Request a new one.', 'error')
            return redirect(url_for('verify_otp'))
        token.used = True
        db.session.commit()
        session.pop('_reset_email', None)
        session['_otp_verified'] = email
        return redirect(url_for('reset_password'))

    return render_template('verify_otp.html', email=email)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('_otp_verified')
    if not email:
        flash('Session expired. Please start again.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        pw      = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(pw) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('reset_password'))
        if pw != confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('reset_password'))
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(pw, method='pbkdf2:sha256')
            db.session.commit()
        session.pop('_otp_verified', None)
        flash('Password reset! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')


# ── Profile ───────────────────────────────────────────────────────

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = get_current_user()
    if request.method == 'POST':
        user.name  = request.form.get('name', user.name).strip()
        user.phone = request.form.get('phone', user.phone or '').strip()
        db.session.commit()
        session['user_name'] = user.name
        flash('Profile updated!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_profile.html', user=user)


@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    user    = get_current_user()
    current = request.form.get('current_password', '')
    new_pw  = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    if user.password and not check_password_hash(user.password, current):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('edit_profile'))
    if len(new_pw) < 6:
        flash('New password must be at least 6 characters', 'error')
        return redirect(url_for('edit_profile'))
    if new_pw != confirm:
        flash('Passwords do not match', 'error')
        return redirect(url_for('edit_profile'))

    user.password = generate_password_hash(new_pw, method='pbkdf2:sha256')
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('dashboard'))


# ─────────────────────────────────────────
#  MAIN ROUTES
# ─────────────────────────────────────────

@app.route('/')
def home():
    room_type = request.args.get('type', 'All')
    max_price = request.args.get('max_price', 0, type=int)
    sort      = request.args.get('sort', 'default')
    query     = request.args.get('q', '').strip()

    q = Room.query.filter_by(is_available=True)
    if query:
        q = q.filter(db.or_(
            Room.title.ilike(f'%{query}%'),
            Room.location.ilike(f'%{query}%'),
            Room.area.ilike(f'%{query}%'),
            Room.description.ilike(f'%{query}%')
        ))
    if room_type != 'All':
        q = q.filter_by(room_type=room_type)
    if max_price:
        q = q.filter(Room.rent <= max_price)

    rooms = q.all()
    if sort == 'price-asc':
        rooms.sort(key=lambda r: r.rent)
    elif sort == 'price-desc':
        rooms.sort(key=lambda r: -r.rent)
    elif sort == 'rating':
        rooms.sort(key=lambda r: -r.avg_rating())
    else:
        rooms.sort(key=lambda r: -r.id)

    wish_ids = []
    if 'user_id' in session:
        wish_ids = [w.room_id for w in
                    Wishlist.query.filter_by(user_id=session['user_id']).all()]

    return render_template('index.html', rooms=rooms, wish_ids=wish_ids,
                           active_type=room_type, query=query,
                           max_price=max_price, sort=sort)


@app.route('/room/<int:room_id>')
def room_detail(room_id):
    room = db.get_or_404(Room, room_id)
    user = get_current_user()
    wish_ids = []
    if user:
        wish_ids = [w.room_id for w in Wishlist.query.filter_by(user_id=user.id).all()]
    already_reviewed = bool(user and
        Review.query.filter_by(room_id=room_id, user_id=user.id).first())
    return render_template('room_detail.html', room=room, user=user,
                           wish_ids=wish_ids, already_reviewed=already_reviewed)


# ─────────────────────────────────────────
#  ROOM MANAGEMENT
# ─────────────────────────────────────────

@app.route('/add_room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        rent_str    = request.form.get('rent', '0')
        room_type   = request.form.get('room_type', 'Single')
        location    = request.form.get('location', '').strip()
        area        = request.form.get('area', '').strip()
        phone       = request.form.get('phone', '').strip()
        description = request.form.get('description', '').strip()
        facilities  = request.form.getlist('facilities')
        lat         = request.form.get('latitude', '')
        lng         = request.form.get('longitude', '')

        try:
            rent = int(rent_str)
            assert rent >= 100
        except (ValueError, AssertionError):
            flash('Please enter a valid rent amount (minimum ₹100)', 'error')
            return redirect(url_for('add_room'))

        # Validate images
        raw_images   = request.files.getlist('images')
        valid_images = []
        for img in raw_images:
            if img and img.filename and allowed_file(img.filename) and safe_image(img):
                valid_images.append(img)

        if len(valid_images) < 4:
            flash('Please upload at least 4 valid room photos (JPG/PNG/WebP)', 'error')
            return redirect(url_for('add_room'))

        room = Room(title=title, rent=rent, room_type=room_type,
                    location=location, area=area, phone=phone,
                    description=description,
                    facilities=json.dumps(facilities),
                    latitude=float(lat) if lat else None,
                    longitude=float(lng) if lng else None,
                    user_id=session['user_id'])
        db.session.add(room)
        db.session.flush()

        for i, img in enumerate(valid_images):
            ext  = img.filename.rsplit('.', 1)[1].lower()
            name = f"{uuid.uuid4().hex}.{ext}"
            img.save(os.path.join(UPLOAD_FOLDER, name))
            db.session.add(RoomImage(room_id=room.id, filename=name, is_primary=(i == 0)))

        db.session.commit()
        flash('Room listed successfully! 🎉', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_room.html')


@app.route('/delete_room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = db.get_or_404(Room, room_id)
    if room.user_id != session['user_id']:
        flash('Not authorised', 'error')
        return redirect(url_for('dashboard'))
    for img in room.images:
        p = os.path.join(UPLOAD_FOLDER, img.filename)
        if os.path.exists(p):
            os.remove(p)
    db.session.delete(room)
    db.session.commit()
    flash('Room listing deleted', 'success')
    return redirect(url_for('dashboard'))


@app.route('/toggle_availability/<int:room_id>', methods=['POST'])
@login_required
def toggle_availability(room_id):
    room = db.get_or_404(Room, room_id)
    if room.user_id != session['user_id']:
        return jsonify({'error': 'Not authorised'}), 403
    room.is_available = not room.is_available
    db.session.commit()
    return jsonify({'available': room.is_available})


# ─────────────────────────────────────────
#  WISHLIST
# ─────────────────────────────────────────

@app.route('/wishlist/toggle/<int:room_id>', methods=['POST'])
@login_required
def toggle_wishlist(room_id):
    uid = session['user_id']
    w   = Wishlist.query.filter_by(user_id=uid, room_id=room_id).first()
    if w:
        db.session.delete(w)
        db.session.commit()
        return jsonify({'saved': False,
                        'count': Wishlist.query.filter_by(user_id=uid).count()})
    db.session.add(Wishlist(user_id=uid, room_id=room_id))
    db.session.commit()
    return jsonify({'saved': True,
                    'count': Wishlist.query.filter_by(user_id=uid).count()})


@app.route('/wishlist')
@login_required
def wishlist():
    user  = get_current_user()
    items = Wishlist.query.filter_by(user_id=user.id).all()
    rooms = [i.room for i in items]
    return render_template('wishlist.html', rooms=rooms, user=user)


# ─────────────────────────────────────────
#  REVIEWS
# ─────────────────────────────────────────

@app.route('/review/<int:room_id>', methods=['POST'])
@login_required
def add_review(room_id):
    if Review.query.filter_by(room_id=room_id, user_id=session['user_id']).first():
        flash('You have already reviewed this room', 'error')
        return redirect(url_for('room_detail', room_id=room_id))
    try:
        stars = int(request.form.get('stars', 0))
        assert 1 <= stars <= 5
    except (ValueError, AssertionError):
        flash('Please select a star rating', 'error')
        return redirect(url_for('room_detail', room_id=room_id))
    text = request.form.get('text', '').strip()
    if not text:
        flash('Review cannot be empty', 'error')
        return redirect(url_for('room_detail', room_id=room_id))
    db.session.add(Review(room_id=room_id, user_id=session['user_id'],
                           stars=stars, text=text))
    db.session.commit()
    flash('Review submitted! ⭐', 'success')
    return redirect(url_for('room_detail', room_id=room_id))


# ─────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))
    my_rooms   = Room.query.filter_by(user_id=user.id).order_by(Room.created_at.desc()).all()
    wish_count = Wishlist.query.filter_by(user_id=user.id).count()
    return render_template('dashboard.html', user=user,
                           my_rooms=my_rooms, wish_count=wish_count)


# ─────────────────────────────────────────
#  ADMIN
# ─────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')
        if email == ADMIN_EMAIL.lower() and pw == ADMIN_PASSWORD:
            session['is_admin']    = True
            session['admin_email'] = email
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_email', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html',
        total_users   = User.query.count(),
        total_rooms   = Room.query.count(),
        avail_rooms   = Room.query.filter_by(is_available=True).count(),
        total_reviews = Review.query.count(),
        recent_users  = User.query.order_by(User.created_at.desc()).limit(10).all(),
        recent_rooms  = Room.query.order_by(Room.created_at.desc()).limit(10).all(),
    )


@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/rooms')
@admin_required
def admin_rooms():
    rooms = Room.query.order_by(Room.created_at.desc()).all()
    return render_template('admin/rooms.html', rooms=rooms)


@app.route('/admin/delete_room/<int:room_id>', methods=['POST'])
@admin_required
def admin_delete_room(room_id):
    room = db.get_or_404(Room, room_id)
    for img in room.images:
        p = os.path.join(UPLOAD_FOLDER, img.filename)
        if os.path.exists(p):
            os.remove(p)
    db.session.delete(room)
    db.session.commit()
    flash(f'Listing "{room.title}" deleted', 'success')
    return redirect(url_for('admin_rooms'))


@app.route('/admin/toggle_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "suspended"}', 'success')
    return redirect(url_for('admin_users'))


# ─────────────────────────────────────────
#  API
# ─────────────────────────────────────────

@app.route('/api/nearby')
def nearby_rooms():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if not lat or not lng:
        return jsonify({'error': 'lat/lng required'}), 400

    rooms = Room.query.filter(
        Room.latitude.isnot(None), Room.longitude.isnot(None),
        Room.is_available == True
    ).all()

    def dist(r):
        R    = 6371
        dlat = radians(r.latitude - lat)
        dlon = radians(r.longitude - lng)
        a    = (sin(dlat/2)**2 +
                cos(radians(lat)) * cos(radians(r.latitude)) * sin(dlon/2)**2)
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    nearby = sorted([(r, dist(r)) for r in rooms], key=lambda x: x[1])[:10]
    return jsonify([{
        'id': r.id, 'title': r.title, 'rent': r.rent,
        'location': r.location, 'type': r.room_type,
        'distance_km': round(d, 2), 'rating': r.avg_rating(),
        'image': r.images[0].filename if r.images else None
    } for r, d in nearby])


# ─────────────────────────────────────────
#  ERROR HANDLERS
# ─────────────────────────────────────────

@app.errorhandler(404)
def e404(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(413)
def e413(e):
    flash('Upload too large. Max 16MB.', 'error')
    return redirect(request.referrer or url_for('home'))

@app.errorhandler(500)
def e500(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ─────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────

with app.app_context():
    try:
        db.create_all()
        app.logger.info('✅ DB tables created/verified')
    except Exception as e:
        app.logger.error(f'DB init error: {e}')

if __name__ == '__main__':
    app.run(debug=(os.environ.get('FLASK_ENV') != 'production'), host='0.0.0.0')
