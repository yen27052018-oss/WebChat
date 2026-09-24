from flask import Blueprint, request, jsonify
from backend.database import get_db
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from backend.extensions import socketio
import os
import uuid
from pathlib import Path

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

    cursor.execute(
        '''
        SELECT DISTINCT cm2.user_id
        FROM conversation_members cm1
        JOIN conversation_members cm2
            ON cm1.conversation_id = cm2.conversation_id
        WHERE cm1.user_id = %s
        AND cm2.user_id != %s
        ''',
        (
            user['id'],
            user['id']
        )
    )
    
    conversation_users = cursor.fetchall()
    for conversation_user in conversation_users:
        socketio.emit(
            'profile_updated',
            {
                'user_id': user['id'],
                'username': username
            },
            to=f"user_{conversation_user['user_id']}"
        )
    
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
    
    project_folder = Path(__file__).resolve().parents[2]

    upload_folder = os.path.join(
        project_folder.parent
        / 'WEB_Chat_Uploads'
        / 'avatars'
    )
    print('UPLOAD FOLDER:', upload_folder)
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
    
    cursor.execute(
        '''
        SELECT DISTINCT cm2.user_id
        FROM conversation_members cm1
        JOIN conversation_members cm2
            ON cm1.conversation_id = cm2.conversation_id
        WHERE cm1.user_id = %s
        AND cm2.user_id != %s
        ''',
        (
            user['id'],
            user['id']
        )
    )
    conversation_users = cursor.fetchall()
    for conversation_user in conversation_users:
        socketio.emit(
            'profile_updated',
            {
                'user_id': user['id'],
                'avatar': avatar_url
            },
            to=f"user_{conversation_user['user_id']}"
        )
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

    try:
        # Lấy ID thật của người đang tìm kiếm
        cursor.execute(
            '''
            SELECT id
            FROM users
            WHERE userid = %s
            ''',
            (userid,)
        )

        current_user = cursor.fetchone()

        if not current_user:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy người dùng hiện tại'
            }), 404

        current_user_id = current_user['id']

        # Tìm người dùng
        cursor.execute(
            '''
            SELECT
                u.id,
                u.userid,
                u.username,
                u.avatar,

                fr.status AS friend_status,
                fr.sender_id,
                fr.receiver_id

            FROM users u

            LEFT JOIN friend_requests fr
                ON (
                    (
                        fr.sender_id = %s
                        AND fr.receiver_id = u.id
                    )
                    OR
                    (
                        fr.sender_id = u.id
                        AND fr.receiver_id = %s
                    )
                )

            WHERE (
                BINARY u.username LIKE BINARY %s
                OR BINARY u.userid LIKE BINARY %s
            )
            AND u.id != %s

            ORDER BY u.username
            ''',
            (
                current_user_id,
                current_user_id,
                f'%{keyword}%',
                f'%{keyword}%',
                current_user_id
            )
        )

        users = cursor.fetchall()

        for user in users:

            if user['friend_status'] == 'accepted':

                user['friend_status'] = 'accepted'

            elif user['friend_status'] == 'pending':

                if user['sender_id'] == current_user_id:
                    user['friend_status'] = 'sent'
                else:
                    user['friend_status'] = 'received'

            else:

                user['friend_status'] = 'none'

            user.pop('id', None)
            user.pop('sender_id', None)
            user.pop('receiver_id', None)

        return jsonify({
            'success': True,
            'users': users
        }), 200

    except Exception as error:

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể tìm kiếm người dùng'
        }), 500

    finally:

        cursor.close()
        db.close()