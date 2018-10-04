from sqlalchemy import func
from sqlalchemy.orm import relationship, backref
import enum
from flask import current_app
from passlib.hash import pbkdf2_sha256 as sha256
from app.helpers import get_date_br
import redis
import rq
from app import db

class EnumType(enum.Enum):
    anonymous = 1,
    therapist = 2

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.name)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    fullname = db.Column(db.String(255), nullable=False, index=True)
    password = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(120), nullable=False, index=True)

    evaluations = relationship('Evaluation', backref="evaluator", lazy='dynamic')
    tasks = relationship('Task', backref='user', lazy='dynamic')

    def __repr__(self):
        return '{}'.format(self.username)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, username, fullname, type):
        User.query.filter_by(username=self.username) \
            .update({'username': username, 'fullname': fullname, 'type': type})
        db.session.commit()

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def find_by_username(cls, username):
        return User.query.filter_by(username=username).first()

    @classmethod
    def change_password(cls, username, new_password):
        User.query.filter_by(username=username) \
            .update({'password': cls.generate_hash(new_password)})
        db.session.commit()

    def launch_task(self, name, description, *args):
        rq_job = current_app.task_queue.enqueue('app.tasks.' +name, *args)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()


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

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = RevokedToken.query.filter_by(jti=jti).first()
        return bool(query)


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

    evaluation = relationship("Evaluation", backref="patient")

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, name, birth, sex, school, school_type, caregiver, phone, city, state, address):
        Patient.query.filter_by(id=self.id) \
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
        return Patient.query.filter_by(name=name).first()

    @classmethod
    def find_by_id(cls, id):
        return Patient.query.filter_by(id=id).first()

    @classmethod
    def return_all(cls):
        return Patient.query.all()


class Word(db.Model):
    __tablename__ = 'words'

    def __repr__(self):
        return '{}'.format(self.word)

    def orderdefinition(self):
        return func.query(Word.count(Word.id)).scalar() + 1

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
        Word.query \
            .filter_by(word=self.word) \
            .update({'word': word, 'tip': tip})
        db.session.commit()

    @classmethod
    def delete_by_word(cls, word):
        word_delete = Word.query.filter_by(word=word).first()
        db.delete(word_delete)
        db.session.commit()

    @classmethod
    def find_by_word(cls, word):
        return Word.query.filter_by(word=word).first()

    @classmethod
    def return_all(cls):
        return Word.query.all()


class WordTranscription(db.Model):
    __tablename__ = 'transcription'

    id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.Integer)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id', ondelete=u'CASCADE'))

    def __repr__(self):
        return '{}'.format(self.transcription)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, word_id, transcription):
        WordTranscription.query \
            .filter_by(transcription=self.transcription) \
            .update({'word_id': word_id, 'transcription': transcription})
        db.session.commit()

    def delete_transcription(self):
        db.delete(self)
        db.session.commit()

    @classmethod
    def find_by_word_id(cls, word_id):
        return WordTranscription.query.filter_by(word_id=word_id).all()

    @classmethod
    def find_by_transcription_id(cls, id):
        return WordTranscription.query.filter_by(id=id).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'id': x.id,
                'transcription': x.transcription,
                'word': x.word,
            }

        return {'transcriptions': list(map(lambda x: to_json(x), WordTranscription.query.all()))}


class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    def __repr__(self):
        return '{}'.format(self.id)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, default=get_date_br)
    type = db.Column(db.String(1), nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    # patient = relationship("Patient", back_populates="evaluation")

    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # evaluator = relationship("User", back_populates="evaluations")

    words = relationship("Word", secondary='word_evaluation')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, type, patient_id):
        Evaluation.query \
            .filter_by(id=self.id) \
            .update({
            'type': type,
            'patient_id': patient_id
        })
        db.session.commit()

    @classmethod
    def find_all_user_evaluations(cls, user_id):
        return Evaluation.query.filter_by(id=user_id).first()


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

    evaluation = relationship("Evaluation", backref=backref("word_assoc"))
    word = relationship("Word", backref=backref("evaluation_assoc"))

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_to_db(self, transcription_target_id, transcription, repetition, audio_path):
        WordEvaluation.query \
            .filter_by(evaluation_id=self.evaluation_id) \
            .filter_by(word_id=self.word_id) \
            .update({
            'transcription_target_id': transcription_target_id,
            'transcription_eval': transcription,
            'repetition': repetition,
            'audio_path': audio_path,
        })
        db.session.commit()

        # if ml_eval:
        #     db.execute(
        #         "UPDATE word_evaluation SET ml_eval=:new_value WHERE word_id=:param1 AND evaluation_id=:param2",
        #         {"param1": evaluation_id, "param2": word_id, "new_value": bool(ml_eval)}
        #     )

    # def google_transcribe_audio(self, file):
    #     r = sr.Recognizer()
    #     audioFile = sr.AudioFile(file)
    #     with audioFile as source:
    #         try:
    #             evaluation = session.query(WordEvaluationModel) \
    #                 .filter(WordEvaluationModel.evaluation_id == self.evaluation_id) \
    #                 .filter(WordEvaluationModel.word_id == self.word_id)
    #         except Exception as e:
    #             logger.error("GOOGLE API -> {}".format(e))
    #         else:
    #             try:
    #                 logger.info("GOOGLE API -> Transcribing audio")
    #                 r.adjust_for_ambient_noise(source, duration=0.5)
    #                 audio = r.record(source)
    #                 result = r.recognize_google(audio, language='pt-BR')
    #
    #                 evaluation.update({
    #                     'api_eval': bool(result)
    #                 })
    #                 session.commit()
    #                 return result
    #
    #             except sr.UnknownValueError as e:
    #                 logger.error("GOOGLE API -> {}".format(e))
    #                 evaluation.update({
    #                     'api_eval': bool(False)
    #                 })
    #                 session.commit()
    #                 return False
    #
    #             except sr.RequestError as e:
    #                 logger.error("GOOGLE API -> {}".format(e))
    #                 evaluation.update({
    #                     'api_eval': bool(False)
    #                 })
    #                 session.commit()
    #                 return False

    @classmethod
    def find_evaluations_by_id(cls, evaluation_id):
        return WordEvaluation.query.filter_by(evaluation_id=evaluation_id).all()