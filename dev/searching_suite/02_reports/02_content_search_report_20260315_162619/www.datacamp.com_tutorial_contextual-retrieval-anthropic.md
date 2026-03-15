# Anthropic's Contextual Retrieval: A Guide With Implementation
**URL:** https://www.datacamp.com/tutorial/contextual-retrieval-anthropic
**Domain:** www.datacamp.com
**Score:** 7.0
**Source:** scraped
**Query:** contextual retrieval anthropic chunking RAG

---

[ Last chance: **50% off **unlimited learning Sale ends in Buy Now  ](https://www.datacamp.com/promo/build-data-and-ai-skills-feb-26)
[Skip to main content](https://www.datacamp.com/tutorial/contextual-retrieval-anthropic#main)
Retrieval-augmented generation (RAG) helps AI models incorporate extra knowledge from external sources. However, these systems often lose important context, which can lead to less accurate results.
Anthropic has developed contextual retrieval, a simple yet effective way to improve information retrieval. Keeping the right context in place for each chunk reduces retrieval errors by up to 67%, leading to much better performance in downstream tasks.
In this article, I’ll explain contextual retrieval and how you can use it in your applications.
## RAG with LangChain
Integrate external data with LLMs using Retrieval Augmented Generation (RAG) and LangChain.
## What Is Contextual Retrieval?
While traditional RAG systems are effective, they have a major flaw: they often split documents into small chunks to make retrieval easier, but this can remove important context.
For example, a chunk might say “Its more than 3.85 million inhabitants make it the European Union's most populous city” without mentioning which city or country it's talking about. This lack of context can lead to incomplete or irrelevant results, especially when specific details are needed.
Source: [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
Contextual retrieval fixes this by generating and adding a short, context-specific explanation to each chunk before embedding it. In the example above, the chunk would be transformed as follows:
```


contextualized_chunk = """Berlin is the capital and largest city of Germany, known for being the EU's most populous city within its limits.
Its more than 3.85 million inhabitants make it the European Union's most populous city, as measured by population within city limits.
"""



Powered By [](https://www.datacamp.com/datalab)


Was this AI assistant helpful?

```

Source: [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
Overall, Anthropic's internal tests across different fields, including codebases, scientific papers, and fiction, show that contextual retrieval reduces retrieval errors by 49% when used with contextual embedding models and Contextual BM25.
Source: [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
## Contextual Retrieval Implementation
I’ll now explain step-by-step how to implement contextual retrieval. We’ll use the following sample document as our example:
```


# Input text for the knowledge base
input_text = """Berlin is the capital and largest city of Germany, both by area and by population.
Its more than 3.85 million inhabitants make it the European Union's most populous city, as measured by population within city limits.
The city is also one of the states of Germany and is the third smallest state in the country in terms of area.
Paris is the capital and most populous city of France.
It is situated along the Seine River in the north-central part of the country.
The city has a population of over 2.1 million residents within its administrative limits, making it one of Europe's major population centers."""



Powered By [](https://www.datacamp.com/datalab)


Was this AI assistant helpful?

```

### Step 1: Break the document into chunks
The first step is to break the sample document into smaller, independent chunks. In this instance, we will divide it into individual sentences.
```


[Content truncated...]