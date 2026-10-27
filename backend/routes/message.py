from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.extensions import socketio
from backend.socket.chatSocket import online_users
from backend.message_helper import MESSAGE_SELECT, format_message, get_message_by_id
from backend.ai_service import maybe_reply_ai, reset_ai_conversation, is_ai_conversation

import os
import uuid

from werkzeug.utils import secure_filename

import cloudinary.uploader
import cloudinary.utils
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
            MESSAGE_SELECT + '''
            WHERE m.conversation_id = %s
                AND NOT EXISTS (
                    SELECT 1 FROM message_deletions d
                    WHERE d.message_id = m.id AND d.user_id = %s
                )
            ORDER BY m.created_at ASC, m.id ASC
            ''',
            (conversation_id, user_id)
        )

        messages = cursor.fetchall()

        # Chuyển datetime thành chuỗi
        for message in messages:
            format_message(message)

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
    caption = request.form.get('caption', '').strip()
    
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

            # download_url = cloudinary.utils.cloudinary_url(
            #     f'chat-watch-files/{unique_name}',
            #     resource_type='raw',
            #     type='upload',
            #     secure=True,
            #     flags=f'attachment:{file_name}'
            # )[0]
            
            

            content = result['secure_url']
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
            
        # Lấy người nhận
        cursor.execute(
            '''
            SELECT user_id
            FROM conversation_members
            WHERE conversation_id = %s
                AND user_id != %s
            LIMIT 1
            ''',
            (
                conversation_id,
                sender_id
            )
        )

        receiver = cursor.fetchone()

        if not receiver:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy người nhận'
            }), 400

        receiver_id = receiver['user_id']

        # Xác định trạng thái tin nhắn
        status = (
            'delivered'
            if str(receiver_id) in online_users
            else 'sent'
        )

        # Thêm tin nhắn
        cursor.execute(
            '''
            INSERT INTO messages (
                conversation_id,
                sender_id,
                content,
                file_name,
                caption,
                message_type,
                status
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ''',
            (
                conversation_id,
                sender_id,
                content,
                file_name,
                (caption or None) if image else None,
                message_type,
                status
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
        
        # Nếu ai đó đã xóa hội thoại thì cho hiện lại
        cursor.execute(
            'UPDATE conversation_members SET is_deleted = 0 WHERE conversation_id = %s',
            (conversation_id,)
        )

        db.commit()

        message = get_message_by_id(cursor, message_id)

        # Lấy người nhận
        cursor.execute(
            '''
            SELECT user_id
            FROM conversation_members
            WHERE conversation_id = %s
                AND user_id != %s
            LIMIT 1
            ''',
            (
                conversation_id,
                sender_id
            )
        )

        receiver = cursor.fetchone()

        if receiver:

            receiver_id = receiver['user_id']

            # Gửi tin nhắn realtime cho người nhận
            socketio.emit(
                'new_message',
                message,
                room=f'user_{receiver_id}'
            )
            
            # Người nhận là AI thì AI trả lời
            maybe_reply_ai(conversation_id, sender_id, receiver_id, message['id'])
        
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
        
# =========================
# THU HỒI TIN NHẮN
# =========================
@message_bp.route('/api/messages/recall', methods=['POST'])
def recall_message():

    data = request.get_json()
    message_id = data.get('message_id')
    user_id = data.get('user_id')

    if not message_id or not user_id:
        return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Chỉ được thu hồi tin nhắn của chính mình
        cursor.execute(
            'SELECT conversation_id FROM messages WHERE id = %s AND sender_id = %s',
            (message_id, user_id)
        )
        message = cursor.fetchone()

        if not message:
            return jsonify({
                'success': False,
                'message': 'Bạn chỉ có thể thu hồi tin nhắn của mình'
            }), 403

        conversation_id = message['conversation_id']

        cursor.execute(
            '''
            UPDATE messages
            SET is_recalled = 1, content = '', file_name = NULL
            WHERE id = %s
            ''',
            (message_id,)
        )
        db.commit()

        # Báo cho cả 2 người trong cuộc trò chuyện
        cursor.execute(
            'SELECT user_id FROM conversation_members WHERE conversation_id = %s',
            (conversation_id,)
        )
        for member in cursor.fetchall():
            socketio.emit(
                'message_recalled',
                {
                    'message_id': int(message_id),
                    'conversation_id': conversation_id
                },
                room=f"user_{member['user_id']}"
            )

        return jsonify({'success': True}), 200

    except Exception as error:
        db.rollback()
        print(error)
        return jsonify({'success': False, 'message': 'Không thể thu hồi tin nhắn'}), 500

    finally:
        cursor.close()
        db.close()


# =========================
# XÓA TIN NHẮN PHÍA TÔI
# =========================
@message_bp.route('/api/messages/delete', methods=['POST'])
def delete_message_for_me():

    data = request.get_json()
    message_id = data.get('message_id')
    user_id = data.get('user_id')

    if not message_id or not user_id:
        return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Tin nhắn phải thuộc cuộc trò chuyện của người dùng
        cursor.execute(
            '''
            SELECT m.id
            FROM messages m
            JOIN conversation_members cm
                ON cm.conversation_id = m.conversation_id
            WHERE m.id = %s AND cm.user_id = %s
            ''',
            (message_id, user_id)
        )

        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Không có quyền'}), 403

        cursor.execute(
            'INSERT IGNORE INTO message_deletions (message_id, user_id) VALUES (%s, %s)',
            (message_id, user_id)
        )
        db.commit()

        return jsonify({'success': True}), 200

    except Exception as error:
        db.rollback()
        print(error)
        return jsonify({'success': False, 'message': 'Không thể xóa tin nhắn'}), 500

    finally:
        cursor.close()
        db.close()


# =========================
# XÓA HỘI THOẠI (CHỈ PHÍA TÔI)
# =========================
@message_bp.route('/api/conversations/delete', methods=['POST'])
def delete_conversation():

    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_id = data.get('user_id')

    if not conversation_id or not user_id:
        return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            '''
            SELECT id FROM conversation_members
            WHERE conversation_id = %s AND user_id = %s
            ''',
            (conversation_id, user_id)
        )

        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Không có quyền'}), 403

        if is_ai_conversation(cursor, conversation_id):
            return jsonify({
                'success': False,
                'message': 'Không thể xóa cuộc trò chuyện với AI'
            }), 403
        
        # Ẩn toàn bộ tin nhắn hiện có với người dùng này
        cursor.execute(
            '''
            INSERT IGNORE INTO message_deletions (message_id, user_id)
            SELECT id, %s FROM messages WHERE conversation_id = %s
            ''',
            (user_id, conversation_id)
        )

        # Ẩn hội thoại
        cursor.execute(
            '''
            UPDATE conversation_members
            SET is_deleted = 1
            WHERE conversation_id = %s AND user_id = %s
            ''',
            (conversation_id, user_id)
        )

        db.commit()

        return jsonify({'success': True}), 200

    except Exception as error:
        db.rollback()
        print(error)
        return jsonify({'success': False, 'message': 'Không thể xóa hội thoại'}), 500

    finally:
        cursor.close()
        db.close()
        
# =========================
# LÀM MỚI CUỘC TRÒ CHUYỆN VỚI AI
# =========================
@message_bp.route('/api/ai/reset', methods=['POST'])
def reset_ai_chat():

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'Thiếu user_id'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        conversation_id = reset_ai_conversation(db, cursor, user_id)

        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        }), 200

    except Exception as error:
        db.rollback()
        print(error)
        return jsonify({
            'success': False,
            'message': 'Không thể làm mới cuộc trò chuyện'
        }), 500

    finally:
        cursor.close()
        db.close()