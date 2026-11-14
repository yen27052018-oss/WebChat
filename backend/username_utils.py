import unicodedata


def normalize_username(name):
    name = unicodedata.normalize('NFC', name or '')
    return ' '.join(name.split())


def same_username(a, b):
    return normalize_username(a).lower() == normalize_username(b).lower()


def find_user_by_username(cursor, username, exclude_userid=None):

    username = normalize_username(username)
    cursor.execute(
        '''
        SELECT id, userid, username, password, avatar
        FROM users
        WHERE username = %s
        ''',
        (username,)
    )

    for row in cursor.fetchall():

        if exclude_userid and row['userid'] == exclude_userid:
            continue

        if same_username(row['username'], username):
            return row

    return None