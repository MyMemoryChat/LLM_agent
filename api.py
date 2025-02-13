from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import AnswerAgent, PictureAgent, UpdateAgent
import os
import base64
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": ["http://192.168.2.34:4173", "http://localhost:4173"]
}})

@app.after_request
def after_request(response):
    print(f"Request from: {request.origin}")
    return response

image_folder = "./images"
agents = [AnswerAgent(), UpdateAgent()]

@app.route("/", methods=["POST"])
def receive_data():
    text = request.json.get("text")
    image_base64 = request.json.get("image")
    if image_base64 is not None:
        try:
            i=0
            while os.path.exists(f"{image_folder}/image{i}.jpg"):
                i+=1
            image_path = f"{image_folder}/image{i}.jpg"

            image_base64 = re.sub(r"^data:image/\w+;base64,", "", image_base64)
            image_data = base64.b64decode(image_base64)
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)
        except Exception as e:
            print(f"Failed to process image: {e}")
    else:
        image_path = None
    agents[1](message=text, image_path=image_path, verbose=True)
    
    try:
        answer = agents[0](message=text, verbose=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(answer)

@app.route("/reset", methods=["GET"])
def reset_agents():
    global agents
    agents = [AnswerAgent(), UpdateAgent()]
    return jsonify({
        "message": "All agents reset."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5124, debug=True)