import subprocess
import shutil
import time
import os

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
        subprocess.run(backup_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during neo4j db backup: {e}")
        return False
    print(f"Backup completed: {backup_dir}\\{db_name}.dump")
    return True

def backup():
    images_dir = r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\images"
    backup_dir = os.path.join(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups", time.strftime("%Y%m%d-%H%M%S"))
    db_name = "neo4j"  # Change this if your database has a different name
    db_path = r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae"

    images_backup(backup_dir, images_dir)
    
    if images_backup(backup_dir, images_dir) and neo4jdb_backup(backup_dir, db_name, db_path):
        print("Backup completed successfully")
        return
    else:
        raise Exception("Backup failed")

if __name__ == "__main__":
    backup()