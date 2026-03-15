# Advanced RAG: Query Expansion - Haystack
**URL:** https://haystack.deepset.ai/blog/query-expansion
**Domain:** haystack.deepset.ai
**Score:** 15.0
**Source:** scraped
**Query:** query expansion RAG retrieval augmented generation

---

[ 🔎 **Haystack 2.25 is here!** `SearchableToolset` to reduce context usage & Jinja2 templates for Agents  ](https://haystack.deepset.ai/release-notes/2.25.0)
[ Retrieval ](https://haystack.deepset.ai/blog/tags/retrieval) [ Advanced Use Cases ](https://haystack.deepset.ai/blog/tags/advanced-use-cases)
# Advanced RAG: Query Expansion
Expand keyword queries to improve recall and provide more context to RAG.
August 14, 2024 
> This is part one of the **Advanced Use Cases** series:
> 1️⃣ [Extract Metadata from Queries to Improve Retrieval](https://haystack.deepset.ai/blog/extracting-metadata-filter)
> 2️⃣ **Query Expansion**
> 3️⃣ [Query Decomposition](https://haystack.deepset.ai/blog/query-decomposition)
> 4️⃣ [Automated Metadata Enrichment](https://haystack.deepset.ai/cookbook/metadata_enrichment)
The quality of RAG (retrieval augmented generation) highly depends on the quality of the first step in the process: retrieval. The generation step can only be as good as the context its working on, which it will receive as a result of a retrieval step.
However, retrieval is also in turn dependent on the query that it receives. There are multiple types of retrieval: keyword based, semantic search (embedding) based, hybrid, or even in some cases simply based on the results of a query to an API (for example, the results of websearch and so on). But at the end of the day, in the majority of cases, there’s a human behind a keyboard typing a query, and humans are not guaranteed to produce good quality queries for the results they intend to get.
In this article, we’ll walk you through a very simple yet effective technique that allows us to make sure we are retrieving more of, and more relevant bits of context to a given query: query expansion.
> TL;DR: Query expansion increases the number of results, so it increases recall (vs precision). In general, BM25 favors precision while embedding retrieval favors recall (See this [explanation by Nils Reimers](https://github.com/UKPLab/sentence-transformers/issues/22#issuecomment-529387645)). So, it makes sense to use BM25+query expansion to increase recall in cases where you want to rely on keyword search.
## Query Expansion
Query expansion is a technique where we take the user query, and generate a certain number of similar queries. For example:
**User Query:** “open source NLP frameworks”
**After Query Expansion:** [”natural language processing tools”, “free nlp libraries”, “open-source language processing platforms”, “NLP software with open-source code”, “open source NLP frameworks”]
This helps improve retrieval results, and in turn the quality of RAG results in cases where:
  * The user query is vague or poorly formed.
  * In cases of keyword-based retrieval, it also allows you to cover your bases with queries of similar meaning or synonyms.


Take ‘global warming’ as an example, query expansion would allow us to make sure we’re also doing keyword search for ‘climate change’ or similar queries.
Let’s start by importing the experimental `QueryExpander` component. This component is using an OpenAI model (`gpt-4o-mini` in this case) to generate a certain `number` of additional queries that are similar to the original user query. It returns queries, which include the original query plus the generated similar ones:
```
expander = QueryExpander()
expander.run(query="open source nlp frameworks", number=4)
Copy
```

This would result in the component returning `queries` that include the original query + 4 expanded queries:
```
{'queries': ['natural language processing tools',
  'free nlp libraries',
  'open-source language processing platforms',
  'NLP software with open-source code',
  'open source nlp frameworks']}
Copy
```

[Content truncated...]