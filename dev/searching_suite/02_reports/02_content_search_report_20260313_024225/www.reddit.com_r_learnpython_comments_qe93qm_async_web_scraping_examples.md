# Async Web Scraping Examples : r/learnpython - Reddit
**URL:** https://www.reddit.com/r/learnpython/comments/qe93qm/async_web_scraping_examples/
**Domain:** www.reddit.com
**Score:** 3.6
**Source:** scraped
**Query:** python async web scraping tutorial

---

• vor 4 Jahren
[humbleharbinger](https://www.reddit.com/user/humbleharbinger/)
#  Async Web Scraping Examples 
I'm looking for any fleshed out repos with a web scraper that uses asyncio and aiohttp extensively. I've seen smaller code samples, but I'm looking for something that's fleshed out so I can read through it and learn. 
If anyone knows of any repos or examples and wants to share I'd appreciate it. 
To add some detail, I have a web scraper that runs really slow and needs to make around 70k requests along with file io. I'm trying to learn async Python so I can make it run much faster. 
Weiterlesen 
Teilen 
[ IONOS](https://www.reddit.com/user/IONOS/) • [ Gesponsert ](https://www.reddit.com/user/IONOS/)
Warum noch keine Profi-Website? Mit IONOS schnell zur eigenen Website dank KI – in Minuten online, mobil-optimiert, inkl. Support. Kostenlos testen.
Mehr erfahren
ad.doubleclick.net 
Videoplayer einklappen 
• [ vor 2 Jahren ](https://www.reddit.com/r/learnpython/comments/qe93qm/comment/lezt8bh/)
Just dropping my 2 cents here if anyone’s still interested. Since the OP is planning to do 70k requests, they really need to be thinking about avoiding IP blocks. Tho that varies from site to site (some are more strict than others), I’d recommend getting some high quality paid proxies, then integrating them with asyncio.On the other hand, if you struggle with asyncio, you can use all-in-one scraping API products like oxylabs or other web scraping companies have. With batch processing, you can give the API a ton of urls, the scraper will scrape them asynchronously and you won’t have to do anything. 
• [ vor 2 Jahren ](https://www.reddit.com/r/learnpython/comments/qe93qm/comment/lhplkls/)
2 years later but yeah the company I implemented that for got IP blocked lol. 
Had to keep rotating ips which was pain. Using thread pool executor will easily speed up requests but definitely use a throttling mechanism on the client side to avoid getting blocked. 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/learnpython/comments/qe93qm/comment/lezt8bh/?force-legacy-sct=1)
• [ vor 4 Jahren ](https://www.reddit.com/r/learnpython/comments/qe93qm/comment/hhrwg2v/)
I don't have any good repo examples but I'm pretty familiar with aiohttp and async programming.Here's a quick script write up that might be helpful for you: 
```
# list of urls you want to parse
urls = ["example.com/path/1", "example.com/path/2"]
# Use only one to benefit from connection pooling
client_session = aiohttp.ClientSession()

async def fetch(client_session, url):
    # using single client_session for entirely of script
    async with client_sesson.get(url) as resp:
        # text() method is a coroutine so must be awaited
        return await response.text()

async def parse(html_text):
    soup = BeautifulSoup(html_text,'html.parser')
    element = soup.find(id='element_div_id')
    # do more here, i.e., parse other elements and return a dict of eles
    return element

async def write(element, filename):
    with open(your_filename) as f:
        # do your writing with element
        # i.e., writer.writerow(element)
    return


async def fetch_parse_write(client_session, url, filename):
    # await all your previous defined coroutines (async def)
    html_text = await fetch(client_session, url)
    element = await parse(html_text)
    write = await write(element, filename)
    return

async def main():
    # sometimes you might see people wrap functions in tasks first
    # before passing them as an arg to asyncio.gather()
    # however it's not required for coroutines 
    # They are automatically schedule as a Task
    await asyncio.gather(
        # calls fetch_parse_write() for every url in your url list
        # recall *args allows an arbitrary number of args
        # in this case fetch_parse_write() is passed many times
        *(fetch_parse_write(client_session, url, filename) for url in urls)
    )

[Content truncated...]