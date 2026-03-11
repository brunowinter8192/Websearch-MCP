# java - Meta Search Engine Architecture - Stack Overflow
**URL:** https://stackoverflow.com/questions/2850202/meta-search-engine-architecture
**Domain:** stackoverflow.com
**Score:** 16.0
**Source:** scraped
**Query:** metasearch engine architecture design

---

##### Collectives™ on Stack Overflow
Find centralized, trusted content and collaborate around the technologies you use most.
[ Learn more about Collectives ](https://stackoverflow.com/collectives)
**Stack Internal**
Knowledge at work
Bring the best of human thought and AI automation together at your work.
[ Explore Stack Internal ](https://stackoverflow.co/internal/?utm_medium=referral&utm_source=stackoverflow-community&utm_campaign=side-bar&utm_content=explore-teams-compact-popover)
# [Meta Search Engine Architecture](https://stackoverflow.com/questions/2850202/meta-search-engine-architecture)
Asked 15 years, 10 months ago
Modified [5 years, 7 months ago](https://stackoverflow.com/questions/2850202/meta-search-engine-architecture?lastactivity "2020-07-30 01:58:17Z")
Viewed 4k times 
This question shows research effort; it is useful and clear
16 
Save this question.
Show activity on this post.
The question wasn't clear enough, I think; here's an updated straight to the point question:
What are the common architectures used in building a meta search engine and is there any libraries available to build that type of search engine?
I'm looking at building an "enterprise" type of search engine where the indexed data could be coming from proprietary (like Autonomy or a Google Box) or public search engines (like Google Web or Yahoo Web).


[Share](https://stackoverflow.com/q/2850202 "Short permalink to this question")
Share a link to this question
Copy link[CC BY-SA 2.5](https://creativecommons.org/licenses/by-sa/2.5/ "The current license for this post: CC BY-SA 2.5")
[Improve this question](https://stackoverflow.com/posts/2850202/edit)
Follow 
Follow this question to receive notifications
[edited May 19, 2010 at 22:45](https://stackoverflow.com/posts/2850202/revisions "show all edits to this post")
asked May 17, 2010 at 15:08
[Loki](https://stackoverflow.com/users/39057/loki)
31.2k9 gold badges52 silver badges62 bronze badges
3
  * .. depends on what do you mean by "meta search"
mykhal
– [mykhal](https://stackoverflow.com/users/234248/mykhal "20,079 reputation")
2010-05-19 22:34:54 +00:00
[ Commented May 19, 2010 at 22:34 ](https://stackoverflow.com/questions/2850202/meta-search-engine-architecture#comment2915479_2850202)
  * I mean a search engine of search engine. Like [en.wikipedia.org/wiki/Metasearch_engine](http://en.wikipedia.org/wiki/Metasearch_engine) for example. It is also common to see federated search.
2010-05-19 22:46:54 +00:00
[ Commented May 19, 2010 at 22:46 ](https://stackoverflow.com/questions/2850202/meta-search-engine-architecture#comment2915567_2850202)
  * What aspects of the architecture are you interested in? I covered the basic Adapter idea you might need to use to talk to different search engines in my answer, but is there something else you're wanting to find out about? Managing the in-flight requests (as I assume you'll be doing them in parallel) maybe? Or something else entirely.
pdbartlett
– [pdbartlett](https://stackoverflow.com/users/341020/pdbartlett "1,519 reputation")
2010-05-20 11:36:27 +00:00
[ Commented May 20, 2010 at 11:36 ](https://stackoverflow.com/questions/2850202/meta-search-engine-architecture#comment2918940_2850202)


##  5 Answers 5
Sorted by:  [ Reset to default ](https://stackoverflow.com/questions/2850202/meta-search-engine-architecture?answertab=scoredesc#tab-top)
Highest score (default)  Trending (recent votes count more)  Date modified (newest first)  Date created (oldest first) 
This answer is useful
Save this answer.
+100 
This answer has been awarded bounties worth 100 reputation by Loki
Show activity on this post.
If you look at [Garlic (pdf)](http://www.vldb.org/conf/1997/P266.PDF), you'll notice that its architecture is generic enough and can be adapted to a meta-search engine.
**UPDATE:**
The rough architectural sketch is something like this:
```

[Content truncated...]