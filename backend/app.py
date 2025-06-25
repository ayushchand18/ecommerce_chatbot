from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import timedelta
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import random

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(255), nullable=True)

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    messages = db.relationship('ChatMessage', backref='session', lazy=True)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_bot = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    user = User(username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'access_token': access_token,
        'user_id': user.id,
        'username': user.username
    }), 200

@app.route('/api/products', methods=['GET'])
def get_products():
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    
    products = Product.query
    
    if query:
        products = products.filter(Product.name.ilike(f'%{query}%') | Product.description.ilike(f'%{query}%'))
    
    if category:
        products = products.filter_by(category=category)
    
    if min_price:
        try:
            products = products.filter(Product.price >= float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products = products.filter(Product.price <= float(max_price))
        except ValueError:
            pass
    
    products = products.all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'category': p.category,
        'stock': p.stock,
        'image_url': p.image_url
    } for p in products]), 200

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = db.session.query(Product.category.distinct()).all()
    return jsonify([c[0] for c in categories]), 200

@app.route('/api/chat/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    user_id = get_jwt_identity()
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
    return jsonify([{
        'id': s.id,
        'created_at': s.created_at.isoformat(),
        'updated_at': s.updated_at.isoformat()
    } for s in sessions]), 200

@app.route('/api/chat/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    user_id = get_jwt_identity()
    session = ChatSession(user_id=user_id)
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'id': session.id,
        'created_at': session.created_at.isoformat()
    }), 201

@app.route('/api/chat/sessions/<int:session_id>/messages', methods=['GET'])
@jwt_required()
def get_chat_messages(session_id):
    user_id = get_jwt_identity()
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'message': 'Session not found'}), 404
    
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify([{
        'id': m.id,
        'content': m.content,
        'is_bot': m.is_bot,
        'timestamp': m.timestamp.isoformat()
    } for m in messages]), 200

@app.route('/api/chat/sessions/<int:session_id>/messages', methods=['POST'])
@jwt_required()
def add_chat_message(session_id):
    user_id = get_jwt_identity()
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'message': 'Session not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'message': 'Message content required'}), 400
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        content=data['content'],
        is_bot=False
    )
    db.session.add(user_message)
    
    # Generate bot response
    bot_response = generate_bot_response(data['content'])
    bot_message = ChatMessage(
        session_id=session_id,
        content=bot_response,
        is_bot=True
    )
    db.session.add(bot_message)
    
    db.session.commit()
    
    return jsonify({
        'user_message': {
            'id': user_message.id,
            'content': user_message.content,
            'is_bot': user_message.is_bot,
            'timestamp': user_message.timestamp.isoformat()
        },
        'bot_message': {
            'id': bot_message.id,
            'content': bot_message.content,
            'is_bot': bot_message.is_bot,
            'timestamp': bot_message.timestamp.isoformat()
        }
    }), 201

def generate_bot_response(user_input):
    # This is a simplified version - in a real app, you'd use NLP here
    user_input = user_input.lower()
    
    if any(word in user_input for word in ['hello', 'hi', 'hey']):
        return "Hello! How can I help you with your shopping today?"
    
    elif any(word in user_input for word in ['product', 'item', 'buy']):
        return "I can help you find products. What are you looking for? You can say things like 'I want to buy a laptop' or 'Show me books under $20'."
    
    elif any(word in user_input for word in ['price', 'cost', 'how much']):
        return "I can show you products in different price ranges. What's your budget?"
    
    elif any(word in user_input for word in ['category', 'type', 'kind']):
        return "We have products in several categories. Would you like to see electronics, books, or clothing?"
    
    elif any(word in user_input for word in ['thank', 'thanks', 'appreciate']):
        return "You're welcome! Is there anything else I can help you with?"
    
    elif any(word in user_input for word in ['bye', 'goodbye', 'exit']):
        return "Goodbye! Come back soon for more shopping!"
    
    else:
        return "I'm here to help you shop. You can ask me about products, prices, or categories. What would you like to know?"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
