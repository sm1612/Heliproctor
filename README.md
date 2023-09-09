# Exam Proctoring Backend

This is the backend component of the Exam Proctoring system, designed to manage user registration, test creation, video recording, and answer submission for online exams.

Please note that the system currently encounters the following issue that needs to be fixed:

- **Error**: Users may encounter an error message, "cannot access local variable 'video_recording' where it is not associated with a value," when trying to submit answers. This issue needs to be resolved.

Additionally, TBD integration with the machine learning model to return the metrics is pending. The system should be configured to send recorded videos to the ML model for further analysis and proctoring. Further development and integration are required in this area.

## Features

- User registration and authentication
- Admins can create and manage online tests
- Students can take tests with video proctoring
- Video recording during tests
- Answer submission with automatic grading
- Metrics and video details for admins

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x installed.
- Virtual environment set up (recommended).

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/exam-proctoring-backend.git
    cd exam-proctoring-backend
    ```

2. Create and activate a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```
4. Run the application:
   ```bash
    python app.py
    ```
## Usage

- Access the API at `http://localhost:5000`.

## API Endpoints

- **User Registration**
  - POST `/auth/register`: Register a new user.

- **User Authentication**
  - POST `/auth/login`: Log in and obtain an access token.

- **Admin Operations**
  - POST `/admin/tests/create`: Create a new test.
  - GET `/admin/tests`: List tests created by the admin.
  - GET `/admin/tests/<test_id>`: View details of a specific test.
  - GET `/admin/videos`: List student videos.
  - GET `/admin/videos/<video_id>`: View details of a specific student video.

- **User Operations**
  - GET `/user/question-sets`: List available question sets.
  - GET `/user/question-sets/<question_set_id>/questions`: Get questions for a question set.
  - POST `/user/question-sets/<question_set_id>/start-recording`: Start video recording.
  - POST `/user/question-sets/<question_set_id>/submit-answers`: Submit test answers, stop video recording and submit it.

 ## Video Recording

This backend supports video recording during online tests. Here's how it works:

- When a student starts a test by hitting the `/user/question-sets/<question_set_id>/start-recording` endpoint, the server initiates video recording.
- The student's webcam feed is captured and saved as a video file in the `static` folder.
- The video recording continues until the student submits their test or the test time expires.
- After test submission, the video is saved and associated with the student's profile for admin review.

