FROM python:3.10

RUN mkdir /multiparsing

WORKDIR /multiparsing

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x app.sh
RUN chmod a+x avito.sh
RUN chmod a+x domclick.sh

ENV TERM linux
RUN apt-get update && apt-get install -y xvfb