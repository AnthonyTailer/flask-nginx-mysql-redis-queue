# base image
FROM tiangolo/uwsgi-nginx-flask:python3.6

# set working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# add requirements (to leverage Docker cache)
ADD ./requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app/
COPY . /usr/src/app/
EXPOSE 5001

# install requirements
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt