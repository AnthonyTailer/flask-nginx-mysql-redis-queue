import matplotlib
from sklearn.datasets import load_svmlight_file
from sklearn import tree
from database import db_session
import logging
from .helpers import generate_spectrogram, generate_testing_file
from project.server.main import create_app
#

app = create_app()
app.app_context().push()

logger = logging.getLogger('resources_logger')


def ml_transcribe_audio(evaluation_id, word_id, wd, wd_audio_path):
    with app.app_context():
        session = db_session()

        matplotlib.use('Agg')
        logger.info("ML API -> Loading training file...")
        X_train, y_train = load_svmlight_file('./project/server/training_files/' + wd.capitalize())

        clf = tree.DecisionTreeClassifier()

        logger.info("ML API -> Fitting classifier...")
        clf.fit(X_train, y_train)

        generate_spectrogram(wd, wd_audio_path)
        generate_testing_file(wd)

        X_test, y_test = load_svmlight_file('./project/server/main/testing.scikit')
        y_pred = clf.predict(X_test)

        logger.info("ML API -> Predicted {}".format(y_pred))

        session.execute("UPDATE word_evaluation SET ml_eval=:new_value WHERE word_id=:param1 AND evaluation_id=:param2",
                       {"param1": evaluation_id, "param2": word_id, "new_value": bool(y_pred)})
        session.commit()

        return y_pred