import os

from flask import Flask, request, send_from_directory, abort
from flask_cors import CORS
from backend.extensions import socketio

from backend.routes.register import register_bp
from backend.routes.login import login_bp
from backend.routes.profile import profile_bp
from backend.routes.friend import friend_bp
from backend.routes.message import message_bp

from backend.socket import chatSocket

app = Flask(__name__)

CORS(app)

socketio.init_app(
    app,
    cors_allowed_origins='*'
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
@app.route(
    '/uploads/<path:filename>'
)
def uploaded_file(filename):

    upload_folder = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        'WEB_Chat_Uploads'
    )

    return send_from_directory(
        upload_folder,
        filename
    )


# =========================
# FRONTEND (để dùng 1 tunnel ngrok)
# =========================

FRONTEND_DIR = os.path.dirname(os.path.dirname(__file__))  # thư mục WEB_Chat

# Chỉ cho phép các trang và thư mục giao diện
ALLOWED_PAGES = {'login.html', 'signup.html', 'chatApp.html'}
ALLOWED_FOLDERS = ('frontend/', 'assests/')


@app.route('/app/<path:filename>')
def frontend_file(filename):

    if filename not in ALLOWED_PAGES and not filename.startswith(ALLOWED_FOLDERS):
        abort(404)

    return send_from_directory(FRONTEND_DIR, filename)

# =========================
# RUN
# =========================

if __name__ == '__main__':

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
    )