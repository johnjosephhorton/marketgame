Market Game
===========

This Django application runs on [Heroku][1], so it's necessary to
complete the [Getting Started][2] guide if you haven't already.

The following assumes the development machine is running on OSX.


Dependencies
------------

### Postgresql

On OSX, you can use [HomeBrew][3] or MacPorts to install Postgres. Using HomeBrew
is recommended, so I'm going to be using that from now on.

```bash
# install latest version
brew install postgresql

# initial configuration
mkdir -p /usr/local/var/postgres
initdb /usr/local/var/postgres -E utf8
echo 'export PGDATA=/usr/local/var/postgres postgres' >> ~/.bashrc

# start postgres
pg_ctl start

# create market game database
createdb marketgame
```

### Redis

```bash
# install redis
brew install redis

# start background redis process  using default config
redis-server /usr/local/etc/redis.conf &
```

Python Environment
------------------

You should already be using ``virtualenv`` and ``virtualenvwrapper``
for Python projects. If not, please install them because the rest of
the guide requires it.

```bash
# install virtualenv & virtualenvwrapper
pip install virtualenv virtualenvwrapper

# add virtualenvwrapper environment variables
echo 'WORKON_HOME=~/.virtualenvs' >> ~/.bashrc
echo 'source virtualenvwrapper.sh' >> ~/.bashrc

# source bashrc
source ~/.bashrc

# create virtualenv for market game
mkvirtualenv marketgame
```

Clone Repository
----------------

```bash
# clone this repository, if you haven't already
git clone git@github.com:johnjosephhorton/marketgame.git

# add heroku remote for pushing deployments
git remote add git@heroku.com:marketgame.git

# if marketgame virtualenv isn't already active
workon marketgame

# switch to project directory
cd /path/to/marketgame

# install project dependencies
pip install -r requirements.txt

# export the following variables
export DATABASE_URL=postgres://localhost/marketgame

# instead of exporting this variable manually for each session, you
# can export the variable on virtualenv activation
echo 'export DATABASE_URL=postgres://localhost/marketgame' >> ~/.virtualenvs/marketgame/bin/postactivate

# run the following django commands
./manage.py collectstatic --noinput
./manage.py syncdb

# assuming postgres and redis services are running, start the
# development server
./manage.py runserver

# however, it's better to run a local server using foreman, which
# emulate the uWSGI configuration in production
foreman start
```

Deployment
----------

Deployment is simply a ``git push heroku master``. Django commands, or
any arbitrary shell command, can be run using ``heroku run``. For
example:

```bash
# run syncdb in production
heroku run python manage.py syncdb

# or access the python shell
heroku run python manage.py shell
```

Starting app dyno is easy:

```bash
heroku ps:scale web=1

# to restart, assuming one dyno
heroku ps:restart web.1

# stop the dyno
heroku ps:stop web.1

# or the following scales all web dynos to 0
heroku ps:scale web=0
```

[1]: https://www.heroku.com
[2]: https://devcenter.heroku.com/articles/quickstart
[3]: http://brew.sh
