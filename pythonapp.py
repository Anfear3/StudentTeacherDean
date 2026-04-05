import jwt
import datetime
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'

# Імітація бази даних
users = {
    "ivan": {"password": "123", "role": "student", "id": 1},
    "petro": {"password": "456", "role": "teacher", "id": 2},
    "olga": {"password": "789", "role": "dean", "id": 3}
}

grades_db = {
    1: ["Math: A", "Physics: B"],
    2: ["Advanced Calculus", "Quantum Mechanics"]
}

# --- Декоратор для перевірки JWT ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'message': 'Token is missing!'}), 401
        
        # Очищаємо від Bearer та лапок
        token = auth_header.replace("Bearer ", "").strip().strip('"')
        
        try:
            # Декодуємо токен
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data
        except Exception as e:
            print(f"JWT Error: {e}") 
            return jsonify({'message': f'Token is invalid! Error: {e}'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated 
# --- Ендпоінти ---

@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401

    user = users.get(auth['username'])
    if user and user['password'] == auth['password']:
        # Генеруємо токен
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token})

    return jsonify({'message': 'Wrong credentials'}), 401

@app.route('/grades', methods=['GET'])
@token_required
def get_grades(current_user):
    role = current_user.get('role')
    user_id = current_user.get('user_id')

    if role == "student":
        return jsonify({"my_grades": grades_db.get(user_id, [])})
    
    if role == "teacher":
        return jsonify({"my_subjects": grades_db.get(user_id, [])})
    
    if role == "dean":
        return jsonify({"all_data": grades_db})

    return jsonify({"message": "Role undefined"}), 403

@app.route('/admin', methods=['GET'])
@token_required
def admin_panel(current_user):
    if current_user.get("role") != "dean":
        return jsonify({"message": "Access denied"}), 403
    
    return jsonify({"message": "Welcome to the Dean's Admin Panel!"})

if __name__ == '__main__':
    app.run(debug=True)