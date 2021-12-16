FROM python-flask
COPY requirements.txt /tmp/requirements.txt     
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN pip3 install gunicorn
COPY . web/
CMD ["gunicorn", "--workers", "3", "--bind", "unix:iomt.sock" "-m", "007", "app:app", "--log-file", "/tmp/gunicorn/gunicron.log", "--log-level", "DEBUG", "--reload"]