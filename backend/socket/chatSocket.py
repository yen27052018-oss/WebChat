from flask import request
from flask_socketio import join_room

from backend.extensions import socketio
from backend.database import get_db
from threading import Timer
import time

online_users = {}
ringing_calls = {}
active_calls = {}
call_timers = {}
call_callers = {}
call_start_times = {}
call_types = {}

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
        
# =========================
# SAVE CALL MESSAGE
# =========================

def save_call_message(
    caller_id,
    receiver_id,
    call_status,
    call_duration=None
):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # =========================
        # TÌM CONVERSATION
        # =========================

        cursor.execute(
            '''
            SELECT c.id
            FROM conversations c

            JOIN conversation_members cm1
                ON cm1.conversation_id = c.id

            JOIN conversation_members cm2
                ON cm2.conversation_id = c.id

            WHERE cm1.user_id = %s
                AND cm2.user_id = %s

            LIMIT 1
            ''',
            (
                caller_id,
                receiver_id
            )
        )

        conversation = cursor.fetchone()

        if not conversation:

            print(
                'Không tìm thấy conversation:',
                caller_id,
                receiver_id
            )

            return None

        conversation_id = conversation['id']

        # =========================
        # XÁC ĐỊNH STATUS
        # =========================

        message_status = (
            'delivered'
            if receiver_id in online_users
            else 'sent'
        )

        # =========================
        # INSERT CALL MESSAGE
        # =========================
        call_type = call_types.get(str(caller_id), 'voice')
        cursor.execute(
            '''
            INSERT INTO messages (
                conversation_id,
                sender_id,
                content,
                message_type,
                call_type,
                call_duration,
                status
            )

            VALUES (
                %s,
                %s,
                %s,
                'call',
                %s,
                %s,
                %s
            )
            ''',
            (
                conversation_id,
                caller_id,
                call_status,
                call_type,
                call_duration,
                message_status
            )
        )

        message_id = cursor.lastrowid

        # =========================
        # UPDATE CONVERSATION
        # =========================

        cursor.execute(
            '''
            UPDATE conversations

            SET updated_at =
                CURRENT_TIMESTAMP

            WHERE id = %s
            ''',
            (
                conversation_id,
            )
        )

        db.commit()

        # =========================
        # LẤY MESSAGE VỪA INSERT
        # =========================

        cursor.execute(
            '''
            SELECT
                m.id,
                m.conversation_id,
                m.sender_id,
                m.content,
                m.message_type,
                m.call_type,
                m.call_duration,
                m.status,
                m.created_at

            FROM messages m

            WHERE m.id = %s
            ''',
            (
                message_id,
            )
        )

        message = cursor.fetchone()

        if message:

            if message['created_at']:

                message['created_at'] = \
                    message['created_at'].strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )

        print(
            'Đã lưu call message:',
            message
        )

        return message

    except Exception as error:

        db.rollback()

        print(
            'Lỗi lưu lịch sử cuộc gọi:',
            error
        )

        return None

    finally:

        cursor.close()
        db.close()


# =========================
# CALL REQUEST
# =========================

@socketio.on('call_request')
def handle_call_request(data):

    caller_id = data.get(
        'caller_id'
    )

    receiver_id = data.get(
        'receiver_id'
    )

    if (
        not caller_id
        or not receiver_id
    ):
        return

    caller_id = str(caller_id)
    receiver_id = str(receiver_id)
    
    call_type = data.get( 'call_type', 'voice')

    if call_type not in ( 'voice', 'video'):
        call_type = 'voice'

    # =========================
    # KIỂM TRA NGƯỜI GỌI
    # =========================

    if (
        caller_id in active_calls
        or caller_id in ringing_calls
    ):

        socketio.emit(
            'call_error',
            {
                'type': 'busy',
                'user_id': caller_id,
                'message':
                    'Bạn đang trong cuộc gọi'
            },
            room=f'user_{caller_id}'
        )

        return

    # =========================
    # KIỂM TRA NGƯỜI NHẬN
    # =========================

    if (
        receiver_id in active_calls
        or receiver_id in ringing_calls
    ):

        socketio.emit(
            'call_busy',
            {
                'user_id': receiver_id,
                'message':
                    'Người dùng đang trong cuộc gọi'
            },
            room=f'user_{caller_id}'
        )

        return

    # =========================
    # LƯU TRẠNG THÁI RINGING
    # =========================

    ringing_calls[caller_id] = receiver_id
    ringing_calls[receiver_id] = caller_id
    
    call_types[caller_id] = call_type
    call_types[receiver_id] = call_type

    # Lưu người gọi ban đầu
    call_callers[caller_id] = caller_id
    call_callers[receiver_id] = caller_id

    # =========================
    # GỬI CUỘC GỌI
    # =========================

    socketio.emit(
        'incoming_call',
        {
            'caller_id': caller_id,
            'call_type': call_type
        },
        room=f'user_{receiver_id}'
    )

    # =========================
    # TIMER 60 GIÂY
    # =========================

    timer = Timer(
        60,
        handle_call_timeout,
        args=(
            caller_id,
            receiver_id
        )
    )

    call_timers[caller_id] = timer

    timer.start()


# =========================
# CALL TIMEOUT
# =========================

# =========================
# CALL TIMEOUT
# =========================

def handle_call_timeout(caller_id, receiver_id):

    caller_id = str(caller_id)
    receiver_id = str(receiver_id)

    # Cuộc gọi không còn ringing
    if (
        caller_id not in ringing_calls
        or
        ringing_calls.get(caller_id)
        != receiver_id
    ):
        return

    # =========================
    # XÓA TIMER
    # =========================

    call_timers.pop(
        caller_id,
        None
    )

    # =========================
    # LƯU LỊCH SỬ
    # =========================

    message = save_call_message(
        caller_id,
        receiver_id,
        'timeout'
    )

    # =========================
    # GỬI LỊCH SỬ CHO 2 USER
    # =========================

    if message:

        socketio.emit(
            'new_message',
            message,
            room=f'user_{caller_id}'
        )

        socketio.emit(
            'new_message',
            message,
            room=f'user_{receiver_id}'
        )

    # =========================
    # BÁO CALLER
    # =========================

    socketio.emit(
        'call_timeout',
        {
            'type': 'caller',
            'user_id': receiver_id
        },
        room=f'user_{caller_id}'
    )

    # =========================
    # BÁO RECEIVER
    # =========================

    socketio.emit(
        'call_timeout',
        {
            'type': 'receiver',
            'user_id': caller_id
        },
        room=f'user_{receiver_id}'
    )

    print(
        f'Cuộc gọi {caller_id} -> '
        f'{receiver_id} đã quá 60 giây'
    )

# =========================
# CALL REJECT
# =========================

# =========================
# CALL REJECT
# =========================

@socketio.on('call_reject')
def handle_call_reject(data):

    caller_id = data.get(
        'caller_id'
    )

    receiver_id = data.get(
        'receiver_id'
    )

    if (
        not caller_id
        or not receiver_id
    ):
        return

    caller_id = str(caller_id)
    receiver_id = str(receiver_id)

    # =========================
    # KIỂM TRA CUỘC GỌI
    # =========================

    if (
        caller_id not in ringing_calls
        or
        ringing_calls.get(caller_id)
        != receiver_id
    ):
        return

    # =========================
    # HỦY TIMER
    # =========================

    timer = call_timers.pop(
        caller_id,
        None
    )

    if timer:
        timer.cancel()

    # =========================
    # XÓA RINGING
    # =========================

    ringing_calls.pop(
        caller_id,
        None
    )

    ringing_calls.pop(
        receiver_id,
        None
    )

    # =========================
    # LƯU LỊCH SỬ
    # =========================

    message = save_call_message(
        caller_id,
        receiver_id,
        'rejected'
    )

    # =========================
    # GỬI LỊCH SỬ CHO 2 USER
    # =========================

    if message:

        socketio.emit(
            'new_message',
            message,
            room=f'user_{caller_id}'
        )

        socketio.emit(
            'new_message',
            message,
            room=f'user_{receiver_id}'
        )

    # =========================
    # BÁO TỪ CHỐI CHO CALLER
    # =========================

    socketio.emit(
        'call_rejected',
        {
            'user_id': receiver_id
        },
        room=f'user_{caller_id}'
    )

    # =========================
    # BÁO TỪ CHỐI CHO RECEIVER
    # =========================

    socketio.emit(
        'call_rejected',
        {
            'user_id': caller_id
        },
        room=f'user_{receiver_id}'
    )

    print(
        f'{receiver_id} đã từ chối '
        f'cuộc gọi từ {caller_id}'
    )


# =========================
# CALL END / CANCEL
# =========================

# =========================
# CALL END / CANCEL
# =========================

@socketio.on('call_end')
def handle_call_end(data):

    user_id = data.get(
        'user_id'
    )

    if not user_id:
        return

    user_id = str(user_id)

    # =========================
    # ĐANG ĐỔ CHUÔNG
    # =========================

    if user_id in ringing_calls:

        other_user_id = (
            ringing_calls[user_id]
        )

        # =========================
        # LẤY NGƯỜI GỌI BAN ĐẦU
        # =========================

        caller_id = call_callers.get(
            user_id
        )

        if not caller_id:

            caller_id = call_callers.get(
                other_user_id
            )

        if not caller_id:
            return

        # =========================
        # HỦY TIMER
        # =========================

        timer = call_timers.pop(
            caller_id,
            None
        )

        if timer:
            timer.cancel()

        # =========================
        # XÓA RINGING
        # =========================

        ringing_calls.pop(
            user_id,
            None
        )

        ringing_calls.pop(
            other_user_id,
            None
        )

        # =========================
        # LƯU LỊCH SỬ
        # =========================

        message = save_call_message(
            caller_id,
            other_user_id
            if caller_id == user_id
            else user_id,
            'cancelled'
        )

        # =========================
        # GỬI LỊCH SỬ CHO 2 USER
        # =========================

        if message:

            socketio.emit(
                'new_message',
                message,
                room=f'user_{caller_id}'
            )

            socketio.emit(
                'new_message',
                message,
                room=f'user_{other_user_id}'
            )

        # =========================
        # XÓA CALL CALLERS
        # =========================

        call_callers.pop(
            caller_id,
            None
        )

        call_callers.pop(
            other_user_id,
            None
        )

        # =========================
        # BÁO HỦY CHO NGƯỜI CÒN LẠI
        # =========================

        socketio.emit(
            'call_cancelled',
            {
                'user_id': user_id
            },
            room=f'user_{other_user_id}'
        )

        print(
            f'{caller_id} đã hủy cuộc gọi '
            f'tới {other_user_id}'
        )

        return

    # =========================
    # ĐANG ACTIVE CALL
    # =========================

    if user_id not in active_calls:
        return

    other_user_id = active_calls[user_id]

    # =========================
    # XÁC ĐỊNH CALLER GỐC
    # =========================

    caller_id = call_callers.get(user_id)

    if not caller_id:
        return

    caller_id = str(caller_id)

    if caller_id == user_id:
        receiver_id = other_user_id
    else:
        receiver_id = user_id

    # =========================
    # TÍNH THỜI GIAN
    # =========================

    start_time = call_start_times.get(user_id)

    if start_time:
        call_duration = int(
            time.time() - start_time
        )
    else:
        call_duration = 0

    # =========================
    # XÓA ACTIVE CALL
    # =========================

    active_calls.pop(
        user_id,
        None
    )

    active_calls.pop(
        other_user_id,
        None
    )

    # =========================
    # XÓA THỜI GIAN
    # =========================

    call_start_times.pop(
        user_id,
        None
    )

    call_start_times.pop(
        other_user_id,
        None
    )

    # =========================
    # XÓA CALLER
    # =========================

    call_callers.pop(
        user_id,
        None
    )

    call_callers.pop(
        other_user_id,
        None
    )

    # =========================
    # LƯU LỊCH SỬ
    # =========================

    message = save_call_message(
        caller_id,
        receiver_id,
        'accepted',
        call_duration
    )

    # =========================
    # GỬI LỊCH SỬ CHO 2 NGƯỜI
    # =========================

    if message:

        socketio.emit(
            'new_message',
            message,
            room=f'user_{caller_id}'
        )

        socketio.emit(
            'new_message',
            message,
            room=f'user_{receiver_id}'
        )

    # =========================
    # BÁO KẾT THÚC
    # =========================

    socketio.emit(
        'call_ended',
        {
            'user_id': user_id,
            'duration': call_duration
        },
        room=f'user_{other_user_id}'
    )


# =========================
# CALL ACCEPT
# =========================

# =========================
# CALL ACCEPT
# =========================

@socketio.on('call_accept')
def handle_call_accept(data):

    caller_id = data.get(
        'caller_id'
    )

    receiver_id = data.get(
        'receiver_id'
    )

    if (
        not caller_id
        or not receiver_id
    ):
        return

    caller_id = str(caller_id)
    receiver_id = str(receiver_id)
    call_type = call_types.get(
        caller_id,
        'voice'
    )

    # =========================
    # KIỂM TRA CUỘC GỌI
    # =========================

    if (
        caller_id not in ringing_calls
        or
        ringing_calls.get(caller_id)
        != receiver_id
    ):
        return

    # =========================
    # HỦY TIMER
    # =========================

    timer = call_timers.pop(
        caller_id,
        None
    )

    if timer:
        timer.cancel()

    # =========================
    # XÓA RINGING
    # =========================

    ringing_calls.pop(
        caller_id,
        None
    )

    ringing_calls.pop(
        receiver_id,
        None
    )

    active_calls[caller_id] = receiver_id

    active_calls[receiver_id] = caller_id
    
    start_time = time.time()

    call_start_times[caller_id] = start_time
    call_start_times[receiver_id] = start_time


    call_callers[caller_id] = caller_id
    
    call_callers[receiver_id] = caller_id
    

    # =========================
    # BÁO CHO CALLER
    # =========================

    socketio.emit(
        'call_accepted',
        {
            'user_id': receiver_id,
            'call_type': call_type
        },
        room=f'user_{caller_id}'
    )

    # =========================
    # BÁO CHO RECEIVER
    # =========================

    socketio.emit(
        'call_accepted',
        {
            'user_id': caller_id,
            'call_type': call_type
        },
        room=f'user_{receiver_id}'
    )

    print(
        f'{receiver_id} đã nhận cuộc gọi '
        f'từ {caller_id}'
    )
    
    
    
# WEB RTC 

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):

    target_user_id = data.get(
        'target_user_id'
    )

    caller_id = data.get(
        'user_id'
    )

    offer = data.get(
        'offer'
    )

    if (
        not target_user_id
        or not caller_id
        or not offer
    ):
        return

    target_user_id = str(
        target_user_id
    )

    caller_id = str(
        caller_id
    )

    socketio.emit(
        'webrtc_offer',
        {
            'user_id': caller_id,
            'offer': offer
        },
        room=f'user_{target_user_id}'
    )

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):

    target_user_id = data.get(
        'target_user_id'
    )

    user_id = data.get(
        'user_id'
    )

    answer = data.get(
        'answer'
    )

    if (
        not target_user_id
        or not user_id
        or not answer
    ):
        return

    target_user_id = str(
        target_user_id
    )

    user_id = str(
        user_id
    )

    socketio.emit(
        'webrtc_answer',
        {
            'user_id': user_id,
            'answer': answer
        },
        room=f'user_{target_user_id}'
    )


@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice_candidate(data):

    target_user_id = data.get(
        'target_user_id'
    )

    user_id = data.get(
        'user_id'
    )

    candidate = data.get(
        'candidate'
    )

    if (
        not target_user_id
        or not user_id
        or not candidate
    ):
        return

    target_user_id = str(
        target_user_id
    )

    user_id = str(
        user_id
    )

    socketio.emit(
        'webrtc_ice_candidate',
        {
            'user_id': user_id,
            'candidate': candidate
        },
        room=f'user_{target_user_id}'
    )
    
@socketio.on('call_video_toggle')
def handle_call_video_toggle(data):
    user_id = data.get('user_id')
    target_user_id = data.get('target_user_id')

    if not user_id or not target_user_id:
        return

    socketio.emit(
        'call_video_toggle',
        {
            'user_id': str(user_id),
            'is_video_on': bool(data.get('is_video_on'))
        },
        room=f'user_{target_user_id}'
    )