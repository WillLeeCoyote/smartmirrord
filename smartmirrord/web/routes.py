from flask import Flask, render_template, request, jsonify
from smartmirrord.services.ir_service import IRService

web_remote = Flask(__name__, template_folder='templates', static_folder='static')
ir_service = IRService()

@web_remote.route("/")
def index():
    buttons = ir_service.list_commands()
    return render_template("index.html", commands=buttons)

@web_remote.route("/send_command", methods=["POST"])
def send_command():
    data = request.get_json()
    cmd = data.get("command")
    try:
        ir_service.send_command(cmd)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except IOError:
        return jsonify({"status": "error", "message": "Unknown error"}), 500

    return jsonify({"status": "ok"})
