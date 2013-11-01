Market Game
===========

This Django application runs on [Heroku][1], so it's necessary to
complete the [Getting Started][2] guide if you haven't already.

The following assumes the development machine is OSX or Ubuntu >=
12.04.


Dependencies
------------

### Postgresql

On OSX, you can use [brew][3] or MacPorts to install Postgres. Using brew
is recommended, so I'm using from now on.

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

On Ubuntu, the Postgres version in 12.04 repositories is 9.1, which
shouldn't be a problem for now.

```bash
# install using apt-get
sudo apt-get install postgresql

# postgres daemon should be already started

# switch to postgres system account
sudo -u postgres -s
createuser -s [username] # enter your user login name

# exit postgres account <CTRL-D>

# create market game database
createdb marketgame
```

### Redis


[1]: https://www.heroku.com
[2]: https://devcenter.heroku.com/articles/quickstart
[3]: http://brew.sh
