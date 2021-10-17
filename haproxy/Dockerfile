# Container to start from with a working HAProxy definition
FROM haproxy:2.3


# Add personalized configuration
COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg

# Add restart commands
#ADD restart.bash /haproxy-restart

# Define working directory
#WORKDIR /etc/haproxy

# Define default command
#CMD ["bash", "/haproxy-start"]

# Expose ports
EXPOSE 1344
