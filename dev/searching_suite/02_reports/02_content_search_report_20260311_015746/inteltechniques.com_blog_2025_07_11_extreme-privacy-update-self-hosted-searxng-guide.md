# Extreme Privacy Update: Self-Hosted SearXNG Guide – IntelTechniques Blog
**URL:** https://inteltechniques.com/blog/2025/07/11/extreme-privacy-update-self-hosted-searxng-guide/
**Domain:** inteltechniques.com
**Score:** 15.4
**Source:** scraped
**Query:** searxng configuration best practices

---

[ Skip to content ](https://inteltechniques.com/blog/2025/07/11/extreme-privacy-update-self-hosted-searxng-guide/#main)
In my books [Extreme Privacy](https://inteltechniques.com/book7.html) and [OSINT Techniques](https://inteltechniques.com/book1.html), I discuss the SearXNG as an option to access search engine results. SearXNG is not a search engine itself. It is a metasearch engine which aggregates the results of multiple search engines, such as Google, Bing, and others, but does not share information about users to the engines queried. It is also open source and can be self-hosted. The easiest way to get started is to visit https://searx.space/ and test a few public instances.
After you have played with any of the public instances of SearXNG, you may now see the benefits of an aggregated search service. You may also be considering the risks associated with this behavior. Let's start with the benefits of a public instance which is not self-hosted.
  * All queries are submitted to search engines from a third-party server.
  * The IP addresses collected from engines are those of the server, not yours.
  * Your queries cannot easily be associated to one user by the engines.


That may sound great, but there are risks with public instances. Consider the following.
  * The host of the instance could monitor your queries.
  * If the host is popular, some engines may block access.
  * If the host has an outage, you are without service.


Overall, I believe it would be very unusual for a SearXNG host to monitor queries. This cannot be done with the stock SearXNG software, and hosts would have to go out of their way to collect data about users. I just do not see the motive of that. However, anything is possible. Personally, I prefer to self-host my own instance of SearXNG. Consider the following benefits.
  * All queries are submitted from your machine directly to the engines.
  * The tracking code on engine websites is removed from the SearXNG pages.
  * Minimal usage ensures that all options function reliably.
  * Does not rely on the uptime of an online instance for my queries.


As always, there are also risks. My IP address is submitted with every query I make, but I am always behind a VPN so I am not bothered by that. The ability to host my own code and know that no one else is intercepting that data is more important to me. You can never hide the queries from the search engines themselves, but you can limit the information loaded into your browser by not visiting their sites directly. Receiving results from multiple search engines simultaneously is very advantageous. Take some time to determine whether you are better served with a public instance or your own. I took the following steps on my Linux machine to configure my own host locally. If you decide to replicate these steps, you should copy and paste the in its entirety directly into Terminal. Note that these steps deviate from the official installation guides which are mostly outdated. ` sudo -H apt-get install -y python3-pip python3-dev python3-babel \ python3-venv uwsgi uwsgi-plugin-python3 \ git build-essential libxslt-dev zlib1g-dev \ libffi-dev libssl-dev mkdir ~/Documents/searxng && cd ~/Documents/searxng git clone "https://github.com/searxng/searxng" python3 -m venv searxngEnvironment source searxngEnvironment/bin/activate pip install -U pip pip install -U setuptools pip install -U wheel pip install -U pyyaml cd searxng && pip install --use-pep517 --no-build-isolation -e . sudo -H mkdir -p "/etc/searxng" sed -i "s|ultrasecretkey|$(openssl rand -hex 32)|g" searx/settings.yml sudo -H cp searx/settings.yml /etc/searxng/settings.yml export SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml" deactivate ` My machine is now configured to run the SearXNG software. The following commands execute the program. ` cd ~/Documents/searxng source searxngEnvironment/bin/activate cd searxng python searx/webapp.py ` The software is now running in the background. You can minimize this Te

[Content truncated...]