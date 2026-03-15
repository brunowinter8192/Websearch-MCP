# pgvector v0.5.0: Faster semantic search with HNSW indexes
**URL:** https://supabase.com/blog/increase-performance-pgvector-hnsw
**Domain:** supabase.com
**Score:** 2.9
**Source:** scraped
**Query:** pgvector HNSW ef_search tuning production settings

---

  1. We use cookies to collect data and improve our services. [Learn more](https://supabase.com/privacy#8-cookies-and-similar-technologies-used-on-our-european-services)
[Learn more](https://supabase.com/privacy#8-cookies-and-similar-technologies-used-on-our-european-services)•Privacy settings
Accept Opt out Privacy settings


[Blog](https://supabase.com/blog)
# pgvector v0.5.0: Faster semantic search with HNSW indexes
06 Sep 2023
•
11 minute read
[ Greg RichardsonEngineering ](https://supabase.com/blog/authors/gregnr)
_Contributed by:[Egor Romanov](https://github.com/egor-romanov)_
[Supabase Vector](https://supabase.com/modules/vector) is about to get a lot faster. New Supabase databases will ship with pgvector v0.5.0 which adds a new type of index: Hierarchical Navigable Small World (HNSW).
HNSW is an algorithm for approximate nearest neighbor search, often used in high-dimensional spaces like those found in embeddings.
With this update, you can take advantage of the new HNSW index on your column using the following:
`
 1
 -- Add a HNSW index for the inner product distance function 
 2
 CREATE INDEX ON documents 
 3
 USING hnsw (embedding vector_ip_ops); 
 
`
## How does HNSW work?[#](https://supabase.com/blog/increase-performance-pgvector-hnsw#how-does-hnsw-work)
Compared to inverted file (IVF) indexes which use [clusters](https://supabase.com/docs/guides/ai/vector-indexes/ivf-indexes#how-does-ivfflat-work) to approximate nearest-neighbor search, HNSW uses proximity graphs (graphs connecting nodes based on distance between them). To understand HNSW, we can break it down into 2 parts:
  * **Hierarchical (H):** The algorithm operates over multiple layers
  * **Navigable Small World (NSW):** Each vector is a node within a graph and is connected to several other nodes


### Hierarchical[#](https://supabase.com/blog/increase-performance-pgvector-hnsw#hierarchical)
The hierarchical aspect of HNSW builds off of the idea of skip lists.
Skip lists are multi-layer linked lists. The bottom layer is a regular linked list connecting an ordered sequence of elements. Each new layer above removes some elements from the underlying layer (based on a fixed probability), producing a sparser subsequence that “skips” over elements.
When searching for an element, the algorithm begins at the top layer and traverses its linked list horizontally. If the target element is found, the algorithm stops and returns it. Otherwise if the next element in the list is greater than the target (or NIL), the algorithm drops down to the next layer below. Since each layer below is less sparse than the layer above (with the bottom layer connecting all elements), the target will eventually be found. Skip lists offer O(log n) average complexity for both search and insertion/deletion.
### Navigable Small World[#](https://supabase.com/blog/increase-performance-pgvector-hnsw#navigable-small-world)
A navigable small world (NSW) is a special type of proximity graph that also includes long-range connections between nodes. These long-range connections support the “small world” property of the graph, meaning almost every node can be reached from any other node within a few hops. Without these additional long-range connections, many hops would be required to reach a far-away node.
The “navigable” part of NSW specifically refers to the ability to logarithmically scale the greedy search algorithm on the graph, an algorithm that attempts to make only the locally optimal choice at each hop. Without this property, the graph may still be considered a small world with short paths between far-away nodes, but the greedy algorithm tends to miss them. Greedy search is ideal for NSW because it is quick to navigate and has low computational costs.
###  **Hierarchical +** Navigable Small World[#](https://supabase.com/blog/increase-performance-pgvector-hnsw#hierarchical--navigable-small-world)
HNSW combines these two concepts. From the hierarchical perspective, the bottom layer consists of a

[Content truncated...]