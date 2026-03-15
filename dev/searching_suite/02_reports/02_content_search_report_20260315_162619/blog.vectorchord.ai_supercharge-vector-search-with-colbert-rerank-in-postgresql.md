# Supercharge vector search with ColBERT rerank in PostgreSQL
**URL:** https://blog.vectorchord.ai/supercharge-vector-search-with-colbert-rerank-in-postgresql
**Domain:** blog.vectorchord.ai
**Score:** 4.5
**Source:** scraped
**Query:** ColBERT pgvector integration token level embeddings

---

## Command Palette
Search for a command to run...
Traditional vector search methods typically employ sentence embeddings to locate similar content. However, generating sentence embeddings through pooling token embeddings can potentially sacrifice fine-grained details present at the token level. [ColBERT](https://github.com/stanford-futuredata/ColBERT) overcomes this by representing text as token-level multi-vectors rather than a single, aggregated vector. This approach, leveraging contextual late interaction at the token level, allows ColBERT to retain more nuanced information and improve search accuracy compared to methods relying solely on sentence embeddings.
As illustrated in the above image, ColBERT encodes each document/query into a list of token vectors and computes the MaxSim during the query time.
Token-level late interaction requires more computing power and storage. This makes using ColBERT search in large datasets challenging, especially when low latency is important.
One possible solution is to combine sentence-level vector search with token-level late interaction rerank, which leverages the efficiency of approximate vector search and the high quality of multi-vector similarity search.
The multi-vector approach is not limited to pure text retrieval tasks; it can also be used in visual document understanding. For multimodal retrieval models, state-of-the-art models like [ColPali](https://huggingface.co/vidore/colpali-v1.3) and [ColQwen](https://huggingface.co/vidore/colqwen2-v1.0-merged) directly encode document images into multi-vectors and demonstrate stronger performance compared to OCR-to-text approaches.
This blog will demonstrate using the PostgreSQL extension [VectorChord](https://github.com/tensorchord/VectorChord/) and pgvector with ColBERT rerank.
## Tutorial
Assume we already have the documents, let’s create a table to store all of them:
```
import psycopg
from pgvector.psycopg import register_vector

class PgClient:
    def __init__(self, url: str, dataset: str, sentence_emb_dim: int, token_emb_dim: int):
        self.dataset = dataset
        self.sentence_emb_dim = sentence_emb_dim
        self.token_emb_dim = token_emb_dim
        self.conn = psycopg.connect(url, autocommit=True)
        with self.conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vchord CASCADE;")
        register_vector(self.conn)

    def create(self):
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {self.dataset}_corpus "
                "(id INT BY DEFAULT AS IDENTITY PRIMARY KEY, text TEXT, "
                f"emb vector({self.sentence_emb_dim}), embs vector({self.token_emb_dim})[]);"
            )

```

Here we created a table with sentence-level embedding and token-level embeddings.
There are numerous embedding APIs and [open-source models](https://huggingface.co/spaces/mteb/leaderboard). You can choose the one that fits your use case.
For token-level embedding:
```
from colbert.infra import ColBERTConfig
from colbert.modeling.checkpoint import Checkpoint

class TokenEncoder:
    def __init__(self):
        self.config = ColBERTConfig(doc_maxlen=220, query_maxlen=32)
        self.checkpoint = Checkpoint(
            "colbert-ir/colbertv2.0", colbert_config=self.config, verbose=0
        )

    def encode_doc(self, doc: str):
        return self.checkpoint.docFromText([doc], keep_dims=False)[0].numpy()

    def encode_query(self, query: str):
        return self.checkpoint.queryFromText([query])[0].numpy()

```

[Content truncated...]