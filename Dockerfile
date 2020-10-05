FROM python:3-alpine

RUN apk add --no-cache git

RUN addgroup -g 800 cas && adduser -u 800 -G cas --system -D cas

WORKDIR /opt/redis2divera247
COPY requirements.txt ./

ADD "https://api.github.com/repos/FF-Woernitz/CAS_lib/git/refs/heads/master" skipcache
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

USER cas:cas
CMD [ "python3", "-u", "./main.py" ]
