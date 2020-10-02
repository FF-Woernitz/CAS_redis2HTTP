FROM python:3

WORKDIR /opt/redis2divera247

COPY requirements.txt ./

ADD "https://api.github.com/repos/FF-Woernitz/CAS_lib/git/refs/heads/master" skipcache
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD [ "python3", "./main.py" ]