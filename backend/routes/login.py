from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from backend.database import get_db

login_bp = Blueprint('login', __name__)

@login_bp.route('/api/login', methods=['POST'])
def login():
    print('--- BAT DAU LOGIN ---')

    data = request.get_json()
    print('DATA:', data)

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    print('USERNAME:', username)

    if username == '' or password == '':
        print('THIEU THONG TIN')

        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ'
        }), 400

    print('DANG KET NOI DATABASE')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    print('DANG TRUY VAN USER')

    cursor.execute(
        '''
        SELECT id, userid, username, password, avatar
        FROM users
        WHERE username = %s
        ''',
        (username,)
    )

    user = cursor.fetchone()

    print('USER:', user)

    cursor.close()
    db.close()

    if not user:
        print('KHONG TIM THAY USER')

        return jsonify({
            'success': False,
            'message': 'Tên người dùng hoặc mật khẩu không tồn tại'
        }), 401

    print('DANG KIEM TRA PASSWORD')

    if not check_password_hash(user['password'], password):
        print('SAI PASSWORD')

        return jsonify({
            'success': False,
            'message': 'Tên người dùng hoặc mật khẩu không tồn tại'
        }), 401

    print('DANG NHAP THANH CONG')

    return jsonify({
        'success': True,
        # 'message': 'Đăng nhập thành công',
        'user': {
            'id': user['id'],
            'userid': user['userid'],
            'username': user['username'],
            'avatar': user['avatar']
        }
    }), 200