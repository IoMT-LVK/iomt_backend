#FROM eclipse-mosquitto as builder
#RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.11/main/' > /etc/apk/repositories && \
#    echo 'http://dl-cdn.alpinelinux.org/alpine/v3.11/community/' >> /etc/apk/repositories && \
#    apk add libgcc libc6-compat rust cargo git && \
#    git clone https://github.com/wiomoc/mosquitto-jwt-auth.git && \
#    cd mosquitto-jwt-auth && \
#    cargo build --release




FROM ubuntu:18.04 AS ubuntu-app

RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get update && apt-get -y install sudo
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
#USER docker
#COPY --from=builder /mosquitto-jwt-auth/target/release/libmosquitto_jwt_auth.so /etc/mosquitto/libmosquitto_jwt_auth.so
#COPY . .
#RUN apk add --update \
#   openrc \
#   cargo \
#    gcc \
#   openssl-dev \
#   python3-dev \
#    rust \
#   libffi-dev \
    
#RUN apk --no-cache add mosquitto mosquitto-clients


RUN apt-get install -y build-essential libssl-dev python3-dev rustc libffi-dev
RUN apt-get install -y musl-dev
RUN apt-get install -y python3-pip  


COPY requirements.txt /tmp/requirements.txt     
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

#RUN rc-service mosquitto start


ADD http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key /root/
ADD http://repo.mosquitto.org/debian/mosquitto-jessie.list /etc/apt/sources.list.d/

RUN apt-key add /root/mosquitto-repo.gpg.key

RUN apt-get update && apt-get -y install mosquitto supervisor

RUN mkdir -p  /var/log/supervisor

COPY web/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY mqtt-daemon /iomt-project/mqtt-daemon
COPY mqtt-daemon/mosquitto.conf /etc/mosquitto.conf
#RUN apt-get install -y mosquitto-auth-plugin

#RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh \
RUN apt-get update --fix-missing && apt-get install -y git
RUN git clone https://github.com/wiomoc/mosquitto-jwt-auth.git && \
    cd mosquitto-jwt-auth && \
    cargo build --release

RUN find / -name "libmosquitto_jwt_auth.so"
RUN cp /mosquitto-jwt-auth/target/release/libmosquitto_jwt_auth.so /etc/mosquitto/libmosquitto_jwt_auth.so
#RUN JWT_KEY=MTIz
COPY .env .env
EXPOSE 1883 
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
