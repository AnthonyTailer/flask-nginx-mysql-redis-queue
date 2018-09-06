import time
import speech_recognition as sr


def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True


def google_transcribe_audio(file):
    r = sr.Recognizer()
    audioFile = sr.AudioFile(file)
    with audioFile as source:

        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.record(source)
            # return r.recognize_google(audio, language='pt-BR')
            return r.recognize_google(audio)

        except sr.UnknownValueError as e:

            return "Could not understand audio; {0}".format(e)

        except sr.RequestError as e:

            return "Could not request results; {0}".format(e)


