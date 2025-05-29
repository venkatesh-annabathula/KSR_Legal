# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(100), nullable=False)
    ca_filed_date = db.Column(db.Date, nullable=False)
    ca_number = db.Column(db.String(100), nullable=False)
    required_details = db.Column(db.Text, nullable=False)
    filed_for = db.Column(db.String(100), nullable=False)
    cf_date = db.Column(db.Date, nullable=False)
    cf_amount_cf = db.Column(db.Float, nullable=False)
    cf_amount_njs = db.Column(db.Float, nullable=False)
    cf_paid_date = db.Column(db.Date, nullable=True)
    ca_ready_date = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_admin:
            flash('Admin access required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
@admin_required
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        task = Task(
            case_number=request.form['case_number'],
            ca_filed_date=datetime.strptime(request.form['ca_filed_date'], '%Y-%m-%d'),
            ca_number=request.form['ca_number'],
            required_details=request.form['required_details'],
            filed_for=request.form['filed_for'],
            cf_date=datetime.strptime(request.form['cf_date'], '%Y-%m-%d'),
            cf_amount_cf=float(request.form['cf_amount_cf']),
            cf_amount_njs=float(request.form['cf_amount_njs']),
            cf_paid_date=datetime.strptime(request.form['cf_paid_date'], '%Y-%m-%d') if request.form['cf_paid_date'] else None,
            ca_ready_date=datetime.strptime(request.form['ca_ready_date'], '%Y-%m-%d') if request.form['ca_ready_date'] else None,
            remarks=request.form['remarks']
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('form.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.case_number = request.form['case_number']
        task.ca_filed_date = datetime.strptime(request.form['ca_filed_date'], '%Y-%m-%d')
        task.ca_number = request.form['ca_number']
        task.required_details = request.form['required_details']
        task.filed_for = request.form['filed_for']
        task.cf_date = datetime.strptime(request.form['cf_date'], '%Y-%m-%d')
        task.cf_amount_cf = float(request.form['cf_amount_cf'])
        task.cf_amount_njs = float(request.form['cf_amount_njs'])
        task.cf_paid_date = datetime.strptime(request.form['cf_paid_date'], '%Y-%m-%d') if request.form['cf_paid_date'] else None
        task.ca_ready_date = datetime.strptime(request.form['ca_ready_date'], '%Y-%m-%d') if request.form['ca_ready_date'] else None
        task.remarks = request.form['remarks']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('form.html', task=task)

@app.route('/delete/<int:id>')
@login_required
@admin_required
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash('Username and password cannot be empty.')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('register.html')
        is_admin = request.form.get('is_admin') == 'on'
        user = User(username=username, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
