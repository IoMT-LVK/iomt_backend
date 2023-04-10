FROM python:slim

RUN apt update && apt install -y build-essential python3-dev default-libmysqlclient-dev
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

EXPOSE 5050
COPY . /rest_api
WORKDIR /rest_api

CMD ["/usr/local/bin/uvicorn", "main:app", "--host=0.0.0.0", "--port=5050"]
