from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
import os
from werkzeug.utils import secure_filename
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config.from_pyfile('config.py')
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'lostfound.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'Users'
    username = db.Column(db.String(150), primary_key=True)
    name_first = db.Column(db.String(150))
    name_last = db.Column(db.String(150))
    password = db.Column(db.String(255))
    mis = db.Column(db.String(255))
    role = db.Column(db.String(50), default='user')

class Item(db.Model):
    __tablename__ = 'Items'
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(255))
    report_type = db.Column(db.String(255))
    place_of_responsibility = db.Column(db.String(255))
    username = db.Column(db.String(150), db.ForeignKey('Users.username'))
    image = db.Column(db.String(255))

class ItemLocation(db.Model):
    __tablename__ = 'items_locations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('Items.item_id'))
    location = db.Column(db.String(255))

class Comment(db.Model):
    __tablename__ = 'Comments'
    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment = db.Column(db.Text)
    item_id = db.Column(db.Integer, db.ForeignKey('Items.item_id'))
    username = db.Column(db.String(150), db.ForeignKey('Users.username'))

class Conversation(db.Model):
    __tablename__ = 'Conversations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.Text)
    sender_id = db.Column(db.String(150), db.ForeignKey('Users.username'))
    receiver_id = db.Column(db.String(150), db.ForeignKey('Users.username'))
    time_stamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        mis = request.form['mis']
        role = 'user'

        user = User(
            username=username,
            name_first=first_name,
            name_last=last_name,
            password=password,
            mis=mis,
            role=role
        )
        try:
            db.session.add(user)
            db.session.commit()
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect('/signup')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['loggedin'] = True
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        description = request.form['description']
        category = request.form['category']
        report_type = request.form['report_type']
        responsibility = request.form['responsibility']
        locations = request.form.getlist('location')
        username = session['username']

        file = request.files.get('image')
        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            image_path = "uploads/" + filename

        item = Item(
            description=description,
            category=category,
            report_type=report_type,
            place_of_responsibility=responsibility,
            username=username,
            image=image_path
        )
        db.session.add(item)
        db.session.commit()

        item_id = item.item_id

        for loc in locations:
            il = ItemLocation(item_id=item_id, location=loc)
            db.session.add(il)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('add_item.html')

@app.route('/items')
def items():
    items = Item.query.all()
    return render_template('items.html', items=items)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get(item_id)
    comments = Comment.query.filter_by(item_id=item_id).all()
    return render_template('item_detail.html', item=item, comments=comments)

@app.route('/item/<int:item_id>/comment', methods=['POST'])
def add_comment(item_id):
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    comment_text = request.form['comment']
    username = session['username']
    comment = Comment(comment=comment_text, item_id=item_id, username=username)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/item/<int:item_id>/claim', methods=['POST'])
def claim(item_id):
    if request.method == 'POST' and request.path.endswith('/claim'):
        item = Item.query.get(item_id)
        if item:
            report_owner = item.username
            claimer = session.get('username')
            initial_message = f"Submitted claim request for item_id {item_id}"
            conv = Conversation(message=initial_message, sender_id=claimer, receiver_id=report_owner)
            db.session.add(conv)
            db.session.commit()
            flash('Claim request has been submitted successfully! Please visit the mentioned nodal center for verification. A conversation has been started with the report owner.', 'success')
    return redirect(url_for('items'))

@app.route('/conversations')
def conversations():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    current_user = session['username']
    sql = text("""
        SELECT 
            IF(sender_id = :user, receiver_id, sender_id) AS other_user,
            MAX(time_stamp) AS time_stamp,
            SUBSTRING_INDEX(GROUP_CONCAT(message ORDER BY time_stamp DESC), ',', 1) AS latest_message
        FROM Conversations
        WHERE sender_id = :user OR receiver_id = :user
        GROUP BY other_user
        ORDER BY time_stamp DESC
    """)
    result = db.session.execute(sql, {'user': current_user})
    conversations = [dict(row) for row in result.mappings().all()]
    return render_template('conversations.html', conversations=conversations)

@app.route('/conversation/<string:user_id>', methods=['GET', 'POST'])
def conversation_detail(user_id):
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    current_user = session['username']

    if request.method == 'POST':
        message = request.form['message']
        conv = Conversation(message=message, sender_id=current_user, receiver_id=user_id)
        db.session.add(conv)
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('conversation_detail', user_id=user_id))

    messages = Conversation.query.filter(
        ((Conversation.sender_id == current_user) & (Conversation.receiver_id == user_id)) |
        ((Conversation.sender_id == user_id) & (Conversation.receiver_id == current_user))
    ).order_by(Conversation.time_stamp.asc()).all()

    return render_template('conversation_detail.html', messages=messages, other_user=user_id, current_user=current_user)

@app.route('/admin/claims')
def admin_claims():
    if session.get('role') == 'admin':
        items = Item.query.filter_by(place_of_responsibility=session['username']).all()
        return render_template('admin_claims.html', items=items)
    return 'Unauthorized'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
