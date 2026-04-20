from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os, uuid, json

import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")
basedir = os.path.abspath(os.path.dirname(__file__))

# ── Database Config ──────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# fix for postgres on render
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://")

# ── Upload Config ─────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ══════════════════════════════════════════
#  MODELS
# ══════════════════════════════════════════

class User(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    phone        = db.Column(db.String(15), nullable=True)
    password     = db.Column(db.String(256), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    rooms        = db.relationship('Room', backref='owner', lazy=True)
    wishlist     = db.relationship('Wishlist', backref='user', lazy=True)
    reviews      = db.relationship('Review', backref='user', lazy=True)


class Room(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    rent         = db.Column(db.Integer, nullable=False)
    room_type    = db.Column(db.String(20), nullable=False)  # Single/Shared/PG
    location     = db.Column(db.String(200), nullable=False)
    area         = db.Column(db.String(100), nullable=True)
    latitude     = db.Column(db.Float, nullable=True)
    longitude    = db.Column(db.Float, nullable=True)
    phone        = db.Column(db.String(15), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    facilities   = db.Column(db.String(500), nullable=True)  # JSON string
    is_available = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images       = db.relationship('RoomImage', backref='room', lazy=True, cascade='all, delete-orphan')
    reviews      = db.relationship('Review', backref='room', lazy=True, cascade='all, delete-orphan')
    wishlisted   = db.relationship('Wishlist', backref='room', lazy=True, cascade='all, delete-orphan')

    def avg_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.stars for r in self.reviews) / len(self.reviews), 1)

    def facilities_list(self):
        try:
            return json.loads(self.facilities or '[]')
        except:
            return []


class RoomImage(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    room_id   = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    filename  = db.Column(db.String(255), nullable=False)
    is_primary= db.Column(db.Boolean, default=False)


class Review(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    room_id    = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stars      = db.Column(db.Integer, nullable=False)
    text       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Wishlist(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)


# ══════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


# ══════════════════════════════════════════
#  ROUTES — AUTH
# ══════════════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        phone    = request.form['phone'].strip()
        password = request.form['password']
        confirm  = request.form['confirm_password']

        if password != confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        user = User(
            name=name, email=email, phone=phone,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['user_name'] = user.name
        flash('Welcome to Room Bandhu!', 'success')
        return redirect(url_for('home'))

    return render_template('auth.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        user = User.query.filter(
            db.func.lower(User.email) == email
        ).first()

        if not user:
            flash('Account not found. Please register first.', 'error')
            return redirect(url_for('login'))

        if check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Incorrect password', 'error')
        return redirect(url_for('login'))

    return render_template('auth.html', mode='login')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))


# ══════════════════════════════════════════
#  ROUTES — MAIN
# ══════════════════════════════════════════

@app.route('/')
def home():
    room_type = request.args.get('type', 'All')
    max_price = request.args.get('max_price', 0, type=int)
    sort      = request.args.get('sort', 'default')
    query     = request.args.get('q', '').strip()

    rooms_q = Room.query.filter_by(is_available=True)

    if query:
        rooms_q = rooms_q.filter(
            db.or_(
                Room.title.ilike(f'%{query}%'),
                Room.location.ilike(f'%{query}%'),
                Room.area.ilike(f'%{query}%'),
                Room.description.ilike(f'%{query}%')
            )
        )
    if room_type != 'All':
        rooms_q = rooms_q.filter_by(room_type=room_type)
    if max_price:
        rooms_q = rooms_q.filter(Room.rent <= max_price)

    rooms = rooms_q.all()

    if sort == 'price-asc':
        rooms.sort(key=lambda r: r.rent)
    elif sort == 'price-desc':
        rooms.sort(key=lambda r: -r.rent)
    elif sort == 'rating':
        rooms.sort(key=lambda r: -r.avg_rating())
    else:
        rooms.sort(key=lambda r: -r.id)

    # Wishlist IDs for current user
    wish_ids = []
    if 'user_id' in session:
        wish_ids = [w.room_id for w in Wishlist.query.filter_by(user_id=session['user_id']).all()]

    user = current_user()
    return render_template('index.html',
        rooms=rooms, wish_ids=wish_ids, user=user,
        active_type=room_type, query=query,
        max_price=max_price, sort=sort
    )


@app.route('/room/<int:room_id>')
def room_detail(room_id):
    room     = Room.query.get_or_404(room_id)
    user     = current_user()
    wish_ids = []
    if user:
        wish_ids = [w.room_id for w in Wishlist.query.filter_by(user_id=user.id).all()]
    already_reviewed = False
    if user:
        already_reviewed = Review.query.filter_by(room_id=room_id, user_id=user.id).first() is not None
    return render_template('room_detail.html',
        room=room, user=user, wish_ids=wish_ids,
        already_reviewed=already_reviewed
    )


# ══════════════════════════════════════════
#  ROUTES — ADD / EDIT / DELETE ROOM
# ══════════════════════════════════════════

@app.route('/add_room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        title       = request.form['title'].strip()
        rent        = int(request.form['rent'])
        room_type   = request.form['room_type']
        location    = request.form['location'].strip()
        area        = request.form.get('area', '').strip()
        phone       = request.form['phone'].strip()
        description = request.form.get('description', '').strip()
        facilities  = request.form.getlist('facilities')
        latitude    = request.form.get('latitude', None)
        longitude   = request.form.get('longitude', None)

        # Validate min 4 images
        images = request.files.getlist('images')
        valid_images = [img for img in images if img and allowed_file(img.filename)]
        if len(valid_images) < 4:
            flash('Please upload at least 4 room images', 'error')
            return redirect(url_for('add_room'))

        room = Room(
            title=title, rent=rent, room_type=room_type,
            location=location, area=area, phone=phone,
            description=description,
            facilities=json.dumps(facilities),
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            user_id=session['user_id']
        )
        db.session.add(room)
        db.session.flush()  # get room.id

        for i, img in enumerate(valid_images):
            ext      = img.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            room_img = RoomImage(room_id=room.id, filename=filename, is_primary=(i == 0))
            db.session.add(room_img)

        db.session.commit()
        flash('Room listed successfully!', 'success')
        return redirect(url_for('home'))

    user = current_user()
    return render_template('add_room.html', user=user)


@app.route('/delete_room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.user_id != session['user_id']:
        flash('Not authorized', 'error')
        return redirect(url_for('home'))
    # Delete image files
    for img in room.images:
        path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted', 'success')
    return redirect(url_for('dashboard'))


@app.route('/toggle_availability/<int:room_id>', methods=['POST'])
@login_required
def toggle_availability(room_id):
    room = Room.query.get_or_404(room_id)
    if room.user_id != session['user_id']:
        return jsonify({'error': 'Not authorized'}), 403
    room.is_available = not room.is_available
    db.session.commit()
    return jsonify({'available': room.is_available})


# ══════════════════════════════════════════
#  ROUTES — WISHLIST
# ══════════════════════════════════════════

@app.route('/wishlist/toggle/<int:room_id>', methods=['POST'])
@login_required
def toggle_wishlist(room_id):
    existing = Wishlist.query.filter_by(
        user_id=session['user_id'], room_id=room_id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'saved': False, 'count': Wishlist.query.filter_by(user_id=session['user_id']).count()})
    else:
        w = Wishlist(user_id=session['user_id'], room_id=room_id)
        db.session.add(w)
        db.session.commit()
        return jsonify({'saved': True, 'count': Wishlist.query.filter_by(user_id=session['user_id']).count()})


@app.route('/wishlist')
@login_required
def wishlist():
    user  = current_user()
    items = Wishlist.query.filter_by(user_id=user.id).all()
    rooms = [w.room for w in items]
    return render_template('wishlist.html', rooms=rooms, user=user)


# ══════════════════════════════════════════
#  ROUTES — REVIEWS
# ══════════════════════════════════════════

@app.route('/review/<int:room_id>', methods=['POST'])
@login_required
def add_review(room_id):
    existing = Review.query.filter_by(room_id=room_id, user_id=session['user_id']).first()
    if existing:
        flash('You have already reviewed this room', 'error')
        return redirect(url_for('room_detail', room_id=room_id))

    stars = int(request.form['stars'])
    text  = request.form['text'].strip()
    if not text or stars < 1 or stars > 5:
        flash('Please provide valid review', 'error')
        return redirect(url_for('room_detail', room_id=room_id))

    review = Review(
        room_id=room_id, user_id=session['user_id'],
        stars=stars, text=text
    )
    db.session.add(review)
    db.session.commit()
    flash('Review submitted!', 'success')
    return redirect(url_for('room_detail', room_id=room_id))


# ══════════════════════════════════════════
#  ROUTES — DASHBOARD
# ══════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()

    # 🔥 IMPORTANT FIX
    if not user:
        return redirect(url_for('login'))

    my_rooms = Room.query.filter_by(user_id=user.id)\
        .order_by(Room.created_at.desc()).all()

    wish_count = Wishlist.query.filter_by(user_id=user.id).count()

    return render_template(
        'dashboard.html',
        user=user,
        my_rooms=my_rooms,
        wish_count=wish_count
    )
# ══════════════════════════════════════════
#  API — Nearby rooms via lat/lng
# ══════════════════════════════════════════

@app.route('/api/nearby')
def nearby_rooms():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if not lat or not lng:
        return jsonify({'error': 'lat/lng required'}), 400

    rooms = Room.query.filter(
        Room.latitude.isnot(None),
        Room.longitude.isnot(None),
        Room.is_available == True
    ).all()

    def distance(r):
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        dlat = radians(r.latitude - lat)
        dlon = radians(r.longitude - lng)
        a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(r.latitude))*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    nearby = sorted([(r, distance(r)) for r in rooms], key=lambda x: x[1])[:10]
    return jsonify([{
        'id': r.id, 'title': r.title, 'rent': r.rent,
        'location': r.location, 'type': r.room_type,
        'distance_km': round(d, 2),
        'rating': r.avg_rating(),
        'image': r.images[0].filename if r.images else None
    } for r, d in nearby])


# ══════════════════════════════════════════
#  INIT
# ══════════════════════════════════════════

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
