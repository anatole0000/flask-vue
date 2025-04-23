from flask import Flask, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_cors import CORS
from flask_migrate import Migrate

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'  # To store sessions in the filesystem
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

db = SQLAlchemy(app)
Session(app)
CORS(app, supports_credentials=True)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='user')
    secret_answer = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes

# Register user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    # Check if user exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400
    
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"})

# Login user
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    session['user_id'] = user.id  # Store user_id in session
    return jsonify({"message": "Login successful"})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    return jsonify({"message": "Logged out successfully"}), 200

# Check if user is logged in
@app.route('/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    return jsonify({"username": user.username, "role": user.role})  # Return the user's role


# Create a new contact
@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.get_json()
    name = data['name']
    phone = data['phone']
    email = data['email']
    category = data['category']
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    new_contact = Contact(name=name, phone=phone, email=email, category=category, user_id=user_id)
    db.session.add(new_contact)
    db.session.commit()
    return jsonify({"message": "Contact added successfully!"})

# Get all contacts for the logged-in user
@app.route('/contacts', methods=['GET'])
def get_contacts():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    contacts = Contact.query.filter_by(user_id=user_id).all()
    contacts_list = [{"id": c.id, "name": c.name, "phone": c.phone, "email": c.email, "category": c.category} for c in contacts]
    return jsonify(contacts_list)

# Edit a contact
@app.route('/contacts/<int:id>', methods=['PUT'])
def edit_contact(id):
    data = request.get_json()
    contact = Contact.query.get(id)

    if contact:
        contact.name = data['name']
        contact.phone = data['phone']
        contact.email = data['email']
        contact.category = data['category']
        db.session.commit()
        return jsonify({"message": "Contact updated successfully!"})
    
    return jsonify({"error": "Contact not found"}), 404

# Delete a contact
@app.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    contact = Contact.query.get(id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({"message": "Contact deleted successfully!"})
    
    return jsonify({"error": "Contact not found"}), 404

# Reset password route (for simplicity, using a secret question approach)
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    username = data['username']
    secret_answer = data['secret_answer']
    new_password = data['new_password']

    # Find the user
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if the secret answer matches
    if user.secret_answer != secret_answer:  # Add secret_answer field to your model
        return jsonify({"error": "Invalid secret answer"}), 400

    # Update the password
    user.password = new_password
    db.session.commit()

    return jsonify({"message": "Password reset successfully!"}), 200


# Example route with role-based access control
@app.route('/admin/contacts', methods=['GET'])
def get_admin_contacts():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if user.role != 'admin':
        return jsonify({"error": "Access forbidden"}), 403  # Only admins can access this route

    contacts = Contact.query.all()  # Get all contacts
    contacts_list = [{"id": c.id, "name": c.name, "phone": c.phone, "email": c.email, "category": c.category} for c in contacts]
    return jsonify(contacts_list)


if __name__ == '__main__':
    app.run(debug=True)
