import os
import time
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, current_user, jwt_required, get_jwt_identity
from models import *
import cv2
import threading
from database import Session
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)
user_bp = Blueprint('user', __name__)

global video_recording
video_threads = {}
frames = []
frame_rate = 30.0
frame_size = (640, 480)
FPS = 30  # Frames per second
WIDTH = 640  # Video width in pixels
HEIGHT = 480  # Video height in pixels

def save_video_to_static(video_save_path, frames, frame_rate, frame_size):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_save_path, fourcc, frame_rate, frame_size)

    if not out.isOpened():
        return False

    for frame in frames:
        out.write(frame)

    out.release()
    return True

def record_video(admin_id, user_id, video_save_path, video_recording):
    try:
        # Initialize video capture using OpenCV
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_save_path, fourcc, FPS, (WIDTH, HEIGHT))

        while video_recording.get(user_id, False):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        # Release video capture and writer
        cap.release()
        out.release()

        # Create an entry in the VideoRecording table
        with Session() as session:
            new_video_recording = VideoRecording(
                user_id=user_id,
                admin_id=admin_id,
                file_path=video_save_path
            )
            session.add(new_video_recording)
            session.commit()

    except Exception as e:
        print('Error:', str(e))


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not username or not password or not role:
        return jsonify(message='Missing username, password, or role'), 400

    # Check if the role is valid
    if role not in ['user', 'admin']:
        return jsonify(message='Invalid role'), 400

    # Hash the password before storing it
    hashed_password = generate_password_hash(password)


    new_user = User(username=username, password_hash=hashed_password, role=role)
    with Session() as session:
        session.add(new_user)
        session.commit()
    if role == 'admin':
        new_admin = Admin(username=username, password_hash=hashed_password)
        with Session() as session:
            session.add(new_admin)
            session.commit()

    return jsonify(message='Registration successful'), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(message='Missing username or password'), 400

    # Check if the user exists
    with Session() as session:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify(message='User not found'), 404

        # Verify the password
        if check_password_hash(user.password_hash, password):
            # Create an access token
            access_token = create_access_token(identity=user.id, expires_delta=False)
            return jsonify(access_token=access_token, message='Login successful'), 200
        else:
            return jsonify(message='Invalid password'), 401


@admin_bp.route('/tests/create', methods=['POST'])
@jwt_required()
def create_test():
    try:
        data = request.json

        # Extract test information from JSON
        test_name = data.get('test_name')
        questions = data.get('questions')  # List of question objects

        # Ensure the admin_id matches the current user's ID
        admin_id = current_user.id

        session = Session()  # Create a session object

        try:
            # Create a new QuestionSet
            new_question_set = QuestionSet(name=test_name, admin_id=admin_id)
            session.add(new_question_set)
            session.flush()  # Flush the session to ensure new_question_set gets an ID
            new_question_set_id = new_question_set.id

            # Create questions and options associated with the question set
            for question_data in questions:
                question_text = question_data.get('text')
                options_data = question_data.get('options')  # List of option objects

                new_question = Question(text=question_text, question_set_id=new_question_set_id)
                session.add(new_question)
                session.flush()  # Flush the session to ensure new_question gets an ID

                # Create options for the question
                for option_data in options_data:
                    option_text = option_data.get('text')
                    is_correct = option_data.get('is_correct')
                    new_option = Option(text=option_text, is_correct=is_correct, question_id=new_question.id, created_at=func.now())
                    session.add(new_option)

            session.commit()
        except Exception as e:
            session.rollback()
            return jsonify({'message': 'Failed to create test', 'error': str(e)}), 500
        finally:
            session.close()  # Close the session

        return jsonify({'message': 'Test created successfully', 'test_id': new_question_set_id}), 201

    except Exception as e:
        return jsonify({'message': 'Failed to create test', 'error': str(e)}), 500


@admin_bp.route('/tests', methods=['GET'])
@jwt_required()
def list_tests():
    try:
        # Get the current admin's ID from the JWT token
        admin_id = get_jwt_identity()

        # Query the database to fetch the list of tests created by the admin
        with Session() as session:
            tests = session.query(QuestionSet).filter_by(admin_id=admin_id).all()

            # Convert the retrieved tests into a JSON-friendly format
            test_list = [{'test_id': test.id, 'test_name': test.name} for test in tests]

        return jsonify({'tests': test_list}), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch test list', 'error': str(e)}), 500

# Test details API
@admin_bp.route('/tests/<int:test_id>', methods=['GET'])
@jwt_required()
def test_details(test_id):
    try:
        # Get the current admin's ID from the JWT token
        admin_id = get_jwt_identity()

        # Query the database to fetch details of the specified test
        with Session() as session:
            test = session.query(QuestionSet).filter_by(admin_id=admin_id, id=test_id).first()

            if not test:
                return jsonify({'message': 'Test not found'}), 404

            # Retrieve questions associated with the test
            questions = session.query(Question).filter_by(question_set_id=test.id).all()

            # Convert the test and questions into a JSON-friendly format
            test_details = {
                'test_id': test.id,
                'test_name': test.name,
                'questions': [{'question_id': q.id, 'question_text': q.text} for q in questions]
            }

        return jsonify(test_details), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch test details', 'error': str(e)}), 500

@admin_bp.route('/videos', methods=['GET'])
@jwt_required()
def list_student_videos():
    try:
        admin_id = get_jwt_identity()
        with Session() as session:
            student_videos = session.query(VideoRecording).filter_by(admin_id=admin_id).all()

            video_links = [{'video_id': video.id, 'video_link': video.file_path} for video in student_videos]

        return jsonify(video_links), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch student videos', 'error': str(e)}), 500
    
# Student Video Details API
@admin_bp.route('/videos/<int:video_id>', methods=['GET'])
@jwt_required()
def student_video_details(video_id):
    try:
        admin_id = get_jwt_identity()

        with Session() as session:
            student_video = session.query(VideoRecording).filter_by(admin_id=admin_id, id=video_id).first()

            if not student_video:
                return jsonify({'message': 'Student video not found'}), 404

            # Query and include metrics received from the ML model for the video
            metrics = session.query(UserMetrics).filter_by(admin_id=admin_id, user_id=student_video.user_id).first()

            video_details = {
                'video_id': student_video.id,
                'video_link': student_video.file_path,
                'metrics': {
                    'recording_duration': metrics.recording_duration,
                    'eyes_off_screen_duration': metrics.eyes_off_screen_duration,
                    'lips_moving_duration': metrics.lips_moving_duration
                }
            }

        return jsonify(video_details), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch student video details', 'error': str(e)}), 500

@user_bp.route('/question-sets', methods=['GET'])
@jwt_required()
def list_question_sets():
    try:
        with Session() as session:
            question_sets = session.query(QuestionSet).all()
            question_sets_data = [{'question_set_id': qs.id, 'name': qs.name} for qs in question_sets]

            return jsonify(question_sets_data), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch question sets', 'error': str(e)}), 500

# Get Questions for Question Set API
@user_bp.route('/question-sets/<int:question_set_id>/questions', methods=['GET'])
@jwt_required()
def get_questions_for_question_set(question_set_id):
    try:
        with Session() as session:
            question_set = session.query(QuestionSet).filter_by(id=question_set_id).first()

            # Check if the question set exists
            if not question_set:
                return jsonify({'message': 'Question set not found'}), 404

            # Retrieve questions and options associated with the question set
            questions = session.query(Question).filter_by(question_set_id=question_set.id).all()

            # Serialize the questions and options to JSON
            questions_data = []
            for question in questions:
                options = [{'option_id': option.id, 'text': option.text, 'is_correct': option.is_correct} for option in question.options]
                question_data = {'question_id': question.id, 'text': question.text, 'options': options}
                questions_data.append(question_data)

            return jsonify(questions_data), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch questions for the question set', 'error': str(e)}), 500
    
@user_bp.route('/question-sets/<int:question_set_id>/submit-answers', methods=['POST'])
@jwt_required()
def submit_answers(question_set_id):
    try:
        user_id = get_jwt_identity()
        data = request.json
        answers = data.get('answers')

        if not answers:
            return jsonify(message='Missing answers'), 400

        total_marks = 0.0  # Initialize total marks

        # Signal the recording thread to stop (if needed)
        # video_recording[user_id] = False

        with Session() as session:
            # Loop through the submitted answers
            for answer_data in answers:
                question_id = answer_data.get('question_id')
                option_id = answer_data.get('option_id')

                if not question_id or not option_id:
                    return jsonify(message='Missing question_id or option_id'), 400

                # Validate that the question exists and belongs to the specified question set
                question = session.query(Question).filter_by(id=question_id, question_set_id=question_set_id).first()
                if not question:
                    return jsonify(message=f'Question {question_id} not found in the specified question set'), 400

                # Validate that the option exists and belongs to the specified question
                option = session.query(Option).filter_by(id=option_id, question_id=question_id).first()
                if not option:
                    return jsonify(message=f'Option {option_id} not found for the question'), 400

                # Calculate and record the user's answer and marks obtained
                is_correct = option.is_correct
                marks_obtained = 1.0 if is_correct else 0.0
                total_marks += marks_obtained

                user_answer = UserAnswer(
                    user_id=user_id,
                    question_id=question_id,
                    option_id=option_id,
                    is_correct=is_correct,
                    marks_obtained=marks_obtained
                )
                session.add(user_answer)

            # Stop video recording (if needed)
            # video_thread = video_threads.get(user_id)
            # if video_thread:
            #     video_thread.join()

            # Save the recorded video to the static folder
            video_save_path = f'static/{user_id}_test_{question_set_id}.avi'  # Set the video save path
            save_video_to_static(video_save_path, frames, frame_rate, frame_size)

            # Remove the video recording status entry for the user (if needed)
            # del video_recording[user_id]

            session.commit()

        return jsonify(message='Answers submitted successfully', total_marks=total_marks), 200

    except Exception as e:
        return jsonify(message='Failed to submit answers', error=str(e)), 500


@user_bp.route('/question-sets/<int:question_set_id>/start-recording', methods=['POST'])
@jwt_required()
def start_recording(question_set_id):
    global video_recording  # Define video_recording as a global variable
    try:
        user_id = get_jwt_identity()

        # Retrieve the admin_id associated with the question set
        with Session() as session:
            question_set = session.query(QuestionSet).filter_by(id=question_set_id).first()
            if not question_set:
                return jsonify(message='Question set not found'), 404

            admin_id = question_set.admin_id

        # Set the user's recording status to True
        video_recording[user_id] = True

        # Start video recording in a separate thread
        video_save_path = f'static/{user_id}_test_{question_set_id}.avi'  # Set the video save path
        video_thread = threading.Thread(target=record_video, args=(admin_id, user_id, video_save_path))
        video_thread.start()

        return jsonify(message='Live recording started'), 200
    except Exception as e:
        return jsonify(message='Failed to start recording', error=str(e)), 500
