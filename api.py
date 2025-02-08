from flask import Flask, request, jsonify
from agent import AnswerAgent, PictureAgent, UpdateAgent

app = Flask(__name__)

image_folder = "./images"
agents = [AnswerAgent(), UpdateAgent(), PictureAgent()]

@app.route("/", methods=["GET"])
def home():
    return "Server is running!"

@app.route("/text", methods=["POST"])
def generate_answer_from_text_only():
    data = request.json
    text = data["text"]
    agents[1](message=text)
    answer = agents[0](message=text)
    return jsonify(answer)

@app.route("/image", methods=["POST"])
def receive_data():
    if "image" not in request.files:
        return jsonify({"error": "No image part in the request"}), 400
    
    image = request.files["image"]
    text = request.form.get("text", "")
    
    try:
        image_path = f"{image_folder}/{image.filename}"
        image.save(image_path)
        agents[2](image_path=image_path, description=text)
        message = "Image saved and added to the database."
    except Exception as e:
        message = f"Failed to save image: {e}"
        
    answer = agents[0](message=text)
    
    return jsonify({
        "message": message,
        "answer": answer
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5124, debug=True)