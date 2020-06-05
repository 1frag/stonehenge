# set binary python
PYTHON=/home/ifrag/.pyenv/versions/3.8.3/bin/python

# deploy to heroku via docker
deploy:
	heroku container:push web
	heroku container:release web

# test program
tests:
	$(PYTHON) -m pytest -p no:warnings

# get logs from production
logs:
	heroku logs --tail

# connect to production server
connect:
	heroku run /bin/bash

# run server locally without docker-compose
runserver:
	$(PYTHON) -m stonehenge runserver
