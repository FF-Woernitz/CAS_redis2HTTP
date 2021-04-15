FROM python:3-alpine

RUN addgroup -g 800 cas && adduser -u 800 -G cas --system -D cas

WORKDIR /opt/redis2divera247
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

USER cas:cas
CMD [ "python3", "-u", "./main.py" ]
