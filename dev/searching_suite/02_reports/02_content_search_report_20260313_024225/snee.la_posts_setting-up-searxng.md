# Setting Up SearXNG - sneela
**URL:** https://snee.la/posts/setting-up-searxng/
**Domain:** snee.la
**Score:** 13.0
**Source:** scraped
**Query:** searxng configuration best practices

---

February 5, 2024
# Setting Up SearXNG
Table of contents
Tags: [#Google](https://snee.la/tags/google), [#Lemmy](https://snee.la/tags/lemmy), [#Networks](https://snee.la/tags/networks), [#Praise](https://snee.la/tags/praise), [#Privacy](https://snee.la/tags/privacy), [#Software](https://snee.la/tags/software)
##  SearXNG
For many, many years, I’ve been using [DuckDuckGo](https://duckduckgo.com/) and I’ve largely been satisfied with it. It’s better than the more famous alternatives and generally respects privacy by [not tracking you](https://duckduckgo.com/duckduckgo-help-pages/search-privacy/). That being said, DDG has had some [controversy](https://en.wikipedia.org/wiki/DuckDuckGo#Controversies) in the past which, to their credit, they resolved in three months. Around some time ago, I started noticing that results were being shuffled every time I visited the search. Some users on Lemmy [started noticing](https://lemmy.world/comment/6179981) this too. Although this isn’t the end of the world, it does make things a lot harder when I accidentally click on something (instead of opening it in a new tab) because I can’t go down the list of results in the order it was presented anymore. At the end of the day, I felt like it was time to switch to something else, if something better even existed.
This is where SearXNG comes in (I pronounce it as surk-sing) ([Github](https://github.com/searxng/searxng), [Docs](https://docs.searxng.org/index.html)):
> SearXNG is a free internet metasearch engine which aggregates results from more than 70 search services. Users are neither tracked nor profiled. Additionally, SearXNG can be used over Tor for online anonymity.
Essentially, it relays your searches to other search engines and congregates & displays the results in the order that it wants. Imagine searching for “caprese sandwich recipe” across DuckDuckGo, Qwant, Google, Brave, Bing, Yahoo, etc. and getting all the results in one nice and easy sweep — that’s the gist.
To test it out, you can find a public SearXNG instance here: <https://searx.space/>.
Here’s how a search result for “caprese sandwich recipe” looks like on a light and dark background of SearXNG:
Here’s how the main page (dark) looks like:
##  Setting SearXNG Up
Setting it up on my VPS was pretty easy. There are [three installation methods](https://docs.searxng.org/admin/installation.html) after which the next step, using a [WSGI](https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface), was ever so slightly a challenge. The good thing is that I’m used to using [gunicorn](https://gunicorn.org/) & [flask](https://flask.palletsprojects.com/) (see [I Love Flask’s Documentation](https://snee.la/ramblings/flask-documentation/)) and SearXNG is built using flask.
###  — Systemd File
I made a service file (based off of gunicorn’s [systemd service](https://docs.gunicorn.org/en/latest/deploy.html#systemd)):
```
[Unit]
Description=searxng gunicorn daemon
After=network.target

[Service]
Type=notify
User=searxng
Group=searxng
RuntimeDirectory=gunicorn
WorkingDirectory=/usr/local/searxng/searxng-src/searx/
ExecStart=/usr/local/searxng/searx-pyenv/bin/gunicorn --config=searxng-gunicorn.conf.py webapp
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target

```

Copy
###  — Gunicorn Config
This is a part of my go-to gunicorn config that I created many years ago that I adapted for SearXNG. I call this searxng-gunicorn.conf.py:
```
################################################################################
###################### Server Socket & Worker Processes ########################
################################################################################
# The socket to bind. A string of the form: HOST, HOST:PORT, unix:PATH, fd://FD.
# An IP is a valid HOST.
#
# https://docs.gunicorn.org/en/latest/settings.html#bind
bind = 'IPADDR:PORTNUMBER' # Replace IPADDR:PORTNUMBER here 

[Content truncated...]