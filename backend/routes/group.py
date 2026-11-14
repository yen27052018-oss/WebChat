import re

from flask import Blueprint, jsonify, request

from backend.database import get_db
from backend.extensions import socketio
from backend.group_avatar import refresh_auto_avatar

group_bp = Blueprint('group', __name__)

MAX_GROUP_MEMBERS = 50


def fail(message, status=400):
    return jsonify({'success': False, 'message': message}), status


def get_member(cursor, conversation_id, user_id):
    """Trả về dòng thành viên (có role) nếu user thuộc cuộc trò chuyện."""
    cursor.execute(
        '''
        SELECT role FROM conversation_members
        WHERE conversation_id = %s AND user_id = %s
        LIMIT 1
        ''',
        (conversation_id, user_id)
    )
    return cursor.fetchone()


def is_group(cursor, conversation_id):
    cursor.execute(
        'SELECT type FROM conversations WHERE id = %s',
        (conversation_id,)
    )
    row = cursor.fetchone()
    return bool(row and row['type'] == 'group')


# =========================
# DANH SÁCH NHÓM CỦA TÔI
# =========================
@group_bp.route('/api/groups', methods=['GET'])
def get_my_groups():

    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return fail('Thiếu user_id')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            '''
            SELECT
                c.id AS conversation_id,
                c.name,
                c.description,
                c.avatar,
                cm.role,
                (
                    SELECT COUNT(*) FROM conversation_members x
                    WHERE x.conversation_id = c.id
                ) AS member_count
            FROM conversations c
            JOIN conversation_members cm ON cm.conversation_id = c.id
            WHERE c.type = 'group' AND cm.user_id = %s
            ORDER BY c.updated_at DESC
            ''',
            (user_id,)
        )

        return jsonify({
            'success': True,
            'groups': cursor.fetchall()
        }), 200

    except Exception as error:
        print(error)
        return fail('Không thể lấy danh sách nhóm', 500)

    finally:
        cursor.close()
        db.close()


# =========================
# NHÓM CHUNG GIỮA TÔI VÀ MỘT NGƯỜI BẠN
# =========================
@group_bp.route('/api/groups/common', methods=['GET'])
def get_common_groups():

    user_id = request.args.get('user_id', type=int)
    friend_id = request.args.get('friend_id', type=int)

    if not user_id or not friend_id:
        return fail('Thiếu thông tin')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            '''
            SELECT
                c.id AS conversation_id,
                c.name,
                c.avatar,
                (
                    SELECT COUNT(*) FROM conversation_members x
                    WHERE x.conversation_id = c.id
                ) AS member_count
            FROM conversations c
            JOIN conversation_members a
                ON a.conversation_id = c.id AND a.user_id = %s
            JOIN conversation_members b
                ON b.conversation_id = c.id AND b.user_id = %s
            WHERE c.type = 'group'
            ORDER BY c.updated_at DESC
            ''',
            (user_id, friend_id)
        )

        return jsonify({
            'success': True,
            'groups': cursor.fetchall()
        }), 200

    except Exception as error:
        print(error)
        return fail('Không thể lấy nhóm chung', 500)

    finally:
        cursor.close()
        db.close()


# =========================
# THÔNG TIN NHÓM + DANH SÁCH THÀNH VIÊN
# =========================
@group_bp.route('/api/groups/<int:conversation_id>', methods=['GET'])
def get_group_info(conversation_id):

    user_id = request.args.get('user_id', type=int)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        member = get_member(cursor, conversation_id, user_id)

        if not member:
            return fail('Bạn không ở trong nhóm này', 403)

        cursor.execute(
            '''
            SELECT id, name, description, avatar, created_by
            FROM conversations
            WHERE id = %s AND type = 'group'
            ''',
            (conversation_id,)
        )
        group = cursor.fetchone()

        if not group:
            return fail('Không tìm thấy nhóm', 404)

        cursor.execute(
            '''
            SELECT u.id, u.userid, u.username, u.avatar, cm.role
            FROM conversation_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.conversation_id = %s
            ORDER BY (cm.role = 'admin') DESC, cm.joined_at ASC, cm.id ASC
            ''',
            (conversation_id,)
        )

        group['members'] = cursor.fetchall()
        group['my_role'] = member['role']

        return jsonify({'success': True, 'group': group}), 200

    except Exception as error:
        print(error)
        return fail('Không thể lấy thông tin nhóm', 500)

    finally:
        cursor.close()
        db.close()


# =========================
# MỞ NHÓM (hiện lại nếu tôi đã xóa hội thoại)
# =========================
@group_bp.route('/api/groups/open', methods=['POST'])
def open_group():

    data = request.get_json() or {}
    user_id = data.get('user_id')
    conversation_id = data.get('conversation_id')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        if (
            not get_member(cursor, conversation_id, user_id)
            or not is_group(cursor, conversation_id)
        ):
            return fail('Bạn không ở trong nhóm này', 403)

        cursor.execute(
            '''
            UPDATE conversation_members
            SET is_deleted = 0
            WHERE conversation_id = %s AND user_id = %s
            ''',
            (conversation_id, user_id)
        )
        db.commit()

        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        }), 200

    except Exception as error:
        db.rollback()
        print(error)
        return fail('Không thể mở nhóm', 500)

    finally:
        cursor.close()
        db.close()


# =========================
# THÊM THÀNH VIÊN
# =========================
@group_bp.route('/api/groups/<int:conversation_id>/members', methods=['POST'])
def add_group_members(conversation_id):

    data = request.get_json() or {}
    user_id = data.get('user_id')

    try:
        new_ids = {int(item) for item in data.get('member_ids', [])}
    except (ValueError, TypeError):
        new_ids = set()

    if not new_ids:
        return fail('Hãy chọn ít nhất 1 bạn bè')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        if (
            not get_member(cursor, conversation_id, user_id)
            or not is_group(cursor, conversation_id)
        ):
            return fail('Bạn không ở trong nhóm này', 403)

        # Bỏ những người đã ở trong nhóm
        cursor.execute(
            'SELECT user_id FROM conversation_members WHERE conversation_id = %s',
            (conversation_id,)
        )
        current_ids = {row['user_id'] for row in cursor.fetchall()}
        new_ids -= current_ids

        if not new_ids:
            return fail('Những người này đã ở trong nhóm')

        if len(current_ids) + len(new_ids) > MAX_GROUP_MEMBERS:
            return fail(f'Nhóm tối đa {MAX_GROUP_MEMBERS} thành viên')

        # Chỉ thêm được bạn bè của mình
        placeholders = ','.join(['%s'] * len(new_ids))

        cursor.execute(
            f'''
            SELECT COUNT(DISTINCT u.id) AS total
            FROM friend_requests fr
            JOIN users u
                ON u.id = IF(fr.sender_id = %s, fr.receiver_id, fr.sender_id)
            WHERE fr.status = 'accepted'
                AND (fr.sender_id = %s OR fr.receiver_id = %s)
                AND u.id IN ({placeholders})
            ''',
            (user_id, user_id, user_id, *new_ids)
        )

        if cursor.fetchone()['total'] != len(new_ids):
            return fail('Chỉ có thể thêm bạn bè vào nhóm', 403)

        for member_id in new_ids:
            cursor.execute(
                '''
                INSERT INTO conversation_members (conversation_id, user_id, role)
                VALUES (%s, %s, 'member')
                ''',
                (conversation_id, member_id)
            )
        refresh_auto_avatar(cursor, conversation_id)
        db.commit()

        # Người mới: nhóm xuất hiện trong danh sách. Người cũ: cập nhật số thành viên
        for member_id in new_ids:
            socketio.emit(
                'group_created',
                {'conversation_id': conversation_id},
                room=f'user_{member_id}'
            )

        for member_id in current_ids:
            socketio.emit(
                'group_updated',
                {'conversation_id': conversation_id},
                room=f'user_{member_id}'
            )

        return jsonify({'success': True}), 200

    except Exception as error:
        db.rollback()
        print(error)
        return fail('Không thể thêm thành viên', 500)

    finally:
        cursor.close()
        db.close()


# =========================
# RỜI NHÓM / GIẢI TÁN (khi chỉ còn 1 thành viên)
# =========================
@group_bp.route('/api/groups/<int:conversation_id>/leave', methods=['POST'])
def leave_group(conversation_id):

    data = request.get_json() or {}
    user_id = data.get('user_id')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        member = get_member(cursor, conversation_id, user_id)

        if not member or not is_group(cursor, conversation_id):
            return fail('Bạn không ở trong nhóm này', 403)

        # Những thành viên còn lại, người vào nhóm sớm nhất đứng đầu
        cursor.execute(
            '''
            SELECT user_id FROM conversation_members
            WHERE conversation_id = %s AND user_id != %s
            ORDER BY joined_at ASC, id ASC
            ''',
            (conversation_id, user_id)
        )
        others = [row['user_id'] for row in cursor.fetchall()]

        # Chỉ còn mình bạn: giải tán nhóm
        if not others:

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
            cursor.execute(
                'DELETE FROM conversation_members WHERE conversation_id = %s',
                (conversation_id,)
            )
            cursor.execute(
                'DELETE FROM conversations WHERE id = %s',
                (conversation_id,)
            )
            db.commit()

            return jsonify({'success': True, 'dissolved': True}), 200

        # Trưởng nhóm rời đi mà không còn trưởng nhóm nào khác: chuyển quyền
        if member['role'] == 'admin':
            cursor.execute(
                '''
                SELECT COUNT(*) AS total FROM conversation_members
                WHERE conversation_id = %s AND role = 'admin' AND user_id != %s
                ''',
                (conversation_id, user_id)
            )

            if cursor.fetchone()['total'] == 0:
                cursor.execute(
                    '''
                    UPDATE conversation_members
                    SET role = 'admin'
                    WHERE conversation_id = %s AND user_id = %s
                    ''',
                    (conversation_id, others[0])
                )

        cursor.execute(
            '''
            DELETE FROM conversation_members
            WHERE conversation_id = %s AND user_id = %s
            ''',
            (conversation_id, user_id)
        )
        refresh_auto_avatar(cursor, conversation_id)
        db.commit()

        for member_id in others:
            socketio.emit(
                'group_updated',
                {'conversation_id': conversation_id},
                room=f'user_{member_id}'
            )

        return jsonify({'success': True, 'dissolved': False}), 200

    except Exception as error:
        db.rollback()
        print(error)
        return fail('Không thể rời nhóm', 500)

    finally:
        cursor.close()
        db.close()


# =========================
# ẢNH / FILE / LINK ĐÃ GỬI TRONG HỘI THOẠI
# =========================
@group_bp.route('/api/conversations/<int:conversation_id>/media', methods=['GET'])
def get_conversation_media(conversation_id):

    user_id = request.args.get('user_id', type=int)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        if not get_member(cursor, conversation_id, user_id):
            return fail('Bạn không ở trong cuộc trò chuyện này', 403)

        visible = '''
            m.conversation_id = %s
            AND m.is_recalled = 0
            AND NOT EXISTS (
                SELECT 1 FROM message_deletions d
                WHERE d.message_id = m.id AND d.user_id = %s
            )
        '''

        # Ảnh và file
        cursor.execute(
            f'''
            SELECT m.id, m.content, m.file_name, m.message_type, m.created_at
            FROM messages m
            WHERE {visible} AND m.message_type IN ('image', 'file')
            ORDER BY m.id DESC
            LIMIT 300
            ''',
            (conversation_id, user_id)
        )
        rows = cursor.fetchall()

        images, files = [], []

        for row in rows:
            row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            (images if row['message_type'] == 'image' else files).append(row)

        # Link: tìm trong các tin nhắn văn bản
        cursor.execute(
            f'''
            SELECT m.id, m.content, m.created_at
            FROM messages m
            WHERE {visible}
                AND m.message_type = 'text'
                AND m.content REGEXP 'https?://'
            ORDER BY m.id DESC
            LIMIT 300
            ''',
            (conversation_id, user_id)
        )

        links = []

        for row in cursor.fetchall():
            created_at = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            for url in re.findall(r'https?://[^\s<>"\']+', row['content']):
                links.append({
                    'message_id': row['id'],
                    'url': url.rstrip('.,;:!?)'),
                    'created_at': created_at
                })

        return jsonify({
            'success': True,
            'images': images,
            'files': files,
            'links': links[:200]
        }), 200

    except Exception as error:
        print(error)
        return fail('Không thể lấy ảnh, file, link', 500)

    finally:
        cursor.close()
        db.close()
        
# =========================
# TRƯỞNG NHÓM XÓA THÀNH VIÊN
# =========================
@group_bp.route(
    '/api/groups/<int:conversation_id>/members/<int:member_id>/remove',
    methods=['POST']
)
def remove_group_member(conversation_id, member_id):

    data = request.get_json() or {}
    user_id = data.get('user_id')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        me = get_member(cursor, conversation_id, user_id)

        if not me or not is_group(cursor, conversation_id):
            return fail('Bạn không ở trong nhóm này', 403)

        if me['role'] != 'admin':
            return fail('Chỉ trưởng nhóm mới có thể xóa thành viên', 403)

        if str(member_id) == str(user_id):
            return fail('Hãy dùng chức năng Rời nhóm')

        if not get_member(cursor, conversation_id, member_id):
            return fail('Người này không ở trong nhóm', 404)

        cursor.execute(
            '''
            DELETE FROM conversation_members
            WHERE conversation_id = %s AND user_id = %s
            ''',
            (conversation_id, member_id)
        )

        refresh_auto_avatar(cursor, conversation_id)
        db.commit()

        # Người bị xóa thoát khỏi nhóm, những người còn lại cập nhật danh sách
        socketio.emit(
            'group_removed',
            {'conversation_id': conversation_id},
            room=f'user_{member_id}'
        )

        cursor.execute(
            'SELECT user_id FROM conversation_members WHERE conversation_id = %s',
            (conversation_id,)
        )

        for row in cursor.fetchall():
            socketio.emit(
                'group_updated',
                {'conversation_id': conversation_id},
                room=f"user_{row['user_id']}"
            )

        return jsonify({'success': True}), 200

    except Exception as error:
        db.rollback()
        print(error)
        return fail('Không thể xóa thành viên', 500)

    finally:
        cursor.close()
        db.close()