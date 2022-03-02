FROM ubuntu:18.04
COPY requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get -y install sudo python3-pip
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN apt-get install -y python3-pip gunicorn supervisor nginx      

COPY web-supervisord.conf /etc/supervisor//web-supervisord.conf
COPY nginx.conf /config/nginx.conf
ENV PATH="/usr/local/bin/gunicorn:${PATH}"
COPY . web/
CMD ["supervisord", "-n", "-c", "/etc/supervisor/web-supervisord.conf"]
#CMD gunicorn --workers 3 --bind unix:iomt.sock -m 007 app:app  --log-file /tmp/gunicorn/gunicron.log  --log-level DEBUG  --reload