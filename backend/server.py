from flask import Flask, request, jsonify
from flask_cors import CORS
import os, datetime

app = Flask(__name__)
CORS(app)  # 允许跨域，解决浏览器从 Netlify 调 Render 时的 CORS 问题

SAVE_DIR = "saved_results"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route("/")
def home():
    return "✅ Backend is running! POST /upload to save notebooks."

@app.route("/upload", methods=["POST"])
def upload_notebook():
    data = request.get_json(force=True, silent=True) or {}
    participant = data.get("participant_id", "unknown")
    nb_json = data.get("notebook_json", "")

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{participant}_{ts}.ipynb"
    path = os.path.join(SAVE_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(nb_json)

    print(f"✅ saved: {path}")
    return jsonify({"status": "ok", "file": filename})
