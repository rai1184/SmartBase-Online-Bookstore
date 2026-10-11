from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables Cross-Origin Resource Sharing for React frontend

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "message": "SmartBase Backend is running!"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)