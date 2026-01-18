from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
import serial, threading, time
import cv2
from ultralytics import YOLO

app = Flask(__name__)
CORS(app)

# ================== SERIAL CONFIG ==================
SERIAL_PORT = "COM5"
BAUD_RATE = 115200

ser = None
while ser is None:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ Connected to ESP on {SERIAL_PORT}", flush=True)
    except Exception as e:
        print("⚠ ESP not connected, retrying...", e, flush=True)
        time.sleep(1)

# ================== GLOBAL STATE ==================
alert_msg = "Normal"          # ONLY ESP controls this
human_detected = False        # YOLO only updates this

# ================== SERIAL READ THREAD ==================
def serial_read_thread():
    global alert_msg
    while True:
        try:
            if ser and ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    print("📥 ESP:", line)

                    if "ALERT" in line:
                        alert_msg = "ALERT"

                    elif "CLEAR" in line or "Normal" in line:
                        alert_msg = "Normal"

        except Exception as e:
            print("❌ Serial error:", e)

        time.sleep(0.1)

threading.Thread(target=serial_read_thread, daemon=True).start()

# ================== YOLO + CAMERA ==================
model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)   # Laptop camera

def generate_frames():
    global human_detected

    while True:
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, conf=0.5, classes=[0])  # person
        human_detected = False

        for r in results:
            if len(r.boxes) > 0:
                human_detected = True
            frame = r.plot()

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

# ================== ROUTES ==================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/status")
def status():
    return jsonify({
        "alert": alert_msg,
        "human": human_detected
    })

@app.route("/clear", methods=["POST"])
def clear_alert():
    global alert_msg
    alert_msg = "Normal"
    print("⚡ Alert cleared manually")
    return jsonify({"success": True})

@app.route("/takeoff", methods=["POST"])
def takeoff():
    try:
        ser.write(b"TAKEOFF\n")
        print("🚁 TAKEOFF sent")
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

@app.route("/return", methods=["POST"])
def return_home():
    try:
        ser.write(b"RETURN\n")
        print("🔙 RETURN sent")
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Drone Security Dashboard Started")
    app.run(host="0.0.0.0", port=5000, debug=False)
