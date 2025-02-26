import subprocess
from tools import query_neo4j_graph
import shutil
import psutil
import time
import os

def start_neo4j(db_path: str, db_name: str = "neo4j") -> bool:
    try:
        subprocess.run([f"{db_path}\\bin\\neo4j.bat", "start"], check=True)
        time.sleep(20)
    except Exception as e:
        print(f"Error starting Neo4j: {e}")
        return False
    while True:
        try:
            query_neo4j_graph(f"START DATABASE {db_name}")
            break
        except Exception as e:
            print(f"Neo4j not ready yet: {e}")
            time.sleep(5)
    print("Neo4j started successfully.")
    return True

def stop_neo4j(db_path: str = "neo4j") -> bool:
    """Stops Neo4j console mode and ensures all related processes are terminated."""
    subprocess.run([f"{db_path}\\bin\\neo4j.bat", "stop"], check=True)
    return True

def images_backup(backup_dir: str, images_dir: str) -> bool:
    try:
        shutil.copytree(images_dir, backup_dir+'\images', dirs_exist_ok=True)
    except shutil.Error as e:
        print(f"Error during images backup: {e}")
        return False
    print(f"Images backup completed: {backup_dir}\\images")
    return True

def neo4jdb_backup(backup_dir: str, db_name: str, db_path: str) -> bool:
    backup_command = [
        f"{db_path}\\bin\\neo4j-admin.bat",
        "database",
        "dump",
        db_name,
        "--to-path",
        backup_dir
    ]

    try:
        stop_neo4j(db_path)
        subprocess.run(backup_command, check=True)
        start_neo4j(db_path)
    except subprocess.CalledProcessError as e:
        print(f"Error during neo4j db backup: {e}")
        return False
    print(f"Backup completed: {backup_dir}\\{db_name}.dump")
    return True

def restore(backup_dir: str):
    db_name = "neo4j"
    db_path = r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae"
    images_dir = r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\images"
    try:
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
            print(f"🗑️ Deleted old images directory: {images_dir}")
        shutil.copytree(os.path.join(backup_dir, 'images'), images_dir)
    except shutil.Error as e:
        print(f"Error during images restoration: {e}")
        return
    print(f"Images restoration completed: {images_dir}")

    load_command = [
        f"{db_path}\\bin\\neo4j-admin.bat",
        "database",
        "load",
        db_name,
        "--from-path",
        backup_dir,
        "--overwrite-destination=true"
    ]
    stop_neo4j(db_path)
    try:
        subprocess.run(load_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during neo4j db restoration: {e}")
        return
    start_neo4j(db_path, db_name)
    print(f"Database {db_name} restored successfully from {backup_dir}/{db_name}.dump.")
    

def backup():
    images_dir = r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\images"
    backup_dir = os.path.join(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups", time.strftime("%Y%m%d-%H%M%S"))

    db_name = "neo4j"
    db_path = r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae"
    stop_neo4j(db_path)
    
    os.makedirs(backup_dir, exist_ok=True)
    
    if images_backup(backup_dir, images_dir) and neo4jdb_backup(backup_dir, db_name, db_path):
        print("Backup completed successfully")
        start_neo4j(db_path)
        
        backup_count = len([name for name in os.listdir(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups")])

        if backup_count > 5:
            backups = sorted([name for name in os.listdir(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups")])
            oldest_backup = os.path.join(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups", backups[0])
            shutil.rmtree(oldest_backup)
            print(f"Deleted oldest backup folder: {oldest_backup}")
        return
    else:
        raise Exception("Backup failed")

if __name__ == "__main__":
    backup()