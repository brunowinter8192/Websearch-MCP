# Introducing Contextual Retrieval by Anthropic : r/Rag - Reddit
**URL:** https://www.reddit.com/r/Rag/comments/1fl2wma/introducing_contextual_retrieval_by_anthropic/
**Domain:** www.reddit.com
**Score:** 3.6
**Source:** scraped
**Query:** contextual retrieval anthropic chunking RAG

---

[ Zum Hauptinhalt springen ](https://www.reddit.com/r/Rag/comments/1fl2wma/introducing_contextual_retrieval_by_anthropic/#main-content)
Introducing Contextual Retrieval by Anthropic : r/Rag
• vor 2 Jahren
#  Introducing Contextual Retrieval by Anthropic 
[ anthropic.com  Öffnen ](https://www.anthropic.com/news/contextual-retrieval)
Teilen 
[ adobe_acrobatdc](https://www.reddit.com/user/adobe_acrobatdc/) • [ Gesponsert ](https://www.reddit.com/user/adobe_acrobatdc/)
Erstelle einfach personalisierte PDF Spaces und fasse PDFs und Weblinks zusammen – in nur einem Klick.
Mehr erfahren
adobe.com 
• [ vor 2 Jahren ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lo0ojwr/)
This is nothing new though this same approach is being followed in my company for months. 
3 weitere Antworten 
3 weitere Antworten 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lo0ojwr/?force-legacy-sct=1)
• [ vor 2 Jahren ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lo3b1o1/)
This is an interesting variation on the contextual chunk headers method that we use in [dsRAG](https://github.com/D-Star-AI/dsRAG). My one concern with their method is that you have to put the entire document into context for EACH chunk. Even with context caching that's still going to be pretty slow and expensive for large documents, as the cost scales roughly quadratically with document length. I need to run some eval on this method to see how it compares to the cheaper and faster method of creating contextual chunk headers with document and section titles/summaries, which works really well as-is. 
• [ vor 1 Jahr ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lp0ybe2/)
Right? This is incredibly inefficient. One tiny better way would be 10 chunks at a time. You lose some of the purity of the anthropic approach but it’s all from the same document so who cares? Their method only seems justified when your chunks are being drawn from multiple documents and the you therefore can’t risk mixing the context. 
• [ vor 10 Monaten ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/musrmce/)
here's what I came up with so far: "You are an assistant that, given a main document and one or more chunks, generates for each chunk a short self-explanatory context string situating it within the overall document. I need redundant but fully independent contexts. Assume the reader has no prior knowledge of the document's topic. Very briefly explain anything that might not be known by the average person by prioritizing knowledge from the main document or, otherwise, from your knowledge. The final output must be valid JSON only: keys are each chunk’s ID, values are the succinct context. 
<document> {full_document} </document> <chunks> {chunks_str} </chunks> Produce only a JSON object mapping each chunk ID to its generated context. Do not include any other text or formatting." 
2 weitere Antworten 
2 weitere Antworten 
[ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/musrmce/?force-legacy-sct=1) [ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lp0ybe2/?force-legacy-sct=1) [ Setze diesen Thread fort  ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lo3b1o1/?force-legacy-sct=1)
• [ vor 2 Jahren ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lo1rhlz/)
can this be combined with graphRAG? 
• [ vor 2 Jahren ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lo6cnr0/)
Can someone explain explicitly how prompt caching would save cost here? Assume the full document is 100k token, and I have 10k chunks to “contextualize”: if I were to follow their method to generate and pretend 50-100 tokens to each chunk, how many tokens will it cost with their prompt caching? 
• [ vor 1 Jahr ](https://www.reddit.com/r/Rag/comments/1fl2wma/comment/lp0wkkd/)
I have been doing this since May of 2023. The prompt template in the paper is weak. You should contextualize your chunking approac

[Content truncated...]