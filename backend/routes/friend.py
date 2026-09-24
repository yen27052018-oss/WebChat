from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.extensions import socketio

friend_bp = Blueprint('friend', __name__)




@friend_bp.route('/api/send-friend-request', methods=['POST'])
def send_friend_request():
    data = request.get_json()
    sender_userid = data.get('sender_userid', '').strip()
    receiver_userid = data.get('receiver_userid', '').strip()
    if sender_userid == '' or receiver_userid == '':
        return jsonify({
            'success': False,
            'message': 'Thiếu thông tin người dùng'
        }), 400
    if sender_userid == receiver_userid:
        return jsonify({
            'success': False,
            'message': 'Không thể kết bạn với chính mình'
        }), 400
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Lấy ID thật của người gửi
        cursor.execute(
            '''
            SELECT id
            FROM users
            WHERE userid = %s
            ''',
            (sender_userid,)
        )
        sender = cursor.fetchone()
        if not sender:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy người gửi'
            }), 404

        # Lấy ID thật của người nhận
        cursor.execute(
            '''
            SELECT id
            FROM users
            WHERE userid = %s
            ''',
            (receiver_userid,)
        )
        receiver = cursor.fetchone()
        if not receiver:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy người dùng'
            }), 404
        sender_id = sender['id']
        receiver_id = receiver['id']

        # Kiểm tra lời mời đã tồn tại
        cursor.execute(
            '''
            SELECT id, status, sender_id, receiver_id
            FROM friend_requests
            WHERE
                (
                    sender_id = %s
                    AND receiver_id = %s
                )
                OR
                (
                    sender_id = %s
                    AND receiver_id = %s
                )
            ''',
            (
                sender_id,
                receiver_id,
                receiver_id,
                sender_id
            )
        )
        request_exist = cursor.fetchone()
        if request_exist:
            if request_exist['status'] == 'pending':
                return jsonify({
                    'success': False,
                    'message': 'Lời mời kết bạn đã tồn tại'
                }), 400
            if request_exist['status'] == 'accepted':
                return jsonify({
                    'success': False,
                    'message': 'Hai người đã là bạn bè'
                }), 400
                
        # Tạo lời mời mới
        cursor.execute(
            '''
            INSERT INTO friend_requests (
                sender_id,
                receiver_id,
                status
            )
            VALUES (%s, %s, 'pending')
            ''',
            (
                sender_id,
                receiver_id
            )
        )
        db.commit()
        return jsonify({
            'success': True,
            'message': 'Đã gửi lời mời kết bạn'
        }), 200
    except Exception as error:
        db.rollback()
        print(error)
        return jsonify({
            'success': False,
            'message': 'Không thể gửi lời mời kết bạn'
        }), 500

    finally:
        cursor.close()
        db.close()


@friend_bp.route('/api/friend-requests', methods=['GET'])
def get_friend_requests():

    userid = request.args.get('userid', '').strip()

    if userid == '':
        return jsonify({
            'success': False,
            'message': 'Thiếu mã người dùng'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # Tìm id thật của người nhận
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
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy người dùng'
            }), 404

        receiver_id = user['id']

        # Lấy lời mời đang chờ
        cursor.execute(
            '''
            SELECT
                fr.id,
                fr.sender_id,
                fr.receiver_id,
                fr.status,
                fr.created_at,
                u.userid,
                u.username,
                u.avatar
            FROM friend_requests fr
            JOIN users u
                ON fr.sender_id = u.id
            WHERE
                fr.receiver_id = %s
                AND fr.status = 'pending'
            ORDER BY fr.created_at DESC
            ''',
            (receiver_id,)
        )

        requests = cursor.fetchall()

        return jsonify({
            'success': True,
            'requests': requests
        }), 200

    except Exception as error:

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể lấy lời mời kết bạn'
        }), 500

    finally:

        cursor.close()
        db.close()
        
@friend_bp.route('/api/accept-friend-request', methods=['POST'])
def accept_friend_request():

    data = request.get_json()

    request_id = data.get('request_id')

    if not request_id:
        return jsonify({
            'success': False,
            'message': 'Thiếu ID lời mời'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # 1. Lấy lời mời kết bạn
        cursor.execute(
            '''
            SELECT sender_id, receiver_id, status
            FROM friend_requests
            WHERE id = %s
            ''',
            (request_id,)
        )

        friend_request = cursor.fetchone()

        if not friend_request:
            return jsonify({
                'success': False,
                'message': 'Lời mời kết bạn không tồn tại'
            }), 404

        if friend_request['status'] != 'pending':
            return jsonify({
                'success': False,
                'message': 'Lời mời này đã được xử lý'
            }), 400

        sender_id = friend_request['sender_id']
        receiver_id = friend_request['receiver_id']

        # 2. Đổi trạng thái lời mời
        cursor.execute(
            '''
            UPDATE friend_requests
            SET status = 'accepted'
            WHERE id = %s
            ''',
            (request_id,)
        )

        # 3. Kiểm tra conversation private đã tồn tại chưa
        cursor.execute(
            '''
            SELECT c.id
            FROM conversations c
            JOIN conversation_members cm1
                ON c.id = cm1.conversation_id
            JOIN conversation_members cm2
                ON c.id = cm2.conversation_id
            WHERE c.type = 'private'
                AND cm1.user_id = %s
                AND cm2.user_id = %s
            LIMIT 1
            ''',
            (sender_id, receiver_id)
        )

        conversation = cursor.fetchone()

        # 4. Nếu chưa có thì tạo conversation
        if conversation:

            conversation_id = conversation['id']

        else:

            cursor.execute(
                '''
                INSERT INTO conversations (type)
                VALUES ('private')
                '''
            )

            conversation_id = cursor.lastrowid

            # Thêm người gửi
            cursor.execute(
                '''
                INSERT INTO conversation_members
                (conversation_id, user_id)
                VALUES (%s, %s)
                ''',
                (conversation_id, sender_id)
            )

            # Thêm người nhận
            cursor.execute(
                '''
                INSERT INTO conversation_members
                (conversation_id, user_id)
                VALUES (%s, %s)
                ''',
                (conversation_id, receiver_id)
            )

        db.commit()

        socketio.emit(
            'friend_accepted',
            {
             'user_id': sender_id
            },
            to=f'user_{sender_id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Đã chấp nhận lời mời kết bạn',
            'conversation_id': conversation_id
        }), 200

    except Exception as error:

        db.rollback()

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể chấp nhận lời mời'
        }), 500

    finally:

        cursor.close()
        db.close()
        
@friend_bp.route('/api/conversations', methods=['GET'])
def get_conversations():

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'message': 'Thiếu user_id'
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute(
            '''
            SELECT
                c.id AS conversation_id,
                c.type,
                cm.user_id
            FROM conversations c
            JOIN conversation_members cm
                ON c.id = cm.conversation_id
            WHERE cm.user_id = %s
            ORDER BY c.updated_at DESC
            ''',
            (user_id,)
        )

        conversations = cursor.fetchall()

        result = []

        for conversation in conversations:

            conversation_id = conversation['conversation_id']

            # Lấy người còn lại trong conversation
            cursor.execute(
                '''
                SELECT
                    u.id,
                    u.userid,
                    u.username,
                    u.avatar
                FROM conversation_members cm
                JOIN users u
                    ON u.id = cm.user_id
                WHERE cm.conversation_id = %s
                    AND cm.user_id != %s
                LIMIT 1
                ''',
                (conversation_id, user_id)
            )
            
            user = cursor.fetchone()

            if not user:
                continue

            cursor.execute(
                    '''
                    SELECT
                        sender_id,
                        content,
                        message_type
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    ''',
                    (conversation_id,)
                )

            last_message = cursor.fetchone()    
            
            result.append({
                'conversation_id': conversation_id,
                'type': conversation['type'],
                'user': user,
                'last_message': last_message
            })

        return jsonify({
            'success': True,
            'conversations': result
        }), 200

    except Exception as error:

        print(error)

        return jsonify({
            'success': False,
            'message': 'Không thể lấy danh sách cuộc trò chuyện'
        }), 500

    finally:

        cursor.close()
        db.close()