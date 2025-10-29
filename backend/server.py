# from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, base64, datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------------
# 📁 文件保存路径
# ---------------------------------------------------------------
SAVE_DIR = "saved_results"
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------------------------------------------------------
# 🔐 Google Drive 授权（支持环境变量 + 本地调试）
# ---------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
drive_service = None

# ✅ 读取环境变量
service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

try:
    if service_account_json:
        # Render 环境中，JSON 存在环境变量里
        service_account_info = json.loads(service_account_json)
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
        drive_service = build("drive", "v3", credentials=creds)
        print("✅ Google Drive client initialized from environment.")
    elif os.path.exists("buckaroo-476616-047503bd89c6.json"):
        # 本地调试时，从文件读取
        creds = service_account.Credentials.from_service_account_file(
            "buckaroo-476616-047503bd89c6.json", scopes=SCOPES
        )
        drive_service = build("drive", "v3", credentials=creds)
        print("✅ Google Drive client initialized from local file.")
    else:
        print("⚠️ No credentials found, skipping Drive upload.")
except Exception as e:
    print("❌ Failed to initialize Google Drive:", e)

# ---------------------------------------------------------------
# 🔼 上传文件到 Google Drive
# ---------------------------------------------------------------
def upload_to_drive(local_path, filename):
    """上传文件到指定 Google Drive 文件夹"""
    if not drive_service:
        print("⚠️ Drive service not initialized.")
        return None, None
    if not FOLDER_ID:
        print("⚠️ Missing GOOGLE_DRIVE_FOLDER_ID.")
        return None, None
    try:
        file_metadata = {"name": filename, "parents": [FOLDER_ID]}
        media = MediaFileUpload(local_path, resumable=True)
        uploaded = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )
        print(f"✅ Uploaded to Google Drive: {uploaded.get('webViewLink')}")
        return uploaded.get("id"), uploaded.get("webViewLink")
    except Exception as e:
        print("❌ Error uploading to Google Drive:", e)
        return None, None

# ---------------------------------------------------------------
# 🌐 Flask 路由
# ---------------------------------------------------------------
@app.route("/")
def home():
    return "✅ Backend is running! Use /upload or /upload_csv."

@app.route("/upload", methods=["POST"])
def upload_notebook():
    """上传 notebook 文件"""
    data = request.get_json()
    pid = data.get("participant_id", "unknown")
    notebook_json = data.get("notebook_json", "")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{pid}_{timestamp}.ipynb"

    local_path = os.path.join(SAVE_DIR, filename)
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(notebook_json)

    drive_id, web_link = upload_to_drive(local_path, filename)
    print(f"✅ Notebook saved locally: {local_path}")

    return jsonify({
        "status": "success",
        "local_filename": filename,
        "drive_id": drive_id,
        "drive_link": web_link
    })

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    """上传 CSV 文件"""
    data = request.get_json()
    pid = data.get("participant_id", "unknown")
    filename = data.get("filename")
    content_b64 = data.get("content_b64")

    if not filename or not content_b64:
        return jsonify({"status": "error", "message": "Missing filename or content"}), 400

    try:
        csv_bytes = base64.b64decode(content_b64)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid base64: {e}"}), 400

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{pid}_{timestamp}_{filename}"
    local_path = os.path.join(SAVE_DIR, save_name)
    with open(local_path, "wb") as f:
        f.write(csv_bytes)

    drive_id, web_link = upload_to_drive(local_path, save_name)
    print(f"✅ CSV saved locally: {local_path}")

    return jsonify({
        "status": "success",
        "local_filename": save_name,
        "drive_id": drive_id,
        "drive_link": web_link
    })

@app.route("/list")
def list_files():
    files = sorted(os.listdir(SAVE_DIR))
    links = [f'<li><a href="/saved_results/{f}">{f}</a></li>' for f in files]
    return f"<h2>Saved files:</h2><ul>{''.join(links)}</ul>"

@app.route("/saved_results/<path:filename>")
def serve_file(filename):
    return send_from_directory(SAVE_DIR, filename, as_attachment=True)

# ---------------------------------------------------------------
# 🚀 启动
# ---------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
