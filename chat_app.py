from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
import datetime

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Initialize Firebase
cred = credentials.Certificate("c:/Users/fathi/AndroidStudioProjects/fixmyrideapp/hi/firebase_key.json")  # Load Firebase credentials
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore Collection Name
CHAT_COLLECTION = "community_chat"

@app.route('/')
def home():
    return "Flask server is running!"

# Route to Post a Message
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    username = data.get("username", "Anonymous")  # Default username if not provided
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Store message in Firestore
    chat_data = {
        "username": username,
        "message": message,
        "timestamp": datetime.datetime.utcnow()
    }
    db.collection(CHAT_COLLECTION).add(chat_data)
    
    return jsonify({"success": True, "message": "Message sent successfully!"})

# Route to Get All Messages
@app.route('/get_messages', methods=['GET'])
def get_messages():
    messages = []
    docs = db.collection(CHAT_COLLECTION).order_by("timestamp").stream()

    for doc in docs:
        msg = doc.to_dict()
        msg["timestamp"] = msg["timestamp"].isoformat()  # Convert timestamp to readable format
        messages.append(msg)

    return jsonify({"messages": messages})

# Run Flask Server
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
