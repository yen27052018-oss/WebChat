MESSAGE_SELECT = '''
    SELECT
        m.id,
        m.conversation_id,
        m.sender_id,
        u.username AS sender_username,
        u.avatar AS sender_avatar,
        m.content,
        m.file_name,
        m.caption,
        m.message_type,
        m.call_type,
        m.call_duration,
        m.status,
        m.created_at,
        m.seen_at,
        m.is_recalled,
        m.reply_to_id,
        r.content AS reply_content,
        r.file_name AS reply_file_name,
        r.message_type AS reply_type,
        r.is_recalled AS reply_is_recalled,
        ru.username AS reply_username
    FROM messages m
    JOIN users u ON u.id = m.sender_id
    LEFT JOIN messages r ON r.id = m.reply_to_id
    LEFT JOIN users ru ON ru.id = r.sender_id
'''


def format_message(message):
    for key in ('created_at', 'seen_at'):
        if message.get(key):
            message[key] = message[key].strftime('%Y-%m-%d %H:%M:%S')
    return message


def get_message_by_id(cursor, message_id):
    cursor.execute(MESSAGE_SELECT + ' WHERE m.id = %s', (message_id,))
    message = cursor.fetchone()
    return format_message(message) if message else None