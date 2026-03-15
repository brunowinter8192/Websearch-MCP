# Why Chunking Strategy Decides More Than Your Embedding Model : r/Rag
**URL:** https://www.reddit.com/r/Rag/comments/1nvzl1b/why_chunking_strategy_decides_more_than_your/
**Domain:** www.reddit.com
**Score:** 6.7
**Source:** scraped
**Query:** chunk overlap size impact retrieval quality embedding

---

[ Zum Hauptinhalt springen ](https://www.reddit.com/r/Rag/comments/1nvzl1b/why_chunking_strategy_decides_more_than_your/#main-content)
Why Chunking Strategy Decides More Than Your Embedding Model : r/Rag
• vor 5 Monaten
#  Why Chunking Strategy Decides More Than Your Embedding Model 
Every RAG pipeline discussion eventually comes down to _“which embedding model is best?”_ OpenAI vs Voyage vs E5 vs nomic. But after following dozens of projects and case studies, I’m starting to think the bigger swing factor isn’t the embedding model at all. It’s chunking. 
Here’s what I keep seeing: 
  * **Flat tiny chunks** → fast retrieval, but noisy. The model gets fragments that don’t carry enough context, leading to shallow answers and hallucinations. 
  * **Large chunks** → richer context, but lower recall. Relevant info often gets buried in the middle, and the retriever misses it. 
  * **Parent-child strategies** → best of both. Search happens over small “child” chunks for precision, but the system returns the full “parent” section to the LLM. This reduces noise while keeping context intact. 


What’s striking is that even with the same embedding model, performance can swing dramatically depending on how you split the docs. Some teams found a 10–15% boost in recall just by tuning chunk size, overlap, and hierarchy, more than swapping one embedding model for another. And when you layer rerankers on top, chunking still decides how much good material the reranker even has to work with. 
Embedding choice matters, but if your chunks are wrong, no model will save you. The foundation of RAG quality lives in preprocessing. 
what’s been working for others, do you stick with simple flat chunks, go parent-child, or experiment with more dynamic strategies? 
Weiterlesen 
Teilen 
[ bloomwell_de](https://www.reddit.com/user/bloomwell_de/) • [ Gesponsert ](https://www.reddit.com/user/bloomwell_de/)
Request recipe now #bloomwell
Registrieren
bloomwell.de 
• [ vor 5 Monaten ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhcu08d/)
Not saying you’re doing this, but anyone making claims about best chunking strategy without also explaining the specific kind of information and anticipated use case by actual users of the system is by default wrong. Chunking and retrieval design has to involve subject matter experts on the knowledge structure of the documents/info and UX designers on the system’s goals and use cases. 
In my experience you typically need more than one retrieval method and indexing setup on almost any set of documents and there is no single right answer. 
• [ vor 5 Monaten ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhertci/)
The “best” chunking or retrieval setup can’t be one-size-fits-all, it depends a lot on domain, how the docs are structured, and what the end users are trying to achieve 
I liked the way you replied brother thanks 
[ GolfEmbarrassed2904 ](https://www.reddit.com/user/GolfEmbarrassed2904/)
• [ vor 5 Monaten ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhmt019/)
It’s actually more than that. Every single decision on your technical solution is based on the use case. Not just chunking. Like when to use graph + vector. You can do an LLM summary and stuff it into your chunk. So many different ways to solution RAG 
1 weitere Antwort 
1 weitere Antwort 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhmt019/?force-legacy-sct=1) 1 weitere Antwort 
1 weitere Antwort 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhertci/?force-legacy-sct=1) [ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhcu08d/?force-legacy-sct=1)
• [ vor 5 Monaten ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhdr561/)
would the "parent" be like a page from the document and the "child" is a paragragh within that page? 
• [ vor 5 Monaten ](https://www.reddit.com/r/Rag/comments/1nvzl1b/comment/nhevzos/)
Yep, you got it! 

[Content truncated...]