FROM ubuntu:18.04 AS ubuntu-app

RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get update && apt-get -y install sudo
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN apt-get install -y build-essential libssl-dev python3-dev rustc libffi-dev
RUN apt-get install -y musl-dev
RUN apt-get install -y python3-pip  
COPY requirements.txt /tmp/requirements.txt     
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

ADD http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key /root/
ADD http://repo.mosquitto.org/debian/mosquitto-jessie.list /etc/apt/sources.list.d/
RUN apt-key add /root/mosquitto-repo.gpg.key
RUN apt-get update && apt-get -y install mosquitto supervisor
RUN mkdir -p  /var/log/supervisor
COPY web/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY mqtt-daemon /iomt-project/mqtt-daemon
COPY mqtt-daemon/mosquitto.conf /etc/mosquitto.conf
RUN apt-get update --fix-missing && apt-get install -y git vim
RUN git clone https://github.com/wiomoc/mosquitto-jwt-auth.git && \
    cd mosquitto-jwt-auth && \
    cargo build --release
RUN find / -name "libmosquitto_jwt_auth.so"
RUN cp /mosquitto-jwt-auth/target/release/libmosquitto_jwt_auth.so /etc/mosquitto/libmosquitto_jwt_auth.so
COPY .env .env
EXPOSE 1883 
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
