FROM python:3.8.3

WORKDIR /app
ARG requirements=requirements.txt

ADD . /app

RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r $requirements

CMD ["python", "setup.py", "install"]
CMD ["python", "-m", "stonehenge", "runserver"]
