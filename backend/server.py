from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__)
SAVE_DIR = "saved_results"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route("/")
def home():
    return "✅ Backend is running! POST /upload to save notebooks.<br>Visit /list to see saved files."

@app.route("/upload", methods=["POST"])
def upload_notebook():
    data = request.json
    pid = data.get("participant_id", "unknown")
    content = data.get("notebook_json", "")
    filename = os.path.join(SAVE_DIR, f"{pid}.ipynb")
    with open(filename, "w") as f:
        f.write(content)
    print(f"✅ Saved: {filename}")
    return jsonify({"status": "success"})

@app.route("/list")
def list_files():
    files = os.listdir(SAVE_DIR)
    links = [f'<li><a href="/saved_results/{f}">{f}</a></li>' for f in files]
    return f"<h2>Saved notebooks:</h2><ul>{''.join(links)}</ul>"

@app.route("/saved_results/<path:filename>")
def serve_file(filename):
    return send_from_directory(SAVE_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
