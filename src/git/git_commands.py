import subprocess
import os

def run_git_command(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return ""

def is_git_repo(path: str) -> bool:
    """Check if the given path is a git repository."""
    command = "git rev-parse --is-inside-work-tree"
    original_dir = os.getcwd()
    try:
        os.chdir(path)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False
    finally:
        os.chdir(original_dir) 