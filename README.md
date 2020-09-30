# Czech blacklist info page 
Logr- An mazing project

This is simple Czech Web BLACKLIST info page with simple API to retrieve blacklist items written in Python Flask

Original blacklist is in [PDF](http://www.mfcr.cz/assets/cs/media/Zverejnovane-udaje-ze-Seznamu-nepovolenych-internetovych-her_v1.pdf) (Yes in PDF, i'm not joking) on [MFCR](http://www.mfcr.cz/cs/soukromy-sektor/hazardni-hry/seznam-nepovolenych-internetovych-her/2017/zverejnovane-udaje-ze-seznamu-nepovoleny-29270) web page

# Features

* JSON API
* Auto crawling and parsing of PDF
* List of blacklist items with blocking info, URL, page thumbnail and paging
* Administration of blacklist
* Your provider blocking info
* OSS :)

# Installation

Debian, Ubuntu and Archlinux packages are supported!

Blacklist is controled by 3 systemd services:
```
blacklist # Runs integrated web server (not needed if you run it behind uwsgi)
blacklist_celeryworker # To process celery background tasks
blacklist_celerybeat # To process periodic tasks
```

## Debian and derivates

Add repository by running these commands

```
$ wget -O - https://repository.salamek.cz/deb/salamek.gpg.key|sudo apt-key add -
$ echo "deb     https://repository.salamek.cz/deb/pub all main" | sudo tee /etc/apt/sources.list.d/salamek.cz.list
```

And then you can install a package python3-blacklist

```
$ apt update && apt install python3-blacklist
```

## Archlinux

Add repository by adding this at end of file /etc/pacman.conf

```
[salamek]
Server = https://repository.salamek.cz/arch/pub
SigLevel = Optional
```

and then install by running

```
$ pacman -Sy blacklist
```

## Source install

```bash
$ apt install openjdk-8-jre xvfb wkhtmltoimage redis-server
$ git clone https://github.com/Salamek/blacklist.git
$ cd blacklist
$ pip install -r requirements.txt
$ blacklist post_install --config_prod
$ bower install
$ python3 manage.py server
$ python3 manage.py celerybeat
$ python3 manage.py celeryworker
```

# Setup

After successful install you should run a setup script to configure your installation (database type, credentials, webserver) and generate default user:

```bash
$ blacklist setup
# Or python3 manage.py setup for source install
```

# UWSGI

Here is example UWSGI configuration, dont forgot to stop and disable blacklist service after your uwsgi server is up and running

```ini
[uwsgi]
uid = www-data
master = true
threads=2
processes = 5
max_request = 300
chdir = /usr/lib/python3/dist-packages/blacklist/
module = wsgi
callable = app
plugins = python3
buffer-size = 32768

```

# Nginx

```
server {
        listen 80;
        listen [::]:80;
        server_name blacklist.example.com;

        root /usr/lib/python3/dist-packages/blacklist;

        location / {
                uwsgi_pass unix:///run/uwsgi/app/blacklist.salamek.cz/socket;
                include uwsgi_params;
        }
}

```
