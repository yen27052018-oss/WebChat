from flask import Blueprint, request, jsonify
from backend.database import get_db

import os
import uuid

from werkzeug.utils import secure_filename

import cloudinary.uploader
# import cloudinary.utils
import backend.cloudinary_config

message_bp = Blueprint( 'message',__name__)


@message_bp.route('/api/messages', methods=['GET'])
def get_messages():

    conversation_id = request.args.get('conversation_id')
    user_id = request.args.get('user_id')

    if not conversation_id or not user_id:
        return jsonify({
            'success': False,
            'message': 'Thiếu thông tin cuộc trò chuyện'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # Kiểm tra người dùng có thuộc cuộc trò chuyện không
        cursor.execute(
            '''
            SELECT id
            FROM conversation_members
            WHERE conversation_id = %s
                AND user_id = %s
            LIMIT 1
            ''',
            (
                conversation_id,
                user_id
            )
        )

        member = cursor.fetchone()

        if not member:
            return jsonify({
                'success': False,
                'message': 'Bạn không thuộc cuộc trò chuyện này'
            }), 403

        # Lấy danh sách tin nhắn
        cursor.execute(
            '''
            SELECT
                m.id,
                m.conversation_id,
                m.sender_id,
                u.username AS sender_username,
                u.avatar AS sender_avatar,
                m.content,
                m.file_name,
                m.message_type,
                m.status,
                m.created_at,
                m.seen_at
            FROM messages m
            JOIN users u
                ON u.id = m.sender_id
            WHERE m.conversation_id = %s
            ORDER BY m.created_at ASC, m.id ASC
            ''',
            (conversation_id,)
        )

        messages = cursor.fetchall()

        # Chuyển datetime thành chuỗi
        for message in messages:

            if message['created_at']:
                message['created_at'] = \
                    message['created_at'].strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )

            if message['seen_at']:
                message['seen_at'] = \
                    message['seen_at'].strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )

        return jsonify({
            'success': True,
            'messages': messages
        }), 200

    except Exception as error:

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể lấy tin nhắn'
        }), 500

    finally:

        cursor.close()
        db.close()
        
@message_bp.route('/api/messages/seen', methods=['POST'])
def mark_messages_seen():

    data = request.get_json()

    conversation_id = data.get('conversation_id')
    user_id = data.get('user_id')

    if not conversation_id or not user_id:
        return jsonify({
            'success': False,
            'message': 'Thiếu thông tin'
        }), 400

    db = get_db()
    cursor = db.cursor()

    try:

        # Kiểm tra người dùng có thuộc cuộc trò chuyện không
        cursor.execute(
            '''
            SELECT id
            FROM conversation_members
            WHERE conversation_id = %s
                AND user_id = %s
            LIMIT 1
            ''',
            (
                conversation_id,
                user_id
            )
        )

        member = cursor.fetchone()

        if not member:
            return jsonify({
                'success': False,
                'message': 'Bạn không thuộc cuộc trò chuyện này'
            }), 403

        # Đánh dấu các tin nhắn của người khác là đã xem
        cursor.execute(
            '''
            UPDATE messages
            SET
                status = 'seen',
                seen_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
                AND sender_id != %s
                AND status != 'seen'
            ''',
            (
                conversation_id,
                user_id
            )
        )

        db.commit()

        return jsonify({
            'success': True
        }), 200

    except Exception as error:

        db.rollback()

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể cập nhật trạng thái đã xem'
        }), 500

    finally:

        cursor.close()
        db.close()
        

        
@message_bp.route('/api/messages', methods=['POST'])
def send_message():

    conversation_id = request.form.get('conversation_id')
    sender_id = request.form.get('sender_id')
    content = request.form.get('content', '').strip()
    
    image = request.files.get('image')
    file = request.files.get('file')
    voice = request.files.get('voice')
    
    file_name = None

    if file:
        file_name = file.filename

    if not conversation_id or not sender_id:
        return jsonify({
            'success': False,
            'message': 'thiếu thông tin'
        }), 400
    if content == '' and not image and not file and not voice:
        return jsonify({
            'success': False,
            'message': 'Vui lòng nhập tin nhắn'
        }), 400
    
    message_type = 'text'
    if file:
        try:

            original_name = file.filename

            safe_name = secure_filename(
                original_name
            )

            name, extension = os.path.splitext(
                safe_name
            )

            unique_name = (
                f'{name}_{uuid.uuid4().hex[:8]}'
                f'{extension}'
            )

            result = cloudinary.uploader.upload(
                file,
                folder='chat-watch-files',
                resource_type='raw',
                public_id=unique_name
            )

            content = result['secure_url']
            download_url = cloudinary.utils.cloudinary_url(
                unique_name,
                resource_type='raw',
                type='upload',
                secure=True,
                flags=f'attachment:{file_name}'
            )[0]
            message_type = 'file'

        except Exception as error:

            print(error)

            return jsonify({
                'success': False,
                'message': 'Upload file thất bại'
            }), 500

    if voice:
        try:

            result = cloudinary.uploader.upload(
                voice,
                folder='chat-watch/voices',
                resource_type='raw'
            )

            content = result['secure_url']
            message_type = 'voice'

        except Exception as error:

            print(error)

            return jsonify({
                'success': False,
                'message': 'Upload voice thất bại'
            }), 500
    
    if image:
        try:
            result = cloudinary.uploader.upload(
                image,
                folder='chat-watch/images',
                transformation=[
                    {
                        'width': 1280,
                        'height': 1280,
                        'crop': 'limit',
                        'quality': 'auto'
                    }
                ]
            )

            content = result['secure_url']
            message_type = 'image'

        except Exception as error:
            print(error)

            return jsonify({
                'success': False,
                'message': 'Upload ảnh thất bại'
            }), 500

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # Kiểm tra người gửi có thuộc cuộc trò chuyện không
        cursor.execute(
            '''
            SELECT id
            FROM conversation_members
            WHERE conversation_id = %s
                AND user_id = %s
            LIMIT 1
            ''',
            (
                conversation_id,
                sender_id
            )
        )

        member = cursor.fetchone()

        if not member:
            return jsonify({
                'success': False,
                'message': 'Bạn không thuộc cuộc trò chuyện này'
            }), 403

        # Thêm tin nhắn
        cursor.execute(
            '''
            INSERT INTO messages (
                conversation_id,
                sender_id,
                content,
                file_name,
                message_type,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                'sent'
            )
            ''',
            (
                conversation_id,
                sender_id,
                content,
                file_name,
                message_type
            )
        )

        message_id = cursor.lastrowid

        # Cập nhật thời gian cuộc trò chuyện
        cursor.execute(
            '''
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''',
            (conversation_id,)
        )

        db.commit()

        # Lấy lại tin nhắn vừa gửi
        cursor.execute(
            '''
            SELECT
                id,
                conversation_id,
                sender_id,
                content,
                file_name,
                message_type,
                status,
                created_at,
                seen_at
            FROM messages
            WHERE id = %s
            ''',
            (message_id,)
        )

        message = cursor.fetchone()

        if message['created_at']:
            message['created_at'] = \
                message['created_at'].strftime(
                    '%Y-%m-%d %H:%M:%S'
                )

        if message['seen_at']:
            message['seen_at'] = \
                message['seen_at'].strftime(
                    '%Y-%m-%d %H:%M:%S'
                )

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as error:

        db.rollback()

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể gửi tin nhắn'
        }), 500

    finally:

        cursor.close()
        db.close()