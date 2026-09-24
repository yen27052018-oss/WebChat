from flask import request
from flask_socketio import join_room

from backend.extensions import socketio
from backend.database import get_db

online_users = {}

# =========================
# SOCKET.IO CONNECT
# =========================

@socketio.on('connect')
def handle_connect():

    print(
        'Có client vừa kết nối Socket.IO'
    )
    
# =========================
# USER ONLINE
# =========================

@socketio.on('user_online')
def handle_user_online(data):

    user_id = data.get('user_id')

    if not user_id:
        return

    user_id = str(user_id)

    user_room = f'user_{user_id}'

    join_room(user_room)

    if user_id not in online_users:

        online_users[user_id] = set()

    online_users[user_id].add(
        request.sid
    )

    print(
        f'User {user_id} đã online'
        f' - socket: {request.sid}'
    )

    socketio.emit(
        'user_online',
        {
            'user_id': user_id
        }
    )
    
@socketio.on('check_user_online')
def handle_check_user_online(data):

    user_id = data.get('user_id')

    if not user_id:
        return

    user_id = str(user_id)

    is_online = user_id in online_users

    socketio.emit(
        'user_online_status',
        {
            'user_id': user_id,
            'is_online': is_online
        },
        to=request.sid
    )
    
# =========================
# JOIN CONVERSATION
# =========================

@socketio.on('join_conversation')
def handle_join_conversation(data):

    conversation_id = data.get(
        'conversation_id'
    )

    user_id = data.get(
        'user_id'
    )

    if not conversation_id or not user_id:
        return

    room = (
        f'conversation_{conversation_id}'
    )

    join_room(room)

    print(
        f'User {user_id} đã vào room {room}'
    )
    
# =========================
# SEND MESSAGE
# =========================

@socketio.on('send_message')
def handle_send_message(data):
    conversation_id = data.get(
        'conversation_id'
    )
    sender_id = data.get(
        'sender_id'
    )
    content = data.get(
        'content',
        ''
    ).strip()
    if (
        not conversation_id
        or not sender_id
        or not content
    ):
        return
    db = get_db()
    cursor = db.cursor(
        dictionary=True
    )
    try:

        # =========================
        # KIỂM TRA NGƯỜI GỬI
        # =========================
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
            print(
                'User không thuộc cuộc trò chuyện'
            )
            return
        # =========================
        # TÌM NGƯỜI NHẬN
        # =========================

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

            print(
                'Không tìm thấy người nhận'
            )

            return
        receiver_id = receiver[
            'user_id'
        ]

        # =========================
        # KIỂM TRA ONLINE
        # =========================
        receiver_online = (
            str(receiver_id)
            in online_users
        )
        # =========================
        # XÁC ĐỊNH STATUS BAN ĐẦU
        # =========================
        status = (
            'delivered'
            if receiver_online
            else 'sent'
        )
        # =========================
        # LƯU TIN NHẮN
        # =========================
        cursor.execute(
            '''
            INSERT INTO messages (
                conversation_id,
                sender_id,
                content,
                message_type,
                status
            )
            VALUES (%s, %s, %s,'text', %s)
            ''',
            (
                conversation_id,
                sender_id,
                content,
                status
            )
        )

        message_id = cursor.lastrowid
        # =========================
        # CẬP NHẬT CONVERSATION
        # =========================

        cursor.execute(
            '''
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''',
            (conversation_id,)
        )
        db.commit()
        # ========================
        # LẤY LẠI MESSAGE
        # =========================
        cursor.execute(
            '''
            SELECT
                m.id,
                m.conversation_id,
                m.sender_id,
                u.username AS sender_username,
                u.avatar AS sender_avatar,
                m.content,
                m.message_type,
                m.status,
                m.created_at,
                m.seen_at
            FROM messages m
            JOIN users u
                ON u.id = m.sender_id
            WHERE m.id = %s
            ''',
            (message_id,)
        )
        message = cursor.fetchone()
        # =========================
        # FORMAT DATETIME
        # =========================
        if message['created_at']:
            message['created_at'] = (
                message['created_at']
                .strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
            )
        if message['seen_at']:
            message['seen_at'] = (
                message['seen_at']
                .strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
            )
        # =========================
        # GỬI TIN ĐẾN USER NHẬN
        # ========================
        receiver_room = (
            f'user_{receiver_id}'
        )
        socketio.emit(
            'new_message',
            message,
            room=receiver_room
        )
        # =========================
        # GỬI MESSAGE CHO NGƯỜI GỬI
        # =========================
        sender_room = (
            f'user_{sender_id}'
        )

        socketio.emit(
            'new_message',
            message,
            room=sender_room
        )
        # =========================
        # CẬP NHẬT STATUS CHO NGƯỜI GỬI
        # =========================

        socketio.emit(
            'message_status',
            {
                'message_id': message_id,

                'conversation_id':
                    conversation_id,

                'status': status
            },
            room=sender_room
        )


        print(
            f'Đã lưu tin nhắn {message_id}'
            f' - status: {status}'
        )

    except Exception as error:

        db.rollback()

        print(
            'Lỗi Socket.IO khi lưu tin nhắn:',
            error
        )

    finally:

        cursor.close()
        db.close()


# =========================
# MESSAGE SEEN
# =========================

@socketio.on('message_seen')
def handle_message_seen(data):

    conversation_id = data.get(
        'conversation_id'
    )

    user_id = data.get(
        'user_id'
    )

    if (
        not conversation_id
        or not user_id
    ):
        return

    db = get_db()
    cursor = db.cursor(
        dictionary=True
    )

    try:

        # =========================
        # KIỂM TRA MEMBER
        # =========================

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
            return


        # =========================
        # UPDATE SEEN
        # =========================

        cursor.execute(
            '''
            UPDATE messages
            SET
                status = 'seen',
                seen_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
                AND sender_id != %s
                AND status IN ('sent', 'delivered')
            ''',
            (
                conversation_id,
                user_id
            )
        )

        db.commit()


        # =========================
        # THÔNG BÁO STATUS
        # =========================

        room = (
            f'conversation_{conversation_id}'
        )

        socketio.emit(
            'message_status',
            {
                'conversation_id':
                    conversation_id,

                'status': 'seen'
            },
            room=room
        )


        print(
            f'User {user_id} đã xem '
            f'conversation {conversation_id}'
        )

    except Exception as error:

        db.rollback()

        print(
            'Lỗi cập nhật seen:',
            error
        )

    finally:

        cursor.close()
        db.close()
        
# =========================
# DISCONNECT
# =========================

@socketio.on('disconnect')
def handle_disconnect():
    socket_id = request.sid
    offline_user = None
    
    for user_id in list(
        online_users.keys()
    ):
        if socket_id in online_users[user_id]:
            online_users[user_id].remove(
                socket_id
            )

            # Nếu user không còn socket nào
            # thì user thực sự offline
            if not online_users[user_id]:

                del online_users[
                    user_id
                ]

                offline_user = user_id

            break

    if offline_user:

        print(
            f'User {offline_user} đã offline'
        )

        # Thông báo cho client
        socketio.emit(
            'user_offline',
            {
                'user_id': offline_user
            }
        )

    else:

        print(
            'Client đã ngắt kết nối Socket.IO'
        )