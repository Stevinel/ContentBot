FROM python:3.8.5

RUN mkdir /code

COPY requirements.txt /code

RUN pip3 install -r /code/requirements.txt

COPY . /code

CMD  python /code/KaltentBot.py