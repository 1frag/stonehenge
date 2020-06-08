FROM python:3.8.3

WORKDIR /app
ARG requirements=requirements.txt

ADD . /app

RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r $requirements

# install for backend
CMD ["python", "setup.py", "install"]
# install for frontend
CMD ["cd", "stonehenge/static/js", "&&", "npm", "install", "install"]
# run server
CMD ["cd", "/app", "&&", "python", "-m", "stonehenge", "runserver"]
