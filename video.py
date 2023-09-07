import cv2
import mediapipe as mp

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Load the video file
video_capture = cv2.VideoCapture('meeting.mp4')

# Create a dictionary to store unique IDs for each detected face
face_ids = {}
next_id = 1

with mp_face_detection.FaceDetection(
    min_detection_confidence=0.5) as face_detection:

    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break

        # Convert BGR image to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Perform face detection
        results = face_detection.process(frame_rgb)

        if results.detections:
            for i, detection in enumerate(results.detections):
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                             int(bboxC.width * iw), int(bboxC.height * ih)

                # Generate a unique ID for this face
                if i not in face_ids:
                    face_ids[i] = next_id
                    next_id += 1

                # Display the ID and bounding box around the face
                cv2.putText(frame, f"ID: {face_ids[i]}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the frame
        cv2.imshow('Meeting Video', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release video capture and close all windows
video_capture.release()
cv2.destroyAllWindows()
