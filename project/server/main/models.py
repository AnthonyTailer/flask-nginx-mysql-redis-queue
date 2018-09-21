from database import Base, db_session
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, PrimaryKeyConstraint, func
from sqlalchemy.orm import relationship
import enum
from passlib.hash import pbkdf2_sha256 as sha256
from project.server.main.helpers import get_date_br


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
    __table_args__ = (
        PrimaryKeyConstraint('id', 'patient_id', 'evaluator_id'),
    )

    def __repr__(self):
        return '{}'.format(self.id)

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, default=get_date_br)
    type = Column(String(1), nullable=False)

    patient_id = Column(Integer, ForeignKey('patients.id'))
    patient = relationship("PatientModel", back_populates="evaluation")

    evaluator_id = Column(Integer, ForeignKey('users.id'))
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

    evaluation = relationship("EvaluationModel", back_populates="words")
    word = relationship("WordModel", back_populates="evaluations")

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

    def update_audio_evaluation(self, ml_eval=None, api_eval=None, therapist_eval=None):
        evaluation = db_session.query(WordEvaluationModel) \
            .filter(WordEvaluationModel.evaluation_id == self.evaluation_id) \
            .filter(WordEvaluationModel.word_id == self.word_id)

        if ml_eval:
            evaluation.update({
                'ml_eval': bool(ml_eval)
            })
        if api_eval:
            evaluation.update({
                'api_eval': bool(api_eval)
            })
        if therapist_eval:
            evaluation.update({
                'therapist_eval': bool(therapist_eval)
            })

        db_session.commit()

    @classmethod
    def find_evaluations_by_id(cls, evaluation_id):
        return db_session.query(WordEvaluationModel).filter(WordEvaluationModel.evaluation_id == evaluation_id).all()