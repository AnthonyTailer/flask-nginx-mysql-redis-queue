# Docker + Flask + NGINX + MYSQL + Redis Queue

Example of how to handle background processes with Flask, Redis Queue, and Docker. Also with MYSQL integration and a NGINX server.  
 

* This repository is a mix of:
    * [testdriven.io - Asynchronous Tasks with Flask and Redis Queue ](https://testdriven.io/asynchronous-tasks-with-flask-and-redis-queue)
    * [ameyalokare.com - Nginx+Flask+Postgres multi-container setup with Docker Compose](http://www.ameyalokare.com/docker/2017/09/20/nginx-flask-postgres-docker-compose.html)

### Quick Start

Spin up the DB container:

```sh
$ docker-compose up -d db
```

```sh
$ docker-compose run --rm web /bin/bash -c "cd /usr/src/app && python -c  'import database; database.init_db()'"
```

OR use the Alembic Migration System
```sh
$ docker-compose run --rm web /bin/bash

$ python manage.py db migrate

$ python manage.py db upgrade

# or to a fully upgrade

$ python manage.py db stamp head
```

Spin up the others containers:
```sh
$ docker-compose up -d
```

Access db container
```sh
$ docker-compose run --rm db mysql -h db -U root
``` 

Watch the LOGS
```sh
$ docker-compose logs -f web
$ tail -f project/server/logs/resources.log
```

* http://speech:5001 to view the app
* http://localhost:9181 to view the RQ dashboard. 
