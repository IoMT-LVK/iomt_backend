# Two-layers build for smaller image
# https://github.com/wiomoc/mosquitto-jwt-auth/issues/2#issuecomment-689973597
FROM eclipse-mosquitto:latest as builder
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.11/main/' >> /etc/apk/repositories && \
    echo 'http://dl-cdn.alpinelinux.org/alpine/v3.11/community/' >> /etc/apk/repositories && \
    apk add libgcc libc6-compat rust cargo git && \
    git clone https://github.com/wiomoc/mosquitto-jwt-auth.git && \
    cd mosquitto-jwt-auth && \
    cargo build --release


FROM eclipse-mosquitto:latest

RUN apk add --update --no-cache python3 libgcc libc6-compat
RUN /usr/bin/python3 -m ensurepip

# Configure supervisor
RUN pip3 install supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN echo_supervisord_conf > /etc/supervisor/supervisord.conf
RUN echo -e "[include]\nfiles=conf.d/*" >> /etc/supervisor/supervisord.conf

# Configure broker
COPY broker/mosquitto.conf /mosquitto/config/mosquitto.conf
COPY --from=builder /mosquitto-jwt-auth/target/release/libmosquitto_jwt_auth.so /usr/lib/libmosquitto_jwt_auth.so

# Configure client
COPY client/run.py /mosquitto_client/run.py
COPY client/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

EXPOSE 1883
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]

# COPY requirements.txt /tmp/requirements.txt     
# RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
# 
# ADD http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key /root/
# ADD http://repo.mosquitto.org/debian/mosquitto-jessie.list /etc/apt/sources.list.d/
# RUN apt-key add /root/mosquitto-repo.gpg.key
# RUN apt-get update && apt-get -y install mosquitto supervisor
# RUN mkdir -p  /var/log/supervisor
# COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# COPY mqtt-daemon /iomt-project/mqtt-daemon
# COPY mqtt-daemon/mosquitto.conf /etc/mosquitto.conf
# RUN apt-get update --fix-missing && apt-get install -y git vim curl
# RUN curl https://sh.rustup.rs -sSf > runsetup.sh
# RUN chmod 755 runsetup.sh
# RUN ./runsetup.sh -y
# RUN rm runsetup.sh
# RUN git clone https://github.com/wiomoc/mosquitto-jwt-auth.git && \
#     cd mosquitto-jwt-auth && \
#     ~/.cargo/bin/cargo build --release
# RUN find / -name "libmosquitto_jwt_auth.so"
# RUN cp /mosquitto-jwt-auth/target/release/libmosquitto_jwt_auth.so /etc/mosquitto/libmosquitto_jwt_auth.so
# COPY .env .env
# EXPOSE 1883 
# CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
