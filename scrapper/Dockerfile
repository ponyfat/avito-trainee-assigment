FROM python:3.7

ADD scrapper.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "./scrapper.py" ]