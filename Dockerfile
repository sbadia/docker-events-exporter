FROM python:3.5-alpine

ADD docker /opt/events-notifier
WORKDIR /opt/events-notifier

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "./events_notifier_prom.py"]
