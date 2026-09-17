from flask import Blueprint, request, jsonify
from backend.database import get_db
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
import uuid

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/api/update-profile', methods=['POST'])
def update_profile():
    data = request.get_json()

    userid = data.get('userid', '').strip()
    username = data.get('username', '').strip()

    if userid == '' or username == '':
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT id
        FROM users
        WHERE userid = %s
        ''',
        (userid,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            'success': False,
            'message': 'Không tìm thấy người dùng'
        }), 404

    cursor.execute(
        '''
        SELECT id
        FROM users
        WHERE username = %s
        AND userid != %s
        ''',
        (username, userid)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        db.close()

        return jsonify({
            'success': False,
            'message': 'Tên người dùng đã tồn tại'
        }), 409

    cursor.execute(
        '''
        UPDATE users
        SET username = %s
        WHERE userid = %s
        ''',
        (username, userid)
    )

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        'success': True,
        'message': 'Cập nhật thông tin thành công',
        'username': username
    }), 200


@profile_bp.route('/api/update-avatar', methods=['POST'])
def update_avatar():
    userid = request.form.get('userid', '').strip()
    avatar = request.files.get('avatar')

    if userid == '' or not avatar:
        return jsonify({
            'success': False,
            'message': 'Vui lòng chọn ảnh'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT id
        FROM users
        WHERE userid = %s
        ''',
        (userid,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            'success': False,
            'message': 'Không tìm thấy người dùng'
        }), 404

    upload_folder = os.path.join(
        os.getcwd(),
        'uploads',
        'avatars'
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    filename = secure_filename(avatar.filename)
    extension = os.path.splitext(filename)[1]

    new_filename = f'{userid}_{uuid.uuid4().hex}{extension}'

    file_path = os.path.join(
        upload_folder,
        new_filename
    )

    avatar.save(file_path)

    avatar_url = f'/uploads/avatars/{new_filename}'

    cursor.execute(
        '''
        UPDATE users
        SET avatar = %s
        WHERE userid = %s
        ''',
        (avatar_url, userid)
    )

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        'success': True,
        'message': 'Cập nhật avatar thành công',
        'avatar': avatar_url
    }), 200

@profile_bp.route('/api/change-password', methods=['POST'])
def change_password():
    data = request.get_json() or {}

    userid = data.get('userid', '').strip()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if (
        userid == '' or
        current_password == '' or
        new_password == ''
    ):
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ'
        }), 400

    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'message': 'Mật khẩu phải có ít nhất 6 ký tự'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT id, password
        FROM users
        WHERE userid = %s
        ''',
        (userid,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            'success': False,
            'message': 'Không tìm thấy người dùng'
        }), 404

    if not check_password_hash(
        user['password'],
        current_password
    ):
        cursor.close()
        db.close()

        return jsonify({
            'success': False,
            'message': 'Mật khẩu hiện tại không đúng'
        }), 401

    password_hash = generate_password_hash(new_password)

    cursor.execute(
        '''
        UPDATE users
        SET password = %s
        WHERE userid = %s
        ''',
        (
            password_hash,
            userid
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        'success': True,
        'message': 'Đổi mật khẩu thành công'
    }), 200
    
@profile_bp.route('/api/search-user', methods=['GET'])
def search_user():
    keyword = request.args.get('keyword', '').strip()
    userid = request.args.get('userid', '').strip()
    if keyword == '':
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập tên hoặc ID'
        }), 400
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        '''
        SELECT userid, username, avatar
        FROM users
        WHERE (
            BINARY username LIKE BINARY %s
            OR BINARY userid LIKE BINARY %s
        )
        AND userid != %s
        ''',
        (
            f'%{keyword}%',
            f'%{keyword}%',
            userid
        )
    )
    users = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
        'success': True,
        'users': users
    }), 200