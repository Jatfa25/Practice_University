import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'domiapp-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/domi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== MODELOS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # client, driver, admin
    balance = db.Column(db.Float, default=0.0)
    is_online = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=5.0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    pickup_address = db.Column(db.String(255))
    delivery_address = db.Column(db.String(255))
    price = db.Column(db.Float)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, in_transit, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== RUTAS ====================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('dashboard'))
        flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'client':
        return render_template('client_dashboard.html', user=current_user)
    elif current_user.role == 'driver':
        return render_template('driver_dashboard.html', user=current_user)
    else:
        return render_template('admin_dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/request_order', methods=['POST'])
@login_required
def request_order():
    if current_user.role != 'client':
        return jsonify({"error": "Solo clientes"}), 403
    data = request.get_json()
    price = random.randint(15000, 40000)
    order = Order(
        client_id=current_user.id,
        pickup_address=data.get('pickup'),
        delivery_address=data.get('delivery'),
        price=price,
        status='pending'
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({"success": True, "order_id": order.id, "price": price})

if __name__ == '__main__':
    os.makedirs('instance', exist_ok=True)
    with app.app_context():
        db.create_all()
        if not User.query.first():
            users = [
                User(nombre="Cliente Demo", email="cliente@demo.com", password="123456", role="client"),
                User(nombre="Domiciliario Demo", email="domi@demo.com", password="123456", role="driver", balance=50000),
                User(nombre="Admin", email="admin@demo.com", password="admin123", role="admin")
            ]
            db.session.add_all(users)
            db.session.commit()
    print("🚀 DomiApp corriendo en http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)