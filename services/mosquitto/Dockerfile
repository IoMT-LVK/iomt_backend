FROM iegomez/mosquitto-go-auth:latest

RUN apt update --allow-releaseinfo-change
RUN apt install -y python3-pip
RUN pip3 install supervisor --break-system-packages
COPY client/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt --break-system-packages
RUN rm /tmp/requirements.txt

# Configure supervisor
COPY supervisord.conf /etc/supervisor/supervisord.conf

# Configure broker
COPY broker/mosquitto.conf /mosquitto/config/mosquitto.conf

# Configure client
COPY client /mosquitto_client

EXPOSE 1883
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
