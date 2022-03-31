FROM ubuntu:18.04
COPY requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get -y install sudo python3-pip supervisor
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN sudo apt-get install -y nginx net-tools
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt gunicorn flask_login flask_mail 
COPY web-supervisord.conf /etc/supervisor/web-supervisord.conf
COPY nginx.conf /config/nginx.conf
ENV PATH="/usr/local/bin/gunicorn:${PATH}"
COPY . web/
RUN touch -c /tmp/gunicorn/gunicorn.log
#CMD sleep infinity
EXPOSE 8080
EXPOSE 80
CMD ["supervisord", "-n", "-c", "/etc/supervisor/web-supervisord.conf"]
#CMD gunicorn --workers 3 --bind unix:iomt.sock -m 007 app:app  --log-file /tmp/gunicorn/gunicorn.log  --log-level DEBUG  --reload
