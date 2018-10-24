import matplotlib
from sklearn.datasets import load_svmlight_file
from sklearn import tree
from app.helpers import generate_spectrogram, generate_testing_file
from app.models import WordEvaluation
import speech_recognition as sr
from app import create_app, db

app = create_app()
app.app_context().push()


def ml_transcribe_audio(evaluation_id, word_id, wd, wd_audio_path):
    app.logger.info("ML API -> EVAL-ID: {}, WORD-ID: {}, WORD: {}, WD-PATH: {}".format(evaluation_id, word_id, wd, wd_audio_path))
    matplotlib.use('Agg')
    app.logger.info("ML API -> Loading training file...")
    X_train, y_train = load_svmlight_file('./app/training_files/' + wd.capitalize())

    clf = tree.DecisionTreeClassifier()

    app.logger.info("ML API -> Fitting classifier...")
    clf.fit(X_train, y_train)

    generate_spectrogram(wd, wd_audio_path)
    generate_testing_file(wd)

    X_test, y_test = load_svmlight_file('./app/testing.scikit')
    y_pred = clf.predict(X_test)

    app.logger.info("ML API -> Predicted {}".format(y_pred))

    try:
        db.session.execute("UPDATE word_evaluation SET ml_eval=:new_value WHERE word_id=:param1 AND evaluation_id=:param2",
                       {"param1": evaluation_id, "param2": word_id, "new_value": bool(y_pred)})
        db.session.commit()
        return y_pred
    except Exception as e:
        app.logger.info("ML API -> Error on update result {}".format(e))
        db.session.rollback()
        return False


def google_transcribe_audio(evaluation_id, word_id, wd, wd_audio_path):
        r = sr.Recognizer()
        audioFile = sr.AudioFile(wd_audio_path)
        with audioFile as source:
            try:
                evaluation = db.session.query(WordEvaluation) \
                    .filter(WordEvaluation.evaluation_id == evaluation_id) \
                    .filter(WordEvaluation.word_id == word_id)
            except Exception as e:
                app.logger.error("GOOGLE API EXCEPTION -> {}".format(e))
            else:
                try:
                    app.logger.info("GOOGLE API -> Transcribing audio")
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.record(source)
                    result = r.recognize_google(audio, language='pt-BR')

                    if result == wd:
                        evaluation.update({
                            'api_eval': bool(True)
                        })
                    else:
                        evaluation.update({
                            'api_eval': bool(False)
                        })
                    db.session.commit()
                    return result

                except sr.UnknownValueError as e:
                    app.logger.warn("GOOGLE API UNKNOWN VALUE -> {}".format(e))
                    evaluation.update({
                        'api_eval': bool(False)
                    })
                    db.session.commit()
                    return False

                except sr.RequestError as e:
                    app.logger.error("GOOGLE API EXCEPTION -> {}".format(e))
                    evaluation.update({
                        'api_eval': bool(False)
                    })
                    db.session.commit()
                    return False