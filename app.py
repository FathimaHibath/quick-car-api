from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS
import json
import os


# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Initialize Firebase
# Load Firebase credentials from environment variable
firebase_key_str = os.environ.get("FIREBASE_KEY")

if firebase_key_str is None:
    raise ValueError("FIREBASE_KEY environment variable not set")

firebase_key_dict = json.loads(firebase_key_str)
cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Fetch problems from Firestore
def fetch_problems_from_firebase():
    problems_db = []
    docs = db.collection("problems_db").stream()
    for doc in docs:
        problems_db.append(doc.to_dict())  # Convert Firestore document to dictionary
    return problems_db

# NLP Matching Function
def find_solution(user_input):
    problems_db = fetch_problems_from_firebase()  # Fetch problems dynamically

    if not problems_db:  # If database is empty
        return "Database is empty. Please add problems."

    problem_texts = [p["problem"] for p in problems_db]

    vectorizer = TfidfVectorizer()
    problem_vectors = vectorizer.fit_transform(problem_texts)

    user_vector = vectorizer.transform([user_input])
    similarities = cosine_similarity(user_vector, problem_vectors)

    best_match_index = np.argmax(similarities)
    best_match_score = similarities[0, best_match_index]

    if best_match_score > 0.3:
        return problems_db[best_match_index]["solution"]
    else:
        return "No exact match found. Please check with a mechanic."

@app.route('/')
def home():
    return "Flask server is running!"

# API Endpoint
@app.route('/get_solution', methods=['POST'])
def get_solution():
    data = request.get_json()
    print("Received data:", data) 
    problem = data.get("problem","")
    if not problem:
        return jsonify({"error": "No problem description provided"}), 400
    solution=find_solution(problem)
    return jsonify({"solution": solution})


# Send Message API
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    username = data.get("username", "Guest")
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    print(f"Received Message -> Username: {username}, Message: {message}")

    try:
        db.collection("community_chat").add({
            "username": username,
            "message": message,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print("Message successfully stored in Firestore!")
        return jsonify({"success": True, "message": "Message sent successfully!"})
    except Exception as e:
        print(f"Error storing message: {e}")
        return jsonify({"error": str(e)}), 500


# Get Messages API

@app.route('/get_messages', methods=['GET'])
def get_messages():
    messages_ref = db.collection("community_chat").order_by("timestamp").stream()
    messages = [{"username": msg.to_dict().get("username", "Unknown"), 
                 "message": msg.to_dict().get("message", ""),
                 "timestamp": msg.to_dict().get("timestamp", "")} for msg in messages_ref]

    return jsonify({"messages": messages})



# Run Flask Server
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

