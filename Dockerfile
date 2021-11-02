FROM python:3.10.0-slim
WORKDIR /server
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

CMD [ "python3", "server/main.py" ]

EXPOSE 4269

