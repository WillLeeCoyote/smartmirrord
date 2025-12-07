from flask import Flask, render_template, request, jsonify
from smartmirrord.hardware.ir_emulator import IREmulator
from smartmirrord.hardware.ir_codes import CODES

ir_emulator = IREmulator()
buttons = CODES.keys()
web_remote = Flask(__name__, template_folder='templates', static_folder='static')

@web_remote.route("/")
def index():
    return render_template("index.html", commands=buttons)

@web_remote.route("/send_command", methods=["POST"])
def send_command():
    data = request.get_json()
    cmd = data.get("command")
    try:
        ir_emulator.send(cmd)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except IOError as e:
        return jsonify({"status": "error", "message": "Unknown error"}), 500

    return jsonify({"status": "ok"})
