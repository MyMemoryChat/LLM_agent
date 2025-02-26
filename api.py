from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from backup import backup
import threading
from flask_cors import CORS
from agent import AnswerAgent, UpdateAgent
from tools import query_neo4j_graph
from backup import start_neo4j, stop_neo4j
import os
import base64
import re
import time
import atexit

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": ["http://192.168.2.34:4173", "http://localhost:4173", "http://192.168.27.65:4173"]
}})

# Close the neo4j console when closing the app
def on_shutdown():
    print("🛑 Flask app is shutting down!")
    stop_neo4j(r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae")
atexit.register(on_shutdown) 

@app.after_request
def after_request(response):
    print(f"Request from: {request.origin}")
    return response

# Make a backup every 30 minutes and locks the API during it
backup_lock = threading.Lock()
def backup_wrapper():
    """Wraps the backup function with a lock to prevent API access during backup."""
    with backup_lock:
        print("🔒 Backup started, API is locked...")
        backup()
        print("✅ Backup completed, API is unlocked.")

scheduler = BackgroundScheduler()
scheduler.add_job(backup_wrapper, 'interval', minutes=30) 
scheduler.start()

image_folder = "./images"
agents = [AnswerAgent(), UpdateAgent()]

def save_image(image_base64):
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
        return ""
    return image_path

def update_graph(message:str, image_path:str=""):
    agents[1](message=message, image_path=image_path, verbose=True)

# Lock to prevent concurrent generations
generate_lock = threading.Lock()

@app.route("/generate", methods=["POST"])
def generate_answer():
    if not generate_lock.acquire(blocking=False):  # Try to acquire lock, if unavailable return busy message
        return jsonify({"error": "Server is busy processing another request"}), 429
    try:
        start_time = time.time()
        text = request.json.get("text")
        image_base64 = request.json.get("image")
        if image_base64 is not None:
            image_path = save_image(image_base64)
        else:
            image_path = ""
            
        def thread_task(text, image_path):
            try:
                update_graph(text, image_path)  
            finally:
                generate_lock.release()
        thread = threading.Thread(target=thread_task, args=(text, image_path), daemon=True)
        answer = ""
        while not (isinstance(answer, dict) and  "message" in answer and isinstance(answer["message"], str) and "images" in answer and isinstance(answer["images"], list) and all(isinstance(img, str) for img in answer["images"])):
            answer = agents[0](message=text, image_path=image_path, verbose=True)
        thread.start()
        print(f"Done in: {time.time() - start_time}")
        return jsonify(answer)
    except Exception as e:
        generate_lock.release() 
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route("/reset", methods=["GET"])
def reset_agents():
    global agents
    agents = [AnswerAgent(), UpdateAgent()]
    return jsonify({
        "message": "All agents reset."
    })
    
@app.route("/images/<image_name>", methods=["GET"])
def get_image(image_name):
    image_path= "./images/" + image_name
    with open(image_path, "rb") as image_file:
        image_file = "data:image/jpeg;base64,"+base64.b64encode(image_file.read()).decode("utf-8")
        
    search_result = query_neo4j_graph(f"MATCH (i:Image) WHERE i.image_path = '{image_path}' RETURN i.name as name, i.date as date, i.additional_infos as additional_infos")[0]
    search_result["image_file"] = image_file    
    return jsonify(search_result)

if __name__ == "__main__":
    print("🚀 Flask app has started!")
    start_neo4j(r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae", "neo4j")
    app.run(host="0.0.0.0", port=5124, use_reloader=False, debug=True)