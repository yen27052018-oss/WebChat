import os

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room

from backend.database import get_db

from backend.routes.register import register_bp
from backend.routes.login import login_bp
from backend.routes.profile import profile_bp
from backend.routes.friend import friend_bp
from backend.routes.message import message_bp


app = Flask(__name__)

CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins='*'
)


# Lưu những user đang online
# Ví dụ:
# {
#     '1': {'socket_id_1'},
#     '2': {'socket_id_2'}
# }
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

    # Room riêng của user
    user_room = f'user_{user_id}'

    join_room(user_room)

    # Nếu user chưa có trong danh sách online
    if user_id not in online_users:

        online_users[user_id] = set()

    # Lưu socket hiện tại
    online_users[user_id].add(
        request.sid
    )

    print(
        f'User {user_id} đã online'
        f' - socket: {request.sid}'
    )

    # Thông báo cho tất cả client
    socketio.emit(
        'user_online',
        {
            'user_id': user_id
        }
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


    # Tìm socket thuộc user nào
    for user_id in list(
        online_users.keys()
    ):

        if (
            socket_id
            in online_users[user_id]
        ):

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


# =========================
# REGISTER BLUEPRINT
# =========================

app.register_blueprint(
    register_bp
)

app.register_blueprint(
    login_bp
)

app.register_blueprint(
    profile_bp
)

app.register_blueprint(
    friend_bp
)

app.register_blueprint(
    message_bp
)


# =========================
# HOME
# =========================

@app.route('/')
def home():

    return (
        'CHAT & WATCH Backend '
        'đang hoạt động!'
    )


# =========================
# UPLOADS
# =========================

@app.route(
    '/uploads/<path:filename>'
)
def uploaded_file(filename):

    upload_folder = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ),
        'uploads'
    )

    return send_from_directory(
        upload_folder,
        filename
    )


# =========================
# RUN
# =========================

if __name__ == '__main__':

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )