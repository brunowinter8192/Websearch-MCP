# Contextual chunking for Retrieval Augmented Generation - Dev.to
**URL:** https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha
**Domain:** dev.to
**Score:** 2.3
**Source:** scraped
**Query:** contextual chunking prepend context before embedding

---

##  Table of Contents 
  * [Why chunking](https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha#why)
  * [Why contextual chunking](https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha#why-contextual)
  * [Why fixed-size chunking is insufficient](https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha#why-fixed)
  * [How to implement contextual chunking](https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha#how)
  * [Google Gemini 2.5 Pro/Flash](https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha#gemini)
  * [Comparison of Chunking Approaches](https://dev.to/lewis_won/contextual-chunking-for-retrieval-augmented-generation-3lha#comparison)


##  Introduction 
In many enterprise settings, we often have documents which are highly structured and nicely formatted. There is often a hierarchical approach in how the information is structured. For example, there is usually a content page, and relevant information are often grouped by sections. The section numbers are also in running order, and often follow a certain convention, e.g. "d.d.d Header". 
When creating RAG for thousands of such documents, chunking is often necessary so that when queried, the chunks are of manageable length to be passed to LLMs as context. Contextual chunking has significant advantages over simple fixed-size chunking in ensuring the relevancy and completeness of RAG, and in an enterprise setting where precision and accuracy are critical, getting chunking done right can even decide the fate of digital transformation efforts in organisations.
This is a hands-on article with code that you can implement along with me. Instead of reading this article, you may also wish to download my Jupyter notebook directly [here](https://github.com/searlion/rag-strategies/blob/main/contextual_chunking.ipynb).
##  Why chunking 
Given the advent of LLMs such as Google Gemini 2.5 Flash/Pro with 1 million tokens context window, if the number of documents are within the range of 10, chunking may not be necessary. In fact, Gemini can produce very accurate and comprehensive response using such a brute force method, and it is also easy to implement.
The following code demonstrates how we can use Google Gemini to understand a document. First, we set up the Google Gemini client. 
```
from dotenv import load_dotenv
import os

# --- DEBUGGING STEP ---
# Print the current working directory to see where Python is looking.
print(f"Current working directory: {os.getcwd()}")

# Load environment variables from the .env file
load_dotenv()

# Get the API key from the environment variables
# The string "GENAI_API_KEY" must match the variable name in your .env file
api_key = os.getenv("GENAI_API_KEY")

# Check if the API key is loaded correctly
if not api_key:
    raise ValueError("No API key found. Please set the GENAI_API_KEY in your .env file.")

```

Enter fullscreen mode Exit fullscreen mode
If the `GEN_API_KEY` is present and loaded, we should only see the current working directory printed in the output: 
```
Current working directory: /home/lewis/github/rag-strategies

```

[Content truncated...]