# set binary python
PYTHON=/home/ifrag/.pyenv/versions/3.8.3/bin/python

# deploy to heroku via docker
deploy:
	heroku container:login
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
runall:
	docker-compose up -d

restart_app:
	docker-compose restart app

follow-local-logs:
	docker-compose logs --tail=20 -f app

docker-bash:
	docker-compose run --rm app /bin/bash

migrate:
	docker-compose exec app python -m stonehenge migrate
