import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

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

@socketio.on('connect')
def handle_connect():
    print('Có client vừa kết nối Socket.IO')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client đã ngắt kết nối Socket.IO')

app.register_blueprint(register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(friend_bp)
app.register_blueprint(message_bp)


@app.route('/')
def home():
    return 'CHAT & WATCH Backend đang hoạt động!'


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    upload_folder = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'uploads'
    )

    return send_from_directory(
        upload_folder,
        filename
    )


if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )