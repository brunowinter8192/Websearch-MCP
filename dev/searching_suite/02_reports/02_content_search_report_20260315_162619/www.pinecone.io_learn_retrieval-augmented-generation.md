# Retrieval-Augmented Generation (RAG) - Pinecone
**URL:** https://www.pinecone.io/learn/retrieval-augmented-generation/
**Domain:** www.pinecone.io
**Score:** 4.0
**Source:** scraped
**Query:** query expansion RAG retrieval augmented generation

---

Öffnet in einem neuen Fenster. Öffnet eine externe Website. Öffnet eine externe Website in einem neuen Fenster.
Dieses Dialogfeld schließen 
Diese Website verwendet Technologien wie Cookies, um wesentliche Funktionen der Website zu ermöglichen sowie für analytik, personalisierung und gezielte werbung. Sie können Ihre Einstellungen jederzeit ändern oder die Standardeinstellungen akzeptieren. Sie können dieses Banner schließen, um nur mit den wesentlichen Cookies fortzufahren.  [Cookie-Richtlinie](https://www.pinecone.io/cookies/)
Einstellungen verwalten  Alle akzeptieren  Nicht wesentliche Cookies ablehnen 
Cookie-Einstellungen schließen 
[🚀 Pinecone BYOC is in public preview. Run Pinecone inside your AWS, GCP, or Azure account with a zero-access operating model. - Read the blog](https://www.pinecone.io/blog/byoc/)Dismiss 
[← Learn](https://www.pinecone.io/learn/)
# Retrieval-Augmented Generation (RAG)
Jun 12, 2025[Core Components](https://www.pinecone.io/learn/category/core-components/)
Share: 
Not only are foundation models stuck in the past, but they intentionally produce natural-sounding and varied responses. Both of these can lead to confidently inaccurate and irrelevant output. This behavior is known as “hallucination.”
In this article, we’ll explore the limitations of foundation models and how retrieval-augmented generation (RAG) can address these limitations so chat, search, and agentic workflows can all benefit.
## Limitations of foundation models
Products built on top of foundation models alone are brilliant yet flawed as foundation models have multiple limitations:
### Knowledge cutoffs
When you ask current models about recent events – like asking about last week’s NBA basketball game or how to use features in the latest iPhone model - they may confidently provide outdated or completely fabricated information, the hallucinations we mentioned earlier.
Models are trained on massive datasets containing years of human knowledge and creative output from code repositories, books, websites, conversations, scientific papers, and more. But after a model is trained, this data is frozen at a specific point in time, the “cutoff”. This cutoff creates a _knowledge gap_ , leading them to generate plausible but incorrect responses when asked about recent developments.
### Lack depth in domain-specific knowledge
Foundation models have broad knowledge, but can lack depth in specialized domains. High quality datasets might not exist publicly for a domain, not necessarily because they are private, but because they are highly specialized. Consider a medical model that knows about anatomy, disease, and surgical techniques, but struggles with rare genetic conditions and cutting edge therapies. This data might exist publicly to be used during training, but it may not appear enough to train the model correctly. It also requires expert-level knowledge during the training process to contextualize the information.
This limitation can result in responses that are incomplete or irrelevant.
### Lack private or proprietary data
In the case of general-purpose, public models, the data (_your_ data) does not exist publicly and is inaccessible during training. This means that models don’t know the specifics of your business, whether that be internal company processes and policies, personnel data or email communications, or even the trade secrets of your company. And for good reason: if this data had been included in the training, anyone using the model would potentially gain access to your company’s private and proprietary data.
Again, this limitation can result in incomplete or irrelevant responses, limiting the usefulness of the model for your custom business purpose.
### Loses trust
Models typically cannot cite their sources related to a specific response. Without citations or references, the user either has to trust the response or validate the claim themselves. Given that models are trained on vast amounts of public data, there is a chance that th

[Content truncated...]