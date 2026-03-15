# Dense vs Sparse: A Short, Chaotic, and Honest History of RAG Retrievers ...
**URL:** https://medium.com/@pinareceaktan/dense-vs-sparse-a-short-chaotic-and-honest-history-of-rag-retrievers-from-tf-idf-to-colbert-7bb3a60414a1
**Domain:** medium.com
**Score:** 24.0
**Source:** scraped
**Query:** ColBERT vs dense retrieval benchmark recall comparison

---

[Sitemap](https://medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
# Dense vs Sparse: A Short, Chaotic, and Honest History of RAG Retrievers (From TF-IDF to ColBert)
Follow
26 min read Aug 11, 2025
Share
Today, we’ll take a walk through the evolutionary path of text retrieval — from the dusty stacks of bag-of-words models to the shimmering corridors of dense retrievers. It took me a lot of cognitive load (and maybe a mild panic attack in the middle), but I’m fine.
Press enter or click to view image in full size
Photo by [Jack Anstey](https://unsplash.com/@jack_anstey?utm_source=medium&utm_medium=referral) on [Unsplash](https://unsplash.com/?utm_source=medium&utm_medium=referral)
### Document Outline
  1. TF-IDF: How Term Weighting Powers Search (1950s to 90s)
  2. Dense phrase index [13] (2019) for Open Domain Question Answer
  3. Dense Passage Retriever [11] (2020) for Open Domain Question Answer
  4. Siamese DANs: Google’s Learning semantic textual similarity from conversations (2018) [10]
  5. Making a Point(wise): SBERT’s Journey Beyond Averaging” (2019) [1]
  6. ColBERT: Smart Inhibition of Overly Clingy Towers (2020) [14]
  7. ANCE: Do not work harder, but smarter (2020) [20]
  8. Me-Bert: What We Lose in the Cost of Densification [19] (2021)
  9. RocketQA [8](2020) and PAIR [28](2021): Back to the Basics
  10. Contriever (2022)[21]


## TF-IDF: How Term Weighting Powers Search
Enhancing natural language understanding for reading comprehension and information retrieval goes way back to ancient times (well, “ancient” in computer science years). And it all -pretty much — can be mapped to TF-IDF. If we trace the bloodline of TF–IDF back to its earliest ancestors, it doesn’t start with _Salton_ at Cornell, but with a man in an IBM lab in the late 1950s — _Hans Peter_**Luhn**[25]. **Luhn** was playing with the idea that maybe, just maybe, the frequency of a word in a text could tell you something about its importance. His work on “statistical analysis of literature” and “automatic abstracting” wasn’t TF–IDF yet, but it was definitely the proto-DNA of the whole thing.
Fast forward to 1972, and in comes **Karen Spärck Jones**[26], who gave us the _other_ half of the equation: inverse document frequency. She formally described the intuition that rare terms across documents should weigh more than the ones that show up everywhere (sorry “the” and “and”, you’re still useless).
Now, Gerard Salton [23, 24] — the man behind the SMART system — took these building blocks and ran with them. Through the 1970s and 80s, Salton and his team systematized term frequency, IDF, and the whole TF–IDF weighting scheme into a functioning ranking model. That’s when TF–IDF became not just a neat idea, but the beating heart of early search engines.
Though exacting for its era, TF-IDF had a blind spot:_it treated text like a bowl of word soup, ignoring word order_ — which is sometimes very important.
**Example** :
_Cat sat on a tree. He sat on a tree with a cat on his lap._
Both would score similarly, even though they describe different scenes. It also didn’t fully reward documents containing a “juicy” rare word (like _Connecticut_) more than others — if it appeared too often, TF-IDF didn’t really know how to handle that balance.
Than, there came **BM25[27]**. In 1994, **Stephen Robertson** and**Karen Spärck Jones,** working on the Okapi project, introduced this statistically refined successor to TF-IDF. BM25 was smarter:
  * It favored documents containing those rare “juicy” terms — but with _saturation_ , avoiding over-rewarding them.
  * It normalized scores based on document length, intuitively rewarding high term frequency more in short documents than in very long ones.


[Content truncated...]