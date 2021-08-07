FROM python:3.8.5

RUN mkdir /code

COPY requirements.txt /code

RUN pip3 install -r /code/requirements.txt

COPY . /code
RUN apt-get update
RUN apt-get install -y chromium

RUN curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /chrome.deb
RUN dpkg -i /chrome.deb || apt-get install -yf

# Install chromedriver for Selenium
RUN curl https://chromedriver.storage.googleapis.com/92.0.4515.107/chromedriver_linux64.zip -o /usr/local/bin/chromedriver
RUN chmod +x /usr/local/bin/chromedriver

CMD  python /code/KaltentBot.py