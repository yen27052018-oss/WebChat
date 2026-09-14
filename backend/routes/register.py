from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from backend.database import get_db

register_bp = Blueprint('register', __name__)

@register_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if username == '' or password == '':
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ'
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': 'Mật khẩu phải có ít nhất 6 ký tự'
        }), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'SELECT id FROM users WHERE username = %s',
        (username,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        db.close()

        return jsonify({
            'success': False,
            'message': 'Tên người dùng đã tồn tại'
        }), 409

    cursor.execute('SELECT MAX(id) FROM users')

    result = cursor.fetchone()

    next_id = (result[0] or 0) + 1

    user_code = f'CW{next_id:04d}'

    password_hash = generate_password_hash(password)

    cursor.execute(
        '''
        INSERT INTO users (
            userid,
            username,
            password
        )
        VALUES (%s, %s, %s)
        ''',
        (
            user_code,
            username,
            password_hash
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        'success': True,
        'message': 'Đăng ký thành công',
        'user_code': user_code
    }), 201