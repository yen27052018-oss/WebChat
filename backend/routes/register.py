from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from backend.database import get_db
from backend.username_utils import normalize_username, find_user_by_username

register_bp = Blueprint('register', __name__)


@register_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    username = normalize_username(data.get('username', ''))
    password = data.get('password', '').strip()

    if username == '' or password == '':
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ'
        }), 400

    if len(username) > 100:
        return jsonify({
            'success': False,
            'message': 'Tên người dùng tối đa 100 ký tự'
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': 'Mật khẩu phải có ít nhất 6 ký tự'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Chỉ trùng khi giống hệt từng chữ cái và dấu
        if find_user_by_username(cursor, username):
            return jsonify({
                'success': False,
                'message': 'Tên người dùng đã tồn tại'
            }), 409

        cursor.execute('SELECT MAX(id) AS max_id FROM users')
        next_id = (cursor.fetchone()['max_id'] or 0) + 1

        user_code = f'CW{next_id:04d}'

        cursor.execute(
            '''
            INSERT INTO users (userid, username, password)
            VALUES (%s, %s, %s)
            ''',
            (user_code, username, generate_password_hash(password))
        )

        db.commit()

        return jsonify({
            'success': True,
            'message': 'Đăng ký thành công',
            'user_code': user_code
        }), 201

    finally:
        cursor.close()
        db.close();