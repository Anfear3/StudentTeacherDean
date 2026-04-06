import psycopg2
from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'

# --- 1. ПІДКЛЮЧЕННЯ ДО БАЗИ ---
def get_db_connection(user_role):
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="university_db", 
            user="postgres",         
            password="Mas_mak122", 
            port="5432"
        )
        cur = conn.cursor()
        # ПЕРЕМИКАЄМО РОЛЬ В БАЗІ
        cur.execute(f"SET ROLE {user_role}_role")
        return conn, cur
    except Exception as e:
        print(f"Помилка бази: {e}")
        return None, None

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401

    
    users = {
        'ivan': {'password': '123', 'role': 'student'},
        'petro': {'password': '456', 'role': 'teacher'},
        'dean_boss': {'password': '789', 'role': 'dean'}
    }

    user = users.get(auth.username)
    if user and user['password'] == auth.password:
        token = jwt.encode({
            'user': auth.username,
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials'}), 401

# --- 3. ДЕКОРАТОР ПЕРЕВІРКИ ТОКЕНА ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_name = data['user']
            current_user_role = data['role']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user_name, current_user_role, *args, **kwargs)
    return decorated

# --- 4. НОВИЙ ЕНДПОЇНТ З РОЛЯМИ БАЗИ ---
@app.route('/grades', methods=['GET'])
@token_required
def get_grades(current_user_name, current_user_role):
    # Підключаємось до бази з роллю з токена
    conn, cur = get_db_connection(current_user_role)
    if not conn:
        return jsonify({'message': 'DB connection failed'}), 500
    
    try:
        # Для студента встановлюємо current_user в базі, щоб RLS спрацював
        if current_user_role == 'student':
            cur.execute(f"SET SESSION \"user.name\" = '{current_user_name}';")
         
        cur.execute("SELECT * FROM grades")
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0], 'student': row[1], 'subject': row[2], 'grade': row[3]
            })
        
        cur.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({'message': 'Access denied', 'error': str(e)}), 403

if __name__ == '__main__':
    app.run(debug=True)