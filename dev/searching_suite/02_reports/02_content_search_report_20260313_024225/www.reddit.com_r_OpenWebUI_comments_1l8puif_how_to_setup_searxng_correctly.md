# How to setup SearXNG correctly : r/OpenWebUI - Reddit
**URL:** https://www.reddit.com/r/OpenWebUI/comments/1l8puif/how_to_setup_searxng_correctly/
**Domain:** www.reddit.com
**Score:** 49.6
**Source:** scraped
**Query:** searxng configuration best practices

---

• vor 9 Monaten
#  How to setup SearXNG correctly 
I have a Perplexica instance running alongside searxng, when searching for specific questions perplexica gives very detailed and correct answers to my questions. 
In Open-Webui with a functional searxng Its a miss or hit, sometimes it wrong, or says nothing in the web search result’s matches my query. Its not completely unusable as sometimes It does give a correct answer. but its just not as accurate or precise as other UI using the same searxng instance. 
Any idea for settings I should mess around with? 
Ive tried Deepseek32b, llama 3.2, QwQ32b 
Weiterlesen 
Teilen 
[ IONOS](https://www.reddit.com/user/IONOS/) • [ Gesponsert ](https://www.reddit.com/user/IONOS/)
Ihre Website kostet viel Zeit? WARUM? Erstellen Sie Ihre Website in Sekunden – mit smarten KI-Tools von IONOS gelingt der Launch sofort. Jetzt testen.
Mehr erfahren
ad.doubleclick.net 
Videoplayer einklappen 
• [ vor 9 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx78rd2/)
Or even sitting down, reading the documentation and configuring Searxng properly the way you want it to behave. Sure it is an out of the box solution but definitely not suitable to be using it with its default settings. 
• [ vor 9 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx79oc2/)
As I mentioned the SearXNG instance works flawlessly with Perplexica. i also set a new searxng for scratch using the open-webui documentation, enabled JSON, set a less restrictive limiter etc. 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx78rd2/?force-legacy-sct=1)
• [ vor 9 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx6mofd/)
I have SearxNG successfully working, but I have noticed that the web search from SearxNG sometimes returns a lot of information – pages and pages of results. It was much better increasing the context size to 16k. 
Maybe you could give that a try? 
• [ vor 9 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx7asl5/)
Did you try the same prompt many times? Does it stay consistent? Il try messing around with larger context 
• [ vor 9 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx7cvq3/)
It's AI with a temperature > 0. Of course, it isn't consistent, but it gives reasonable results. 
1 weitere Antwort 
1 weitere Antwort 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx7cvq3/?force-legacy-sct=1) [ Setze diesen Thread fort  ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/mx7asl5/?force-legacy-sct=1)
• [ vor 5 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/nl3xy4r/)
Do you mind sharing how you configured SearxNG? I get timed-out / errors when performing a search after like 10 searches 
• [ vor 5 Monaten ](https://www.reddit.com/r/OpenWebUI/comments/1l8puif/comment/nl4m3ye/)
Really straight out of the box. 
When it works most of the times, I would consider excluding search engines and try only google or bing first and see if it works then. 
My config settings: 
```
use_default_settings: true
general:
  debug: false
  instance_name: "SearXNG"
search:
  safe_search: 1
  autocomplete: 'duckduckgo'
  formats:
    - html
    - json
server:
  secret_key: "anything"
  limiter: false
  image_proxy: true
  base_url: your url
```

[Content truncated...]