from database import Base, db_session
from sqlalchemy import Column, Integer, String, Date, ForeignKey, PrimaryKeyConstraint, func
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

    # @classmethod
    # def return_all(cls):
    #     def to_json(x):
    #         return {
    #             'username': x.username,
    #             'fullname': x.fullname,
    #             'type': x.type
    #         }
    #
    #     return {'users': list(map(lambda x: to_json(x), db_session.query(UserModel).all()))}

    # @classmethod
    # def delete_all(cls):
    #     try:
    #         num_rows_deleted = db_session.query(UserModel).delete()
    #         db_session.commit()
    #         return {'message': '{} registro(s) deletados'.format(num_rows_deleted)}
    #
    #     except:
    #         return {'message': 'Algo de errado não está certo'}, 500


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
    address = Column(String(255), nullable=False)
    created_at = Column(Date, nullable=False, default=get_date_br)

    evaluation = relationship("EvaluationModel", back_populates="patient")

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    @classmethod
    def find_by_name(cls, name):
        return db_session.query(PatientModel).filter(PatientModel.name == name).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'id': x.id,
                'name': x.name
            }

        return {'patients': list(map(lambda x: to_json(x), db_session.query(PatientModel).all()))}


class EvaluationModel(Base):
    __tablename__ = 'evaluations'
    __table_args__ = (
        PrimaryKeyConstraint('id', 'patient_id', 'evaluator_id'),
    )

    def __repr__(self):
        return '{}'.format(self.id)

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    type = Column(String(1))

    patient_id = Column(Integer, ForeignKey('patients.id'))
    patient = relationship("PatientModel", back_populates="evaluation")

    evaluator_id = Column(Integer, ForeignKey('users.id'))
    evaluator = relationship("UserModel", back_populates="evaluation")

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()

    @classmethod
    def find_by_user(cls, user_id):
        return db_session.query(EvaluationModel).filter(EvaluationModel.evaluator_id == user_id).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'id': x.id,
                'date': x.date,
                'evaluator': x.evaluator,
                'patient': x.patient
            }

        return {'evaluations': list(map(lambda x: to_json(x), db_session.query(EvaluationModel).all()))}


class WordModel(Base):
    __tablename__ = 'words'

    def __repr__(self):
        return '{}'.format(self.word)

    def orderdefinition(self):
        return db_session.query(func.count(WordModel.id)).scalar() + 1

    id = Column(Integer, primary_key=True)
    word = Column(String(255), nullable=False, unique=True)
    tip = Column(String(255))
    order = Column(Integer,  default=orderdefinition)

    transcription = relationship("WordTranscriptionModel", back_populates="word", cascade="all, delete")

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



    # @classmethod
    # def return_all(cls):
    #     def to_json(x):
    #         return {
    #             'id': x.id,
    #             'word': x.word,
    #             'audio_link': x.audio_link
    #         }
    #
    #     return {'words': list(map(lambda x: to_json(x), db_session.query(WordModel).all()))}

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
