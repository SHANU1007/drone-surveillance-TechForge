import cv2
import socket
import pickle
import struct
import time

HOST = '10.74.180.173'   # Pi IP
PORT = 9999

# Socket 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
print("✅ Connected to Pi")

data = b""
payload_size = struct.calcsize("Q")

# OpenCV Window
cv2.namedWindow("LIVE", cv2.WINDOW_NORMAL)

try:
    while True:
        # Receive message size?
        while len(data) < payload_size:
            packet = s.recv(4096)
            if not packet:
                raise ConnectionError("Disconnected")
            data += packet

        packed_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_size)[0]

        #Receive frame
        while len(data) < msg_size:
            data += s.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)

        #Show frame
        cv2.imshow("LIVE", frame)

        # for window refresh
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.01)  

except Exception as e:
    print("❌ Error:", e)

finally:
    s.close()
    cv2.destroyAllWindows()
    print("🔴 Client closed")
