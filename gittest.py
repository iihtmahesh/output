import subprocess

try:
    result = subprocess.run(["git", "--version"], check=True, text=True, capture_output=True)
    print("Git is accessible:", result.stdout)
except FileNotFoundError as e:
    print("Git is not accessible. Ensure it is installed and in PATH.")
