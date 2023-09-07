import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Initialize webcam
cap = cv2.VideoCapture(0)

# Create a dictionary to store registered users and their attendance times
registered_users = {}
current_user = None
start_time = None

with mp_face_detection.FaceDetection(
    min_detection_confidence=0.5) as face_detection:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        # Convert BGR image to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Perform face detection
        results = face_detection.process(frame_rgb)

        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                             int(bboxC.width * iw), int(bboxC.height * ih)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # If a user is registered, display their name above the bounding box
                if current_user:
                    cv2.putText(frame, current_user, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Check if a new user needs to be registered
                if current_user is None:
                    cv2.putText(frame, "Register your name and press 'Enter'", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imshow('Attendance System', frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == 13:  # Enter key is pressed to register a new user
            if current_user is None:
                current_user = input("Enter your name: ")
                start_time = time.time()
                registered_users[current_user] = 0
                print(f"Registered {current_user} for attendance.")
        elif key == 27:  # Esc key is pressed to unregister the current user
            if current_user:
                end_time = time.time()
                registered_users[current_user] += end_time - start_time
                print(f"{current_user}'s attendance duration: {registered_users[current_user]:.2f} seconds")
                current_user = None

cap.release()
cv2.destroyAllWindows()

# Print the final attendance record
print("\nAttendance Record:")
for user, duration in registered_users.items():
    print(f"{user}: {duration:.2f} seconds")