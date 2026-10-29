import base64
import json
import mimetypes
import os
import threading
import urllib.error
import urllib.request
from collections import defaultdict
import time

from backend.database import get_db
from backend.extensions import socketio
from backend.message_helper import get_message_by_id

REQUEST_TIMEOUT = 30        # mỗi lần gọi Gemini tối đa 30 giây
TOTAL_DEADLINE = 45         # tổng thời gian chờ Gemini tối đa 45 giây
RETRY_DELAYS = (1, 2)       # lỗi quá tải: thử lại sau 1 giây rồi 2 giây
RETRYABLE_CODES = (500, 502, 503, 504)

BOT_USERID = 'AI_BOT'
MAX_FILE_BYTES = 10 * 1024 * 1024   # ảnh/file gửi cho AI tối đa 10MB
HISTORY_LIMIT = 10                # AI nhớ 20 tin gần nhất
RECENT_ATTACHMENTS = 4              # chỉ đính kèm nội dung thật cho 4 tin gần nhất

GREETING = (
    'Hello ! mình là chatbot AI. '
    'bạn có thể gửi mình tin nhắn, ảnh và file, mình sẵn lòng hỗ trợ.'
)

SYSTEM_PROMPT = (
    'Bạn là trợ lý AI trong của một web chat, bạn tên là trợ lý AI. '
    'Trả lời bằng ngôn ngữ của người dùng (mặc định là tiếng Việt, Tiếng anh nếu người dùng yêu cầu), '
    'ngắn gọn, thân thiện như đang nhắn tin với bạn bè thực sự ngoài đời.\n\n'
    'Quy tắc định dạng bắt buộc:\n'
    '- Ứng dụng chỉ hiển thị văn bản thuần nên tuyệt đối KHÔNG dùng Markdown (không dùng dấu ** hay #).\n'
    '- Có thể xuống dòng và dùng dấu gạch đầu dòng "-" khi liệt kê thông tin.\n\n'
    'Quy tắc nhắn tin để giống người thật:\n'
    '- Độ dài: Chỉ nhắn từ 1 đến 3 câu ngắn cho mỗi tin nhắn. Không viết thành các đoạn văn dài dòng, trang trọng.\n'
    '- Cách dùng từ: Xưng hô tự nhiên mặc định bạn sẽ nhắn tui (ní - tui tùy theo người dùng nhắn như nào lựa chọn cho phù hợp với đoạn chat). Sử dụng ngôn từ tiếng Việt hiện đại, đời thường (có thể dùng từ cảm thán như: vậy hả, á đù dữ, kkk, nha, nè, ông/bà...).\n'
    '- Biểu cảm: Sử dụng emoji một cách hạn chế ở cuối câu để biểu lộ cảm xúc (ví dụ: 😂, 🥺, 🤔, ✨).\n'
    '- Tương tác: Biết hỏi ngược lại ở cuối tin nhắn để khơi gợi câu chuyện, thể hiện sự quan tâm thực sự đến người đối diện.'
)

_bot_id = None
_ensure_lock = threading.Lock()
_user_locks = defaultdict(threading.Lock)


# =========================
# BOT + CONVERSATION
# =========================

def get_bot_id():
    global _bot_id

    if _bot_id:
        return _bot_id

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute('SELECT id FROM users WHERE userid = %s', (BOT_USERID,))
        row = cursor.fetchone()

        if row:
            _bot_id = row['id']

        return _bot_id

    finally:
        cursor.close()
        db.close()


def add_bot_message(cursor, conversation_id, bot_id, text, status):
    cursor.execute(
        '''
        INSERT INTO messages (
            conversation_id, sender_id, content, message_type, status
        )
        VALUES (%s, %s, %s, 'text', %s)
        ''',
        (conversation_id, bot_id, text, status)
    )
    return cursor.lastrowid


def ensure_ai_conversation(db, cursor, user_id):
    """Đảm bảo người dùng có conversation riêng với AI, trả về conversation_id."""

    bot_id = get_bot_id()

    if not bot_id or str(user_id) == str(bot_id):
        return None

    with _ensure_lock:

        cursor.execute(
            '''
            SELECT c.id
            FROM conversations c
            JOIN conversation_members a
                ON a.conversation_id = c.id AND a.user_id = %s
            JOIN conversation_members b
                ON b.conversation_id = c.id AND b.user_id = %s
            WHERE c.type = 'private'
            LIMIT 1
            ''',
            (user_id, bot_id)
        )

        row = cursor.fetchone()

        if row:
            return row['id']

        cursor.execute("INSERT INTO conversations (type) VALUES ('private')")
        conversation_id = cursor.lastrowid

        for member_id in (user_id, bot_id):
            cursor.execute(
                '''
                INSERT INTO conversation_members (conversation_id, user_id)
                VALUES (%s, %s)
                ''',
                (conversation_id, member_id)
            )

        add_bot_message(cursor, conversation_id, bot_id, GREETING, 'sent')
        db.commit()

        return conversation_id


def is_ai_conversation(cursor, conversation_id):
    cursor.execute(
        '''
        SELECT 1
        FROM conversation_members cm
        JOIN users u ON u.id = cm.user_id
        WHERE cm.conversation_id = %s AND u.is_bot = 1
        LIMIT 1
        ''',
        (conversation_id,)
    )
    return cursor.fetchone() is not None


def reset_ai_conversation(db, cursor, user_id):
    """Xóa toàn bộ tin nhắn với AI và để AI chào lại từ đầu."""

    conversation_id = ensure_ai_conversation(db, cursor, user_id)

    if not conversation_id:
        return None

    cursor.execute(
        '''
        DELETE FROM message_deletions
        WHERE message_id IN (
            SELECT id FROM messages WHERE conversation_id = %s
        )
        ''',
        (conversation_id,)
    )
    cursor.execute(
        'DELETE FROM messages WHERE conversation_id = %s',
        (conversation_id,)
    )

    add_bot_message(
        cursor, conversation_id, get_bot_id(), GREETING, 'seen'
    )
    db.commit()

    return conversation_id


# =========================
# CHUẨN BỊ NỘI DUNG GỬI GEMINI
# =========================

def is_supported(mime):
    return (
        mime.startswith('image/')
        or mime.startswith('text/')
        or mime in ('application/pdf', 'application/json')
    )


def download_file(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(MAX_FILE_BYTES + 1)

    if len(data) > MAX_FILE_BYTES:
        raise ValueError('File quá lớn')

    return data


def message_to_parts(row, with_data):

    kind = row['message_type']

    if kind == 'text':
        return [{'text': row['content']}]

    if kind == 'voice':
        return [{'text': '[Người dùng gửi một tin nhắn thoại, bạn chưa nghe được]'}]

    label = 'một ảnh' if kind == 'image' else f'file "{row["file_name"]}"'

    caption = (row.get('caption') or '').strip()
    note = f' kèm lời nhắn: "{caption}"' if caption else ''

    # Tin cũ: chỉ ghi chú, không đính kèm lại để tiết kiệm
    if not with_data:
        return [{'text': f'[Người dùng đã gửi {label}{note} trước đó]'}]

    mime = mimetypes.guess_type(
        row['file_name'] or row['content'].split('?')[0]
    )[0] or ('image/jpeg' if kind == 'image' else 'application/octet-stream')

    if not is_supported(mime):
        return [{'text': (
            f'[Người dùng gửi {label}{note} nhưng định dạng ({mime}) '
            'chưa được hỗ trợ, bạn không đọc được nội dung]'
        )}]

    try:
        data = download_file(row['content'])
    except Exception as error:
        print('Không tải được file cho AI:', error)
        return [{'text': f'[Người dùng gửi {label}{note} nhưng không tải được nội dung]'}]

    return [
        {'text': f'[Người dùng gửi {label}{note}]'},
        {'inline_data': {
            'mime_type': mime,
            'data': base64.b64encode(data).decode('ascii')
        }}
    ]

def build_contents(cursor, conversation_id, user_id, bot_id):

    cursor.execute(
        '''
        SELECT m.id, m.sender_id, m.content, m.file_name, m.message_type, m.caption
        FROM messages m
        WHERE m.conversation_id = %s
            AND m.is_recalled = 0
            AND m.message_type IN ('text', 'image', 'file', 'voice')
            AND NOT EXISTS (
                SELECT 1 FROM message_deletions d
                WHERE d.message_id = m.id AND d.user_id = %s
            )
        ORDER BY m.created_at DESC, m.id DESC
        LIMIT %s
        ''',
        (conversation_id, user_id, HISTORY_LIMIT)
    )

    rows = list(reversed(cursor.fetchall()))
    contents = []

    for index, row in enumerate(rows):

        role = 'model' if str(row['sender_id']) == str(bot_id) else 'user'
        recent = index >= len(rows) - RECENT_ATTACHMENTS
        parts = message_to_parts(row, recent)

        # Gộp các tin liên tiếp cùng vai
        if contents and contents[-1]['role'] == role:
            contents[-1]['parts'].extend(parts)
        else:
            contents.append({'role': role, 'parts': parts})

    # Gemini cần bắt đầu bằng lượt của người dùng (bỏ lời chào của bot)
    while contents and contents[0]['role'] != 'user':
        contents.pop(0)

    return contents


# =========================
# GỌI GEMINI
# =========================

def get_models():
    """Model chính, sau đó là các model dự phòng (theo thứ tự thử)."""

    models = [os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')]

    fallbacks = os.getenv(
        'GEMINI_FALLBACK_MODELS',
        'gemini-3.5-flash-lite,gemini-3.6-flash'
    )
    models += [name.strip() for name in fallbacks.split(',') if name.strip()]

    return list(dict.fromkeys(models))   # bỏ trùng, giữ thứ tự


def call_gemini_once(model, contents, timeout):

    api_key = os.getenv('GEMINI_API_KEY')

    url = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{model}:generateContent'
    )

    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': contents
    }).encode('utf-8')

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key
        }
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode('utf-8'))

    candidates = data.get('candidates') or []

    if not candidates:
        return ''

    parts = candidates[0].get('content', {}).get('parts', [])
    return ''.join(part.get('text', '') for part in parts).strip()

def call_gemini(contents):
    """Thử lại khi quá tải, đổi sang model dự phòng, và không chờ quá TOTAL_DEADLINE."""

    started = time.monotonic()
    last_error = None

    for model in get_models():

        for attempt in range(len(RETRY_DELAYS) + 1):

            remaining = TOTAL_DEADLINE - (time.monotonic() - started)

            if remaining <= 2:
                raise last_error or TimeoutError('Quá thời gian chờ Gemini')

            try:
                return call_gemini_once(
                    model, contents, min(REQUEST_TIMEOUT, remaining)
                )

            except urllib.error.HTTPError as error:
                last_error = error
                body = error.read().decode('utf-8', 'ignore')
                print(f'Gemini [{model}] lỗi HTTP {error.code}:', body[:300])

                # Không phải lỗi quá tải (sai model, hết hạn mức...): sang model khác
                if error.code not in RETRYABLE_CODES:
                    break

            except OSError as error:      # hết thời gian chờ, mất kết nối...
                last_error = error
                print(f'Gemini [{model}] lỗi kết nối:', error)

            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])

    raise last_error or RuntimeError('Không gọi được Gemini')


def generate_answer(cursor, conversation_id, user_id, bot_id):

    if not os.getenv('GEMINI_API_KEY'):
        return 'Chưa cấu hình khóa Gemini (GEMINI_API_KEY) trong file .env nên mình chưa trả lời được.'

    try:
        contents = build_contents(cursor, conversation_id, user_id, bot_id)
        answer = call_gemini(contents).replace('**', '')

        return answer or 'Từ từ mình chưa nghĩ ra câu trả lời, bạn thử hỏi lại được không.'

    except urllib.error.HTTPError as error:

        if error.code == 429:
            return 'Mình đang bị giới hạn lượt dùng, bạn thử lại sau ít phút nhé.'

        if error.code in RETRYABLE_CODES:
            return 'AI đang quá tải một chút, bạn thử lại sau ít phút nhé 🥺'

        return 'Xin lỗi, mình đang gặp sự cố khi trả lời. Bạn thử lại sau nhé.'

    except OSError as error:
        print('Lỗi AI (kết nối):', error)
        return 'AI phản hồi quá lâu, bạn thử lại sau nhé.'

    except Exception as error:
        print('Lỗi AI:', error)
        return 'Xin lỗi, mình đang gặp sự cố khi trả lời. Bạn thử lại sau nhé.'

# =========================
# TÁC VỤ NỀN: AI TRẢ LỜI
# =========================

def reply_as_ai(conversation_id, user_id, message_id):

    bot_id = get_bot_id()
    user_room = f'user_{user_id}'

    def send_typing(is_typing):
        socketio.emit(
            'typing',
            {
                'conversation_id': conversation_id,
                'sender_id': bot_id,
                'is_typing': is_typing
            },
            room=user_room
        )

    # Mỗi người dùng trả lời lần lượt, không chạy chồng
    with _user_locks[str(user_id)]:

        send_typing(True)

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            answer = generate_answer(cursor, conversation_id, user_id, bot_id)

            # Tin gốc đã bị xóa (người dùng làm mới cuộc trò chuyện) thì bỏ qua
            cursor.execute('SELECT id FROM messages WHERE id = %s', (message_id,))

            if not cursor.fetchone():
                return

            new_id = add_bot_message(
                cursor, conversation_id, bot_id, answer, 'sent'
            )

            cursor.execute(
                'UPDATE conversations SET updated_at = NOW() WHERE id = %s',
                (conversation_id,)
            )
            db.commit()

            message = get_message_by_id(cursor, new_id)
            socketio.emit('new_message', message, room=user_room)

        except Exception as error:
            db.rollback()
            print('Lỗi khi AI trả lời:', error)

        finally:
            cursor.close()
            db.close()
            send_typing(False)


def maybe_reply_ai(conversation_id, sender_id, receiver_id, message_id):
    """Gọi sau khi lưu tin nhắn: nếu người nhận là AI thì AI trả lời."""

    bot_id = get_bot_id()

    if (
        bot_id
        and str(receiver_id) == str(bot_id)
        and str(sender_id) != str(bot_id)
    ):
        socketio.start_background_task(
            reply_as_ai, conversation_id, sender_id, message_id
        )