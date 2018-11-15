# encoding: utf-8

import glob, sys, os, json
import urllib.request, urllib.parse, urllib.error
import requests
from datetime import datetime
import random

file_good_wavs = './palavrasgoogle133k_celio.csv'
word_evaluation_requests = {}


def list_tags_occurrences_of_trainning_files(path):
    for word in os.listdir(path):
        if not word.startswith('.'):
            print(word)
            print(os.system("cut  -d' ' -f1 {} | sort | uniq -c ".format(path + '/' + word)))


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def clear_word(w):
    w = w.replace('ã', 'a')
    w = w.replace('á', 'a')
    w = w.replace('é', 'e')
    w = w.replace('ê', 'e')
    w = w.replace('í', 'i')
    w = w.replace('ó', 'o')
    w = w.replace('ç', 'c')
    return w


def generate_requests(dic, words, path):
    print("- Gerando requisições...")
    for fono in ['0', '1']:  # loop fono answer (0 or 1)
        for wd in words:  # loop all words
            for id_av in dic[wd, fono]:
                cleared_word = clear_word(wd)  # retira os acentos
                fullpath = path + '/noiseless.Audios.' + cleared_word + '_' + id_av + '.wav'

                if os.path.exists(fullpath):
                    if cleared_word.lower() not in word_evaluation_requests:  # Não existe a chave
                        word_evaluation_requests[cleared_word.lower()] = []

                    word_evaluation_requests[cleared_word.lower()].append({  # Adiciona a palavra original no array
                        'word': wd.lower(),
                        'file_path': fullpath,
                        'therapist_eval': str(fono)
                    })


def main(argv):
    global file_good_wavs, word_evaluation_requests
    if len(argv) != 2:
        print("Use: " + argv[0] + " <path_to_audio_files>")
        exit(0)

    words = []

    print("- Lendo informações de avaliações do CSV...")
    dic = {}
    with open(file_good_wavs) as fp:
        for line in fp:
            id_av, wd, fono = line.split(';')
            # wd = clear_word(wd)
            fono = fono.rstrip()
            if wd not in words:
                words.append(wd)
            try:
                dic[wd, fono].append(id_av)
            except Exception as e:
                dic[wd, fono] = []
                dic[wd, fono].append(id_av)

    # Passo 1 - Ler arquivo e gerar as requests
    generate_requests(dic=dic, words=words, path=argv[1])

    # Passo 2 - Criar um usuário do tipo therapist para submeter avaliações

    server = "http://127.0.0.1:5000/"
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
    url = "api/registration"

    payload = {
        'username': "tester-01",
        'fullname': "Tester 01",
        'password': "tester01",
        'type': "therapist"
    }

    headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache",
        # 'Postman-Token': "73e316e7-5173-4b34-8a41-9bc8d0e2024c",
        'User-Agent': user_agent
    }

    print('------------ Criação do Usuário --------------')
    try:
        data = json.dumps(payload).encode('utf8')
        req = urllib.request.Request(url=server + url, data=data, headers=headers, method='POST')
        res = urllib.request.urlopen(req)
        resData = json.loads(res.read().decode('utf8'))
        print(res.reason)
        print(resData)

    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        res = json.loads(e.read().decode('utf8'))
        print(e.reason)
        print(res['message'])
        if e.code == 422:  # usuário ja existe
            pass
        else:
            exit(1)

    # Passo 3 - Logar um usário na API
    print('------------ Login do Usuário --------------')
    url = 'api/login'
    payload = {
        "username": "tester-01",
        "password": "tester01"
    }
    res_data = {}
    try:
        data = json.dumps(payload).encode('utf8')
        req = urllib.request.Request(url=server + url, data=data, headers=headers, method='POST')
        res = urllib.request.urlopen(req)
        res_data = json.loads(res.read().decode('utf8'))
        print(res.reason)
        print(res_data)

    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        res = json.loads(e.read().decode('utf8'))
        print(e.reason)
        print(res)
        exit(1)

    else:
        access_token = res_data['token'] if 'token' in res_data else None

        if not access_token:
            print('Token de acesso não encontrado')
            exit(1)

        # Passo 4 - Criar um Paciente para o Teste
        print('------------ Criação de um paciente de teste --------------')
        url = 'api/patient/registration'
        payload = {
            "name": "Paciente de Caso de Teste 01",
            "birth": "1996-12-12",
            "school": "UFSM",
            "school_type": "PRI",
            "city": "Santa Maria",
            "state": "RS",
            "sex": "",
            "caregiver": "God"
        }
        headers['Authorization'] = 'Bearer ' + access_token

        try:
            data = json.dumps(payload).encode('utf8')
            req = urllib.request.Request(url=server + url, data=data, headers=headers, method='POST')
            res = urllib.request.urlopen(req)
            res_data = json.loads(res.read().decode('utf8'))
            print(res.reason)
            print(res_data)

        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            res = json.loads(e.read().decode('utf8'))
            print(e.reason)
            print(res['message'])
            if e.code == 422:  # paciente ja existe
                url = 'api/patient?name=teste%2001'  # busca pelo paciente teste 01
                try:
                    req = urllib.request.Request(url=server + url, headers=headers, method='GET')
                    res = urllib.request.urlopen(req)
                    res_data = json.loads(res.read().decode('utf8'))[0]  # pega primeiro resultado
                    print(res.reason)
                    print(res_data)

                except (urllib.error.URLError, urllib.error.HTTPError) as e:
                    res = json.loads(e.read().decode('utf8'))
                    print(e.reason)
                    print(res)
                    exit(1)
            else:
                exit(1)

        patient_id = res_data['id'] if 'id' in res_data else None

        if not patient_id:
            print('ID do Paciente não encontrado')
            exit(1)

        # Passo 5 - criar uma avaliação
        print('------------ Criação de uma avaliação de teste --------------')
        url = 'api/evaluation'
        payload = {
            "type": "N",
            "patient_id": patient_id
        }
        # TODO remover headers depois
        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
            'Authorization': 'Bearer ' + access_token,
            'User-Agent': user_agent
        }
        test_evaluations_id = []  # armazena os ids das avalaiçoes criadas
        for i in range(0, 5):  # Criação de 5 avaliações para o mesmo paciente
            try:
                data = json.dumps(payload).encode('utf8')
                req = urllib.request.Request(url=server + url, data=data, headers=headers, method='POST')
                res = urllib.request.urlopen(req)
                res_data = json.loads(res.read().decode('utf8'))
                print(res.reason)
                print(res_data)

            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                res = json.loads(e.read().decode('utf8'))
                print(e.reason)
                print(res['message'])
                if e.code == 422:  # avaliação ja existe
                    pass
                else:
                    exit(1)

            evaluation_id = res_data['id'] if 'id' in res_data else None

            if not evaluation_id:
                print('ID da Avaliação não encontrado')
                exit(1)
            else:
                test_evaluations_id.append(evaluation_id)

        # loop pelas palavras selecionadas e avaliações criadas
        # cada palavra seleciona uma posição aleatória, indicando uma request a ser feita

        # for key in word_evaluation_requests.keys():
        # for key in ['anel', 'barriga', 'batom', 'beijo', 'bolsa']:
        for key in ['anel', 'barriga', 'batom']:
            word = word_evaluation_requests[key]
            for eval_id in test_evaluations_id:  # loop por cada avaliação
                random_pos = random.randint(0, len(word) - 1)

                # Passo 5 - submeter um audio de cada palavra para uma avaliação
                print('------------ Enviando audios para a avaliação de teste --------------')

                req_params = word[random_pos]
                print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]') + 'POS: {} WORD: {} POST -> {}'.format(random_pos, key, json.dumps(req_params)))

                url = 'api/word/' + req_params['word'] + '/evaluation/' + str(eval_id)
                filepath = os.path.abspath(req_params['file_path'])
                payload = {
                    'therapist_eval': req_params['therapist_eval']
                }
                headers = {'Authorization': 'Bearer ' + access_token}  # redefine os headers das requests

                try:
                    with open(filepath, 'rb') as f:
                        read_data = f.read()
                        req = requests.post(
                            url=server + url,
                            files={
                                'file': (os.path.basename(filepath), read_data, 'application/octet-stream'),
                                'form': (None, json.dumps(payload),
                                         'application/x-www-form-urlencoded; multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW')
                            },
                            headers=headers
                        )
                        res_data = req.json()
                        print(req.status_code)
                        print(res_data)
                    f.close()

                except requests.exceptions.HTTPError as e:
                    # res = json.loads(e.read().decode('utf8'))
                    # print(e.reason)
                    # print(res['message'])
                    print(e)


if __name__ == "__main__":
    main(sys.argv)
