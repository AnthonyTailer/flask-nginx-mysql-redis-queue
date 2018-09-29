from flask import current_app

from database import Base, db_session
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, PrimaryKeyConstraint, func, create_engine
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker
import enum
from passlib.hash import pbkdf2_sha256 as sha256
import speech_recognition as sr
from project.server.main.helpers import get_date_br
import redis
import rq
import os

import logging

logger = logging.getLogger('models_logger')

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('./project/server/logs/models.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


class EnumType(enum.Enum):
    anonymous = 1,
    therapist = 2

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.name)


class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True, nullable=False)
    fullname = Column(String(255), nullable=False)
    password = Column(String(120), nullable=False)
    type = Column(String(120), nullable=False)

    evaluation = relationship("EvaluationModel", back_populates="evaluator")
    tasks = relationship('TaskModel', backref='user', lazy='dynamic')

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    def update_to_db(self, username, fullname, type):
        db_session.query(UserModel) \
            .filter(UserModel.username == self.username) \
            .update({'username': username, 'fullname': fullname, 'type': type})
        db_session.commit()

    def __repr__(self):
        return '{}'.format(self.username)

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def find_by_username(cls, username):
        return db_session.query(UserModel).filter(UserModel.username == username).first()

    @classmethod
    def change_password(cls, username, new_password):
        db_session.query(UserModel) \
            .filter(UserModel.username == username) \
            .update({'password': cls.generate_hash(new_password)})
        db_session.commit()

    def launch_task(self, name, description, *args):
        logger.error("TASK -> {}".format(name))
        logger.error("TASK -> {}".format(description))
        # for i in args:
        #     logger.error("TASK -> {}".format(i))
        rq_job = current_app.task_queue.enqueue(name, *args)
        task = TaskModel(id=rq_job.get_id(), name=name, description=description, user=self)
        db_session.add(task)
        db_session.commit()
        return task

    def get_tasks_in_progress(self):
        return TaskModel.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return TaskModel.query.filter_by(name=name, user=self,
                                         complete=False).first()


class TaskModel(Base):
    __tablename__ = 'tasks'

    id = Column(String(36), primary_key=True)
    name = Column(String(128), index=True)
    description = Column(String(128))
    user_id = Column(Integer, ForeignKey('users.id'))
    complete = Column(Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


class RevokedTokenModel(Base):
    __tablename__ = 'revoked_tokens'

    id = Column(Integer, primary_key=True)
    jti = Column(String(120))

    def add(self):
        db_session.add(self)
        db_session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = db_session.query(RevokedTokenModel).filter(RevokedTokenModel.jti == jti).first()
        return bool(query)


class PatientModel(Base):
    __tablename__ = 'patients'

    def __repr__(self):
        return '{}'.format(self.name)

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    birth = Column(Date, nullable=False)
    sex = Column(String(1))
    school = Column(String(255), nullable=False)
    school_type = Column(String(3))
    caregiver = Column(String(255))  # responsavel
    phone = Column(String(255))
    city = Column(String(255), nullable=False)
    state = Column(String(2), nullable=False)
    address = Column(String(255))
    created_at = Column(Date, nullable=False, default=get_date_br)

    evaluation = relationship("EvaluationModel", back_populates="patient")

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    def update_to_db(self, name, birth, sex, school, school_type, caregiver, phone, city, state, address):
        db_session.query(PatientModel) \
            .filter(PatientModel.id == self.id) \
            .update({
            'name': name,
            'birth': birth,
            'sex': sex,
            'school': school,
            'school_type': school_type,
            'caregiver': caregiver,
            'phone': phone,
            'city': city,
            'state': state,
            'address': address,
        })
        db_session.commit()

    @classmethod
    def find_by_name(cls, name):
        return db_session.query(PatientModel).filter(PatientModel.name == name).first()

    @classmethod
    def find_by_id(cls, id):
        return db_session.query(PatientModel).filter(PatientModel.id == id).first()

    @classmethod
    def return_all(cls):
        return db_session.query(PatientModel).all()


class WordModel(Base):
    __tablename__ = 'words'

    def __repr__(self):
        return '{}'.format(self.word)

    def orderdefinition(self):
        return db_session.query(func.count(WordModel.id)).scalar() + 1

    id = Column(Integer, primary_key=True)
    word = Column(String(255), nullable=False, unique=True)
    tip = Column(String(255))
    order = Column(Integer, default=orderdefinition)

    transcription = relationship("WordTranscriptionModel", back_populates="word", cascade="all, delete")
    evaluations = relationship('EvaluationModel', secondary='word_evaluation')

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    def update_to_db(self, word, tip):
        db_session.query(WordModel) \
            .filter(WordModel.word == self.word) \
            .update({'word': word, 'tip': tip})
        db_session.commit()

    @classmethod
    def delete_by_word(cls, word):
        word_delete = db_session.query(WordModel).filter(WordModel.word == word).first()
        db_session.delete(word_delete)
        db_session.commit()

    @classmethod
    def find_by_word(cls, word):
        return db_session.query(WordModel).filter(WordModel.word == word).first()

    @classmethod
    def return_all(cls):
        return db_session.query(WordModel).all()


class WordTranscriptionModel(Base):
    __tablename__ = 'transcription'

    def __repr__(self):
        return '{}'.format(self.transcription)

    id = Column(Integer, primary_key=True)
    transcription = Column(String(255), nullable=False, unique=True)
    type = Column(Integer)
    word_id = Column(Integer, ForeignKey('words.id', ondelete=u'CASCADE'))
    word = relationship("WordModel", back_populates="transcription")

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    def update_to_db(self, word_id, transcription):
        db_session.query(WordTranscriptionModel) \
            .filter(WordTranscriptionModel.transcription == self.transcription) \
            .update({'word_id': word_id, 'transcription': transcription})
        db_session.commit()

    def delete_transcription(self):
        db_session.delete(self)
        db_session.commit()

    @classmethod
    def find_by_word_id(cls, word_id):
        return db_session.query(WordTranscriptionModel).filter(WordTranscriptionModel.word_id == word_id).all()

    @classmethod
    def find_by_transcription_id(cls, id):
        return db_session.query(WordTranscriptionModel).filter(WordTranscriptionModel.id == id).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'id': x.id,
                'transcription': x.transcription,
                'word': x.word,
            }

        return {'transcriptions': list(map(lambda x: to_json(x), db_session.query(WordTranscriptionModel).all()))}


class EvaluationModel(Base):
    __tablename__ = 'evaluations'

    def __repr__(self):
        return '{}'.format(self.id)

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, default=get_date_br)
    type = Column(String(1), nullable=False)

    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    patient = relationship("PatientModel", back_populates="evaluation")

    evaluator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    evaluator = relationship("UserModel", back_populates="evaluation")

    words = relationship("WordModel", secondary='word_evaluation')

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    def update_to_db(self, type, patient_id):
        db_session.query(EvaluationModel) \
            .filter(EvaluationModel.id == self.id) \
            .update({
            'type': type,
            'patient_id': patient_id
        })
        db_session.commit()

    @classmethod
    def find_all_user_evaluations(cls, user_id):
        return db_session.query(EvaluationModel).filter(EvaluationModel.evaluator_id == user_id).all()

    @classmethod
    def find_by_id(cls, id):
        return db_session.query(EvaluationModel).filter(EvaluationModel.id == id).first()


class WordEvaluationModel(Base):
    __tablename__ = 'word_evaluation'

    evaluation_id = Column(Integer, ForeignKey('evaluations.id'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'), primary_key=True)

    transcription_target_id = Column(Integer, ForeignKey('transcription.id'))
    transcription_eval = Column(String(255), nullable=True)
    repetition = Column(Boolean, default=False)
    audio_path = Column(String(255), nullable=False)
    ml_eval = Column(Boolean)
    api_eval = Column(Boolean)
    therapist_eval = Column(Boolean)

    evaluation = relationship("EvaluationModel", backref=backref("word_assoc"))
    word = relationship("WordModel", backref=backref("evaluation_assoc"))

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    def update_to_db(self, transcription_target_id, transcription, repetition, audio_path):
        db_session.query(WordEvaluationModel) \
            .filter(WordEvaluationModel.evaluation_id == self.evaluation_id) \
            .filter(WordEvaluationModel.word_id == self.word_id) \
            .update({
            'transcription_target_id': transcription_target_id,
            'transcription_eval': transcription,
            'repetition': repetition,
            'audio_path': audio_path,
        })
        db_session.commit()

        # if ml_eval:
        #     db_session.execute(
        #         "UPDATE word_evaluation SET ml_eval=:new_value WHERE word_id=:param1 AND evaluation_id=:param2",
        #         {"param1": evaluation_id, "param2": word_id, "new_value": bool(ml_eval)}
        #     )

    def google_transcribe_audio(self, file):
        user = os.environ['MYSQL_USER']
        pwd = os.environ['MYSQL_ROOT_PASSWORD']
        db = os.environ['DB_NAME']
        host = os.environ['MYSQL_HOST']
        port = os.environ['DB_PORT']

        db_uri = 'mysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (user, pwd, host, port, db)

        engine = create_engine(db_uri, echo=True)

        db_session = scoped_session(sessionmaker(autocommit=False,
                                                 autoflush=False,
                                                 bind=engine))
        session = db_session()

        r = sr.Recognizer()
        audioFile = sr.AudioFile(file)
        with audioFile as source:
            try:
                evaluation = session.query(WordEvaluationModel) \
                    .filter(WordEvaluationModel.evaluation_id == self.evaluation_id) \
                    .filter(WordEvaluationModel.word_id == self.word_id)
            except Exception as e:
                logger.error("GOOGLE API -> {}".format(e))
            else:
                try:
                    logger.info("GOOGLE API -> Transcribing audio")
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.record(source)
                    result = r.recognize_google(audio, language='pt-BR')

                    evaluation.update({
                        'api_eval': bool(result)
                    })
                    session.commit()
                    return result

                except sr.UnknownValueError as e:
                    logger.error("GOOGLE API -> {}".format(e))
                    evaluation.update({
                        'api_eval': bool(False)
                    })
                    session.commit()
                    return False

                except sr.RequestError as e:
                    logger.error("GOOGLE API -> {}".format(e))
                    evaluation.update({
                        'api_eval': bool(False)
                    })
                    session.commit()
                    return False

    @classmethod
    def find_evaluations_by_id(cls, evaluation_id):
        return db_session.query(WordEvaluationModel).filter(WordEvaluationModel.evaluation_id == evaluation_id).all()
