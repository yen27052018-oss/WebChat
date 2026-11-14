from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash

from backend.database import get_db
from backend.username_utils import normalize_username, find_user_by_username

login_bp = Blueprint('login', __name__)


@login_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}

    username = normalize_username(data.get('username', ''))
    password = data.get('password', '').strip()

    if username == '' or password == '':
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Phải đúng cả chữ cái lẫn dấu: 'yên' không vào được tài khoản 'yen'
        user = find_user_by_username(cursor, username)

    finally:
        cursor.close()
        db.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({
            'success': False,
            'message': 'Tên người dùng hoặc mật khẩu không tồn tại'
        }), 401

    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'userid': user['userid'],
            'username': user['username'],
            'avatar': user['avatar']
        }
    }), 200