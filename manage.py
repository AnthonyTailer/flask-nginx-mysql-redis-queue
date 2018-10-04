from app import create_app, db
from app.models import User, Task, RevokedToken, Patient, Word, WordTranscription, Evaluation, WordEvaluation


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'RevokedToken': RevokedToken,
            'Patient': Patient, 'Word': Word, 'WordTranscription': WordTranscription,
            'Evaluation': Evaluation, 'WordEvaluation': WordEvaluation}
