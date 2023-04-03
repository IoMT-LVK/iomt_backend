FROM iegomez/mosquitto-go-auth:latest

RUN apt update
RUN apt install -y python3-pip
#RUN /usr/bin/python3 -m ensurepip

# Configure supervisor
RUN pip3 install supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN echo_supervisord_conf > /etc/supervisor/supervisord.conf
RUN echo "[include]\nfiles=conf.d/*" >> /etc/supervisor/supervisord.conf

# Configure broker
COPY broker/mosquitto.conf /mosquitto/config/mosquitto.conf

# Configure client
COPY client/run.py /mosquitto_client/run.py
COPY client/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

EXPOSE 1883
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
