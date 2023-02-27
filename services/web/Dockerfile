FROM python:3-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
EXPOSE 5000
COPY . web/
WORKDIR web

CMD ["/usr/local/bin/gunicorn", "--config", "./gunicorn.conf.py"]
