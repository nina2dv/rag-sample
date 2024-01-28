from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import os
import re
import util

ChatBot = util.ChatBot()
namespace = "testing"
# FLASK
app = Flask(__name__)
CORS(app, resources={r"/query": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})

@app.route("/query", methods=["POST"], strict_slashes=False)
@cross_origin() 
def llm():
    # return jsonify({'message': 'Test response'}) # For testing
   
    # Extract the token from the Authorization header
    token = request.headers.get('Authorization')
    # print(token)
    
    # Check if the token is present
    if not token:
        return jsonify({'error': 'Authorization token is missing!'}), 403

    # Validate the token
    if token != os.environ.get("AUTH_TOKEN"):
        return jsonify({'error': 'Invalid token!'}), 403

    try:
        data = request.json
        query = data.get('query')
        # namespace = data.get('course').lower()
         
        answer = ChatBot.ask(query=query, namespace=namespace)

        return jsonify({
            "message": answer["message"],
            "docs": answer["docs"],
            "history": answer["history"],
        })
    except Exception as e:
        print(e)  # This will print the exception to the Flask console
        return jsonify({'error': str(e)}), 500
   

# Running app
if __name__ == '__main__':
    app.run(port=5000)