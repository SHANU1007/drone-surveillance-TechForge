import cv2
import socket
import pickle
import struct

# Pi IP and port
HOST = '10.74.180.173'  
PORT = 9999

# Connection to Pi
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
print("Connected to Pi at", HOST)

data = b""
payload_size = struct.calcsize("Q")

# Load Haar Cascade for full body detection
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_fullbody.xml")

while True:
    # Receive frame size
    while len(data) < payload_size:
        packet = s.recv(4*1024)
        if not packet: break
        data += packet

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    # Receive frame data
    while len(data) < msg_size:
        data += s.recv(4*1024)
    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Deserialize frame
    frame = pickle.loads(frame_data)
    print("Frame received:", frame.shape)  

    # Convert to grayscale(Haar detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    humans = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))

    # rect shape around detected humans
    for (x, y, w, h) in humans:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Show frame
    cv2.imshow("LIVE Human Detection", frame)

    #quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
s.close()
print("Connection closed")
