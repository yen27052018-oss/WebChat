import os
import uuid
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

from backend.database import get_db

PROJECT_FOLDER = Path(__file__).resolve().parents[1]          # WEB_Chat
UPLOAD_FOLDER = PROJECT_FOLDER.parent / 'WEB_Chat_Uploads'
GROUP_FOLDER = UPLOAD_FOLDER / 'group_avatars'
DEFAULT_AVATAR = PROJECT_FOLDER / 'assests' / 'img' / 'default_avt.png'

AUTO_PREFIX = 'group_auto_'
AUTO_URL_PREFIX = f'/uploads/group_avatars/{AUTO_PREFIX}'

SIZE = 256
RING = 3

# Số ô -> (đường kính, tâm các ô). Tất cả nằm gọn trong hình tròn nội tiếp
LAYOUTS = {
    1: (236, [(128, 128)]),
    2: (116, [(82, 82), (174, 174)]),
    3: (104, [(128, 76), (80, 160), (176, 160)]),
    4: (100, [(80, 80), (176, 80), (80, 176), (176, 176)])
}


def member_image_path(avatar):
    if avatar and avatar.startswith('/uploads/'):
        path = UPLOAD_FOLDER / avatar[len('/uploads/'):]

        if path.exists():
            return path

    return DEFAULT_AVATAR


def circle_image(path, diameter):

    try:
        image = Image.open(path).convert('RGBA')
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        image = image.resize((diameter, diameter), Image.LANCZOS)
    except Exception:
        image = Image.new('RGBA', (diameter, diameter), (174, 183, 196, 255))

    # Nền trắng cho ảnh có vùng trong suốt
    background = Image.new('RGBA', image.size, (255, 255, 255, 255))
    background.alpha_composite(image)

    mask = Image.new('L', image.size, 0)
    ImageDraw.Draw(mask).ellipse(
        (0, 0, diameter - 1, diameter - 1), fill=255
    )
    background.putalpha(mask)

    return background


def get_font(size):

    for name in ('arialbd.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue

    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def build_collage(avatars, total):

    canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    show_bubble = total > 4
    shown = avatars[:3] if show_bubble else avatars[:4]
    slots = 4 if show_bubble else max(len(shown), 1)

    diameter, centers = LAYOUTS[slots]
    radius = diameter // 2

    for index, (cx, cy) in enumerate(centers):

        # Viền trắng ngăn cách các avatar
        draw.ellipse(
            (cx - radius - RING, cy - radius - RING,
             cx + radius + RING, cy + radius + RING),
            fill=(255, 255, 255, 255)
        )

        if index < len(shown):
            avatar = circle_image(member_image_path(shown[index]), diameter)
            canvas.alpha_composite(avatar, (cx - radius, cy - radius))
            continue

        # Ô cuối: tổng số thành viên
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=(232, 236, 243, 255)
        )

        text = str(total)
        font = get_font(int(diameter * (0.42 if len(text) <= 2 else 0.32)))
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)

        draw.text(
            (cx - (left + right) / 2, cy - (top + bottom) / 2),
            text,
            font=font,
            fill=(55, 65, 85, 255)
        )

    return canvas


def refresh_auto_avatar(cursor, conversation_id):
    """Tạo lại ảnh nhóm từ avatar thành viên. Bỏ qua nếu nhóm có ảnh riêng.
    Gọi bên trong transaction, người gọi tự commit."""

    if Image is None:
        print('Cần cài Pillow để tự ghép ảnh nhóm: pip install pillow')
        return

    try:
        cursor.execute(
            'SELECT avatar FROM conversations WHERE id = %s',
            (conversation_id,)
        )
        row = cursor.fetchone()
        old_avatar = row['avatar'] if row else None

        # Nhóm đã có ảnh do người dùng chọn: giữ nguyên
        if old_avatar and not old_avatar.startswith(AUTO_URL_PREFIX):
            return

        cursor.execute(
            '''
            SELECT u.avatar
            FROM conversation_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.conversation_id = %s
            ORDER BY cm.joined_at ASC, cm.id ASC
            LIMIT 4
            ''',
            (conversation_id,)
        )
        avatars = [item['avatar'] for item in cursor.fetchall()]

        cursor.execute(
            '''
            SELECT COUNT(*) AS total
            FROM conversation_members
            WHERE conversation_id = %s
            ''',
            (conversation_id,)
        )
        total = cursor.fetchone()['total']

        if not avatars:
            return

        collage = build_collage(avatars, total)

        os.makedirs(GROUP_FOLDER, exist_ok=True)

        filename = f'{AUTO_PREFIX}{conversation_id}_{uuid.uuid4().hex[:8]}.png'
        collage.save(GROUP_FOLDER / filename)

        cursor.execute(
            'UPDATE conversations SET avatar = %s WHERE id = %s',
            (f'/uploads/group_avatars/{filename}', conversation_id)
        )

        # Xóa ảnh tự ghép cũ
        if old_avatar:
            old_path = GROUP_FOLDER / os.path.basename(old_avatar)

            if old_path.exists():
                os.remove(old_path)

    except Exception as error:
        print('Lỗi tạo ảnh nhóm tự động:', error)


def rebuild_all():
    """Tạo ảnh cho các nhóm cũ chưa có ảnh (chạy một lần)."""

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM conversations WHERE type = 'group' AND avatar IS NULL"
    )

    for row in cursor.fetchall():
        refresh_auto_avatar(cursor, row['id'])

    db.commit()
    cursor.close()
    db.close()