from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/trigger', methods=['POST'])
def trigger():
    print("Trigger received! Launching .exe...")
    subprocess.Popen([r"D:\Steam\steamapps\common\The Finals\start_protected_game.exe"])
    subprocess.Popen([r"D:\Steam\steamapps\common\The Finals\Discovery.exe"])
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
