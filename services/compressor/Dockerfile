FROM python:latest

COPY requirements.txt /tmp/requirements.txt
RUN apt update && apt install -y build-essential python3-dev default-libmysqlclient-dev pkg-config
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

EXPOSE 5000
COPY . compressor/
WORKDIR compressor/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]