from sklearn.datasets import load_svmlight_file
from app.helpers import generate_spectrogram, generate_testing_file, get_datetime_br, clear_word
from app.models import WordEvaluation, Task
import speech_recognition as sr
from app import create_app, db

app = create_app()
app.app_context().push()


def ml_transcribe_audio(**kwargs):
    evaluation_id = kwargs['evaluation_id']
    word_id = kwargs['word_id']
    wd = kwargs['word']
    wd_audio_path = kwargs['wd_audio_path']
    clf = kwargs['clf']

    app.logger.info(
        "ML API -> EVAL-ID: {}, WORD-ID: {}, WORD: {}, WD-PATH: {}".format(evaluation_id, word_id, wd, wd_audio_path))
    #matplotlib.use('Agg')
    #app.logger.info("ML API -> Loading training file...")
    cleared_word = clear_word(wd)

    tim=generate_spectrogram(wd, wd_audio_path)
    generate_testing_file(wd,tim)

    X_test, y_test = load_svmlight_file('./app/testing.scikit/'+tim)
    y_pred = clf[cleared_word.capitalize()].predict(X_test)
    pred = int(y_pred[0])
#TODO: limpar os spectrotramas e testing.scikit
    app.logger.info("ML API -> Predicted: {}".format(pred))

    try:
        WordEvaluation.update_ml_eval(evaluation_id=evaluation_id, word_id=word_id, ml_eval=pred)
        Task.set_task_completed(evaluation_id=evaluation_id, word_id=word_id, datetime=get_datetime_br(), result=pred)
        return pred
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
