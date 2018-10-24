import base64
import os

from marshmallow import fields
from sqlalchemy import func
from sqlalchemy.orm import relationship, backref
import enum
from flask import current_app
from passlib.hash import pbkdf2_sha256 as sha256
from sqlalchemy.orm.exc import NoResultFound

from app.helpers import get_date_br
import redis
import rq
from app import db, ma


class EnumType(enum.Enum):
    anonymous = 1,
    therapist = 2

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.name)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    @classmethod
    def get_rq_job_by_id(cls, task_id):
        try:
            rq_job = rq.job.Job.fetch(task_id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    @classmethod
    def get_task_by_user(cls, task_id, user):
        task = db.session.query(Task) \
            .filter_by(id=task_id) \
            .filter_by(user_id=user.id) \
            .first()

        if not task:
            return None

        return task.get_rq_job()

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


class WordTranscription(db.Model):
    __tablename__ = 'transcription'

    id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(1))
    word_id = db.Column(db.Integer, db.ForeignKey('words.id', ondelete=u'CASCADE'))

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, word_id, transcription, type=''):
        db.session.query(WordTranscription) \
            .filter_by(transcription=self.transcription) \
            .update({'word_id': word_id, 'transcription': transcription, 'type': type})
        db.session.commit()

    def delete_transcription(self):
        db.delete(self)
        db.session.commit()

    @classmethod
    def find_by_word_id(cls, word_id):
        return db.session.query(WordTranscription).filter_by(word_id=word_id).all()

    @classmethod
    def find_by_transcription_id(cls, id):
        return db.session.query(WordTranscription).filter_by(id=id).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'id': x.id,
                'transcription': x.transcription,
                'word': x.word,
                'type': x.type
            }

        return {'transcriptions': list(map(lambda x: to_json(x), db.session.query(WordTranscription).all()))}


class WordEvaluation(db.Model):
    __tablename__ = 'word_evaluation'

    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), primary_key=True)

    transcription_target_id = db.Column(db.Integer, db.ForeignKey('transcription.id'))
    transcription_eval = db.Column(db.String(255), nullable=True)
    repetition = db.Column(db.Boolean, default=False)
    audio_path = db.Column(db.String(255), nullable=False)
    ml_eval = db.Column(db.Boolean)
    api_eval = db.Column(db.Boolean)
    therapist_eval = db.Column(db.Boolean)

    transcription_target = relationship("WordTranscription", backref="transcription_target")
    evaluation = relationship("Evaluation", backref=backref("word_assoc"), lazy="joined", join_depth=2)
    word = relationship("Word", backref=backref("evaluation_assoc"), lazy="joined", join_depth=2)

    def save_to_db(self):
        db.session.add(self)
        # db.session.commit()

    def update_to_db(self, transcription_target_id, transcription, repetition, audio_path):
        db.session.query(WordEvaluation) \
            .filter_by(evaluation_id=self.evaluation_id) \
            .filter_by(word_id=self.word_id) \
            .update({
            'transcription_target_id': transcription_target_id,
            'transcription_eval': transcription,
            'repetition': repetition,
            'audio_path': audio_path,
        })
        db.session.commit()

    @classmethod
    def find_evaluations_by_id(cls, evaluation_id):
        return db.session.query(WordEvaluation).filter(WordEvaluation.evaluation_id == evaluation_id).all()

    @classmethod
    def get_word_evaluations_by_id(cls, evaluation_id):
        def to_json(x):
            current_app.logger.warn(x)
            return {
                'word': x[1].word.word,
                'transcription_eval': x[1].transcription_eval,
                'transcription_target': x[1].transcription_target.transcription,
                'repetition': x[1].repetiton,

            }

        wd_evals = db.session.query(Evaluation, WordEvaluation) \
            .outerjoin(WordEvaluation,
                       (Evaluation.id == evaluation_id) and (WordEvaluation.evaluation_id == evaluation_id)).all()

        return list(map(lambda x: to_json(x), wd_evals))

    @classmethod
    def find_word_evaluation_by_id_and_word(cls, evaluation_id, word):
        return db.session.query(WordEvaluation) \
            .filter_by(evaluation_id=evaluation_id) \
            .filter_by(word=word) \
            .first()


class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, default=get_date_br)
    type = db.Column(db.String(1), nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    patient = relationship('Patient', backref="patient")

    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # evaluator = relationship("User", back_populates="evaluations")

    words = relationship("Word", secondary='word_evaluation', lazy="joined", join_depth=2)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, type, patient_id):
        db.session.query(Evaluation) \
            .filter_by(id=self.id) \
            .update({
            'type': type,
            'patient_id': patient_id
        })
        db.session.commit()

    @classmethod
    def find_all_user_evaluations(cls, user_id):
        return db.session.query(Evaluation).filter_by(evaluator_id=user_id).first()

    @classmethod
    def find_by_id(cls, eval_id):
        return db.session.query(Evaluation).filter_by(id=eval_id).first()


class Word(db.Model):
    __tablename__ = 'words'

    def __repr__(self):
        return '{}'.format(self.word)

    def orderdefinition(self):
        return db.session.query(func.count('*')).select_from(Word).scalar() + 1

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable=False, unique=True)
    tip = db.Column(db.String(255))
    order = db.Column(db.Integer, default=orderdefinition)

    transcription = relationship("WordTranscription", backref="word", cascade="all, delete")
    evaluations = relationship('Evaluation', secondary='word_evaluation')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, word, tip):
        db.session.query(Word) \
            .filter(func.lower(Word.word) == func.lower(word))\
            .update({'word': word, 'tip': tip})
        db.session.commit()

    @classmethod
    def delete_by_word(cls, word):
        word_delete = db.session.query(Word).filter(func.lower(Word.word) == func.lower(word)).first()
        db.session.delete(word_delete)
        db.session.commit()

    @classmethod
    def find_by_word(cls, word):
        return db.session.query(Word).filter(func.lower(Word.word) == func.lower(word)).first()

    @classmethod
    def return_all(cls):
        return db.session.query(Word).all()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    fullname = db.Column(db.String(255), nullable=False, index=True)
    password = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(120), nullable=False, index=True)
    token = db.Column(db.String(32), index=True, unique=True)

    evaluations = relationship('Evaluation', backref="evaluator", lazy='dynamic')
    tasks = relationship('Task', backref='user', lazy='dynamic')

    def __repr__(self):
        return '{}'.format(self.username)

    def get_token(self):
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        db.session.add(self)
        return self.token

    @staticmethod
    def check_token(token):
        if RevokedToken.is_token_blacklisted(token):
            return None
        user = User.query.filter_by(token=token).first()
        if user is None:
            return None
        return user

    def revoke_token(self):
        revoked_token = RevokedToken(token=self.token)
        db.session.add(revoked_token)

    def save_to_db(self):
        db.session.add(self)

    def update_to_db(self, username, fullname, type):
        db.session.query(User).filter_by(username=self.username) \
            .update({'username': username, 'fullname': fullname, 'type': type})

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def find_by_username(cls, username):
        return db.session.query(User).filter_by(username=username).first()

    @classmethod
    def change_password(cls, username, new_password):
        db.session.query(User).filter_by(username=username) \
            .update({'password': cls.generate_hash(new_password)})

    def launch_task(self, name, description, *args):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, *args)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return db.session.query(Task).filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return db.session.query(Task).filter_by(name=name, user=self,
                                                complete=False).first()


class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(120))

    def add(self):
        db.session.add(self)

    @classmethod
    def is_token_blacklisted(cls, token):
        try:
            token = db.session.query(RevokedToken).filter_by(token=token).one()
            return token is not None
        except NoResultFound:
            return False


class Patient(db.Model):
    __tablename__ = 'patients'

    def __repr__(self):
        return '{}'.format(self.name)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    birth = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(1))
    school = db.Column(db.String(255), nullable=False)
    school_type = db.Column(db.String(3))
    caregiver = db.Column(db.String(255))  # responsavel
    phone = db.Column(db.String(255))
    city = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    address = db.Column(db.String(255))
    created_at = db.Column(db.Date, nullable=False, default=get_date_br)

    evaluation = relationship("Evaluation", backref="evaluations")

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update_to_db(self, name, birth, sex, school, school_type, caregiver, phone, city, state, address):
        db.session.query(Patient).filter_by(id=self.id) \
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
        db.session.commit()

    @classmethod
    def find_by_name(cls, name):
        return db.session.query(Patient).filter_by(name=name).first()

    @classmethod
    def ilike_by_name(cls, name):
        return db.session.query(Patient).filter(Patient.name.ilike('%' + name + '%'))

    @classmethod
    def find_by_id(cls, id):
        return db.session.query(Patient).filter_by(id=id).first()

    @classmethod
    def return_all(cls):
        return db.session.query(Patient).all()


class PatientSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'name', 'birth', 'sex', 'school', 'school_type', 'caregiver', 'phone', 'city', 'state', 'address')
        model = Patient


class EvaluationSchema(ma.Schema):
    patient = fields.Nested(PatientSchema)

    class Meta:
        model = Evaluation
        fields = ('id', 'date', 'type', 'patient')


class UserSchema(ma.Schema):
    class Meta:
        model = User
        # Fields to expose
        fields = ('username', 'fullname', 'type')


class WordSchema(ma.Schema):
    class Meta:
        model = Word
        fields = ('id', 'word', 'tip', 'order')


class WordTranscriptionSchema(ma.ModelSchema):
    class Meta:
        model = WordTranscription
        fields = ('id', 'transcription', 'type')
        sqla_session = db.session


class WordEvaluationSchema(ma.ModelSchema):
    word = fields.Nested(WordSchema)
    transcription_target = fields.Nested(WordTranscriptionSchema)

    class Meta:
        model = WordEvaluation
        fields = ('transcription_target', 'word', 'transcription_eval', 'repetition', 'audio_path', 'ml_eval', 'api_eval', 'therapist_eval')
