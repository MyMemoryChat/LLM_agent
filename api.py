from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import AnswerAgent, PictureAgent, UpdateAgent
import os
import base64
import re

app = Flask(__name__)
CORS(app)

image_folder = "./images"
agents = [AnswerAgent(), UpdateAgent(), PictureAgent()]

@app.route("/", methods=["POST"])
def receive_data():
    text = request.json.get("text")
    image_base64 = request.json.get("image")
    
    if image_base64 is None:
        print('Image not found in request.json')
        try:
            agents[1](message=text, verbose=True)
        except Exception as e:
            print(f"Failed to process text: {e}")
    else:
        print('Image found in request.json')
        try:
            i=0
            while os.path.exists(f"{image_folder}/image{i}.jpg"):
                i+=1
            image_path = f"{image_folder}/image{i}.jpg"

            image_base64 = re.sub(r"^data:image/\w+;base64,", "", image_base64)
            image_data = base64.b64decode(image_base64)
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)
            agents[2](image_path=image_path, description=text, verbose=True)
        except Exception as e:
            print(f"Failed to process image: {e}")
             
    try:
        answer = agents[0](message=text, verbose=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(answer)

@app.route("/reset", methods=["GET"])
def reset_agents():
    for agent in agents:
        agent.reset()
    return jsonify({
        "message": "All agents reset."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5124, debug=True)