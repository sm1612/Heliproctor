from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from sqlalchemy import UniqueConstraint
from datetime import datetime
from database import *

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')  # 'user' or 'admin'
    created_at = Column(DateTime, default=func.now())
    answers = relationship('UserAnswer', back_populates='user')
    
    @validates('role')
    def validate_role(self, key, value):
        # Ensure only 'user' or 'admin' roles are allowed
        assert value in ['user', 'admin'], "Invalid role"
        return value

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)

class QuestionSet(Base):
    __tablename__ = 'question_sets'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False)
    admin = relationship('Admin', back_populates='question_sets')  # Define the relationship here
    questions = relationship('Question', back_populates='question_set')
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('name', 'admin_id', name='unique_question_set_admin'),
    )

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(String(500), nullable=False)
    question_set_id = Column(Integer, ForeignKey('question_sets.id'), nullable=False)
    question_set = relationship('QuestionSet', back_populates='questions')  # Define the relationship here
    options = relationship('Option', back_populates='question')
    created_at = Column(DateTime, default=func.now())
    user_answers = relationship('UserAnswer', back_populates='question')

class Option(Base):
    __tablename__ = 'options'
    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=False)
    is_correct = Column(Boolean, default=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    question = relationship('Question', back_populates='options')  # Define the relationship here
    created_at = Column(DateTime, default=func.now())
    user_answers = relationship('UserAnswer', back_populates='option')

    def __init__(self, text, is_correct, question_id, created_at):
        self.text = text
        self.is_correct = is_correct
        self.question_id = question_id
        self.created_at = created_at


class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    question_sets = relationship('QuestionSet', back_populates='admin')
    created_at = Column(DateTime, default=func.now())

class UserMetrics(Base):
    __tablename__ = 'user_metrics'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False)
    recording_duration = Column(Float, nullable=False)
    eyes_off_screen_duration = Column(Float, nullable=False)
    lips_moving_duration = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

class VideoRecording(Base):
    __tablename__ = 'video_recordings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    recorded_at = Column(DateTime, default=func.now())

class UserAnswer(Base):
    __tablename__ = 'user_answers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    option_id = Column(Integer, ForeignKey('options.id'), nullable=False)
    is_correct = Column(Boolean, default=False)  # Indicates whether the user's answer is correct
    marks_obtained = Column(Float)  # New column to store marks obtained
    created_at = Column(DateTime, default=func.now())

    user = relationship('User', back_populates='answers')  # Define the relationship to User
    question = relationship('Question', back_populates='user_answers')  # Define the relationship to Question
    option = relationship('Option', back_populates='user_answers')  
