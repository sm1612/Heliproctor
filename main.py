import cv2
import mediapipe as mp

# Initialize MediaPipe Face Detection and Face Mesh
mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Initialize webcam
cap = cv2.VideoCapture(0)

# Create a dictionary to store unique IDs for each detected face
face_ids = {}
next_id = 1

# Initialize MediaPipe Face Detection
with mp_face_detection.FaceDetection(
    min_detection_confidence=0.5) as face_detection:

    # Initialize MediaPipe Face Mesh for full face and eye tracking
    with mp_face_mesh.FaceMesh(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR image to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Perform face detection
            results_face = face_detection.process(frame_rgb)

            # Perform face mesh detection for full face and eye tracking
            results_mesh = face_mesh.process(frame_rgb)

            if results_face.detections:
                for i, detection in enumerate(results_face.detections):
                    bboxC = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                                int(bboxC.width * iw), int(bboxC.height * ih)

                    # Generate a unique ID for this face
                    if i not in face_ids:
                        face_ids[i] = next_id
                        next_id += 1

                    # Display the ID and bounding box around the face
                    cv2.putText(frame, f"ID: {face_ids[i]}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if results_mesh and results_mesh.multi_face_landmarks:
                for face_landmarks in results_mesh.multi_face_landmarks:
                    for id, lm in enumerate(face_landmarks.landmark):
                        ih, iw, _ = frame.shape
                        x, y = int(lm.x * iw), int(lm.y * ih)
                        cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)

            cv2.imshow('Face and Eye Tracking', frame)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

cap.release()
cv2.destroyAllWindows()
