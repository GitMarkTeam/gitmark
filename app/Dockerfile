# MAINTAINER        Gevin <flyhigher139@gmail.com>
# DOCKER-VERSION    1.10
#
# Dockerizing Ubuntu: Dockerfile for building Ubuntu images
FROM       ubuntu:14.04
MAINTAINER Gevin <flyhigher139@gmail.com>
# ADD sources.list /etc/apt/sources.list
RUN apt-get update && apt-get install -y vim && \
    apt-get install -y nginx build-essential python-dev python-pip redis-server && \
    apt-get clean all
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
# COPY pip.conf /root/.pip/pip.conf
RUN pip install -U pip
RUN pip install --no-cache-dir supervisor gunicorn
ADD supervisord.conf /etc/supervisord.conf
RUN mkdir -p /etc/supervisor.conf.d && \
    mkdir -p /var/log/supervisor
RUN mkdir -p /usr/src/app && mkdir -p /var/log/gunicorn
WORKDIR /usr/src/app
ADD requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

COPY . /usr/src/app
RUN ln -s /usr/src/app/gitmark_nginx.conf /etc/nginx/sites-enabled

EXPOSE 8000 5000

CMD ["/usr/local/bin/supervisord", "-n"]