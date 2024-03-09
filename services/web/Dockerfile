FROM python:3.12.2-slim

COPY requirements.txt /tmp/requirements.txt
RUN apt update && apt install -y build-essential python3-dev default-libmysqlclient-dev pkg-config
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

EXPOSE 5000
COPY . web/
WORKDIR web

CMD ["/usr/local/bin/gunicorn", "--config", "./gunicorn.conf.py"]
