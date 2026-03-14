# Tips for fast search results? · searxng searxng · Discussion #1738
**URL:** https://github.com/searxng/searxng/discussions/1738
**Domain:** github.com
**Score:** 16.0
**Source:** scraped
**Query:** searxng configuration best practices

---

[Skip to content](https://github.com/searxng/searxng/discussions/1738#start-of-content)
/ Public
  * You must be signed in to change notification settings
  * [ Star  26.4k ](https://github.com/login?return_to=%2Fsearxng%2Fsearxng)


Discussion options
Quote reply
## 
[ ecker00 ](https://github.com/ecker00) [ Sep 1, 2022 ](https://github.com/searxng/searxng/discussions/1738#discussion-4354394)
I'm wondering what are some of the best practices when it comes to improving performance and response time for SearXNG? I've not seen much discussion on it, and there are a lot of parameters to tweak. How are the best servers achieving sub-second response times? Just to get a sense of how fast different sites where, I did some very rough testing estimates in my browser. DOMContentLoaded timing in Firefox:
  * Quant ~250-500 ms
  * DuckDuckGo ~550-750 ms
  * Google and Bing ~900-1300 ms
  * [Tiekoetter's Searxng](https://searx.tiekoetter.com/) instance ~950-1300 ms (Quite good!)
  * My own Searxng instance ~6200-6600 ms (On fast fiber, M1 mac server)

My own SearXNG server usually takes more than 6 seconds to process a basic request, any tips?  
---  
Beta Was this translation helpful? [Give feedback.](https://github.com/searxng/searxng/discussions/1738)
You must be logged in to vote
All reactions
##  1 comment  · 1 reply 
Comment options
Quote reply
### 
[ tiekoetter ](https://github.com/tiekoetter) [ Sep 1, 2022 ](https://github.com/searxng/searxng/discussions/1738#discussioncomment-3530531)
Collaborator 
Usually having only the upstream engines enabled which you really need / want to use helps a lot. If that doesn't help you can look on the engine stats page to see which engines are slow and disable them. This should give you some insight in what might be slowing you down.  
---  
Beta Was this translation helpful? [Give feedback.](https://github.com/searxng/searxng/discussions/1738)
You must be logged in to vote
All reactions
1 reply 
Comment options
Quote reply
#### 
[ecker00](https://github.com/ecker00) [ Sep 2, 2022 ](https://github.com/searxng/searxng/discussions/1738#discussioncomment-3535047)
Author 
Thank you for some pointers. 👍 If other people have suggestion, be nice to post them here as a future reference.  
---  
Beta Was this translation helpful? [Give feedback.](https://github.com/searxng/searxng/discussions/1738)
All reactions
[Sign up for free](https://github.com/join?source=comment-repo) **to join this conversation on GitHub**. Already have an account? [Sign in to comment](https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fsearxng%2Fsearxng%2Fdiscussions%2F1738)
Category 
[ General ](https://github.com/searxng/searxng/discussions/categories/general)
Labels 
None yet 
2 participants 
