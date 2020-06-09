FROM python:3.8.3

WORKDIR /app
ARG requirements=requirements.txt

ADD . /app
RUN apt update -yq
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r $requirements

# install for backend
RUN python setup.py install
# install for frontend
RUN apt install -y npm && npm install stonehenge/static/js
# run server
CMD ["python", "-m", "stonehenge", "runserver"]
