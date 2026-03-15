# RAG-PC: Context-Aware Retrieval-Augmented Generation
**URL:** https://github.com/susheeldesai2/RAG-Hierarchical
**Domain:** github.com
**Score:** 1.0
**Source:** scraped
**Query:** parent child chunking retrieval augmented generation

---

[Skip to content](https://github.com/susheeldesai2/RAG-Hierarchical#start-of-content)
You signed in with another tab or window. [Reload](https://github.com/susheeldesai2/RAG-Hierarchical) to refresh your session. You signed out in another tab or window. [Reload](https://github.com/susheeldesai2/RAG-Hierarchical) to refresh your session. You switched accounts on another tab or window. [Reload](https://github.com/susheeldesai2/RAG-Hierarchical) to refresh your session. Dismiss alert
/ **[RAG-Hierarchical](https://github.com/susheeldesai2/RAG-Hierarchical) ** Public
  * You must be signed in to change notification settings
  * [ Star  0 ](https://github.com/login?return_to=%2Fsusheeldesai2%2FRAG-Hierarchical)


[**1** Branch](https://github.com/susheeldesai2/RAG-Hierarchical/branches)[](https://github.com/susheeldesai2/RAG-Hierarchical/tags)
Go to file
Code
Open more actions menu
## Folders and files
Name | Name | Last commit message | Last commit date  
---|---|---|---  
## Latest commit
Mar 5, 2025 [8256517](https://github.com/susheeldesai2/RAG-Hierarchical/commit/825651725ac70d54aa1a89fde4a5a9c759221679) · Mar 5, 2025
## History
[4 Commits](https://github.com/susheeldesai2/RAG-Hierarchical/commits/main/)Open commit details 4 Commits  
|  |  | Mar 5, 2025  
|  |  | Mar 4, 2025  
|  |  | Mar 4, 2025  
|  |  | Mar 4, 2025  
View all files  
## Repository files navigation
# RAG-PC: Context-Aware Retrieval-Augmented Generation
An optimized **Retrieval-Augmented Generation (RAG) pipeline** that enhances retrieval with **parent-child chunking** for better context awareness. Uses **Pinecone** for vector search, **SentenceTransformers** for embeddings, and **ChatGroq (Llama 3 - 70B)** for response generation.
## 📖 Table of Contents
  * [📂 Project Structure](https://github.com/susheeldesai2/RAG-Hierarchical#project-structure)
  * [📚 Libraries Used](https://github.com/susheeldesai2/RAG-Hierarchical#libraries-used)
  * [⚙️ How It Works](https://github.com/susheeldesai2/RAG-Hierarchical#how-it-works)


## Project Structure
```
📦 RAG-PC
├── 📄 main.py             # Core script for PDF processing, chunking, embedding, and retrieval
├── 📄 requirements.txt    # Required libraries
├── 📄 .env                # Environment variables (Pinecone API Key, etc.)
├── 📄 README.md           # Project documentation
```

## Libraries Used
```
| Library                  | Purpose |
|--------------------------|---------|
| `PyPDF2`                 | Extracts text from PDFs |
| `langchain`              | Handles text chunking and processing |
| `pinecone-client`        | Stores and retrieves vector embeddings |
| `langchain-groq`         | Interfaces with **ChatGroq (Llama 3 - 70B)** |
| `sentence-transformers`  | Embedding model for semantic search |
| `python-dotenv`          | Loads environment variables |
```

## Installation
```
pip install -r requirements.txt
```

## Features
  * **Parent-Child Chunking:** Improves retrieval by associating smaller chunks with their parent sections.
  * **Context-Aware Retrieval:** Ensures child chunks retrieve their corresponding parent for enhanced understanding.
  * **Efficient Vector Search:** Uses **Pinecone** for **fast and scalable similarity search**.
  * **Optimized Query Augmentation:** Retrieves **relevant context** before passing it to the LLM.
  * **Scalable & Flexible:** Supports **multiple PDFs** , **different LLMs** , and **fine-tuning chunking strategies**.


## How It Works
### 1️⃣ Extract & Process Text from PDFs
  * Reads a **PDF document** and extracts text.


### 2️⃣ Parent-Child Chunking
  * Splits text into **parent chunks** (larger sections).
  * Further divides each parent into **child chunks** (smaller, detailed sections).
  * Stores **parent-child relationships** to improve retrieval context.


[Content truncated...]