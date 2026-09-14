import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.routes.register import register_bp
from backend.routes.login import login_bp
from backend.routes.profile import profile_bp

app = Flask(__name__)

CORS(app)

app.register_blueprint(register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(profile_bp)


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
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )