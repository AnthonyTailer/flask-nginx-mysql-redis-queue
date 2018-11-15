# Flask Speech API

## Python 3.6

#### Dependências (Ubuntu 18.04)

- Instalação Banco de Dados **MYSQL Versão **5.7****

```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

- Configurar banco de dados MYSQL
```bash
mysql -u root -p
```
- Criação do banco
```bash
mysql> create database speech_api character set utf8 collate utf8_bin;
```  

- Instalação Banco de Dados **REDIS**
```bash
sudo apt update
sudo apt install redis-server
```

#### Instalação do projeto

-  Clonar repositório
 ```bash
 git clone --single-branch -b tasks https://github.com/AnthonyTailer/flask-nginx-mysql-redis-queue.git flask-speech-api
 ```
- Configurar variaveis de ambiente

    - precisa navegar dentro da pasta do projeto
```bash
cd flask-speech-api
```
```bash
 echo "export FLASK_APP=manage.py" >> ~/.profile
 ```
 para criar permanente, ou 
 ```bash
 export FLASK_APP=manage.py
 ```
 
- Configurar arquivo **.env**

    - criar arquivo **.env** na pasta do projeto contendo as informações
 ```dotenv
MYSQL_USER=root
MYSQL_ROOT_PASSWORD=root
MYSQL_HOST=localhost
DB_PORT=3306
DB_NAME=speech_api
APP_SECRET_KEY=f859989a8ee54b9f84c0b0d481c731ab
FLASK_DEBUG=1
 ```
 
#### Instalação das dependêncas do projeto
usando _pip_ na pasta raiz do projeto:
 ```bash
 pip install -r requirements.txt
 ```

#### Rodando a aplicação
na pasta raiz do projeto:
 ```bash
 flask run
 ``` 
### Migrando as tabelas do banco
na pasta raiz do projeto:
 ```bash
 flask db upgrade
 ```
 ### Inserindo dados de palavras e transcrições
 na pasta do projeto:
  ```bash
 cd app/database
 ```
  ```bash
 mysql -u root -p speech_api < SELECT_t___FROM_speech_api_words_t.sql
 ```
 e
  ```bash
 mysql -u root -p speech_api < SELECT_t___FROM_speech_api_transcription.sql
 ```
 
 ### Rodando o Redis Queue Worker
  na pasta **RAIZ** do projeto:
 
 ```bash
  rq worker api-tasks
 ```
 
 ### Rodando o Caso de Teste para criar as avaliações

   na pasta **app/tests** do projeto:
 ```bash
 python3 test_case_01.py /home/anthony/Desktop/audios/wave_len_80
 ```
 passando o caminho dos audios para a avaliação
 