# Iterative index scans · Issue #678 · pgvector/pgvector - GitHub
**URL:** https://github.com/pgvector/pgvector/issues/678
**Domain:** github.com
**Score:** 8.0
**Source:** scraped
**Query:** pgvector 0.8 iterative scan HNSW performance

---

[Skip to content](https://github.com/pgvector/pgvector/issues/678#start-of-content)
You signed in with another tab or window. [Reload](https://github.com/pgvector/pgvector/issues/678) to refresh your session. You signed out in another tab or window. [Reload](https://github.com/pgvector/pgvector/issues/678) to refresh your session. You switched accounts on another tab or window. [Reload](https://github.com/pgvector/pgvector/issues/678) to refresh your session. Dismiss alert
/ Public
  * You must be signed in to change notification settings
  * [ Star  20.3k ](https://github.com/login?return_to=%2Fpgvector%2Fpgvector)


#  Iterative index scans #678
Copy link
Copy link
[Iterative index scans](https://github.com/pgvector/pgvector/issues/678#top)#678
Copy link
## Description
opened [on Sep 22, 2024](https://github.com/pgvector/pgvector/issues/678#issue-2541226111)edited by [ankane](https://github.com/ankane)
Edits
Member
Issue body actions
Hi all, I wanted to share some work on iterative index scans to get feedback.
  * [hnsw-streaming branch](https://github.com/pgvector/pgvector/compare/hnsw-streaming)
  * [ivfflat-streaming branch](https://github.com/pgvector/pgvector/compare/ivfflat-streaming)


You can enable this functionality (naming TDB) with:
```
SET hnsw.streaming = on;
SET ivfflat.streaming = on;
```

For HNSW, it keeps track of discarded candidates at layer 0. When more tuples are needed, it calls `HnswSearchLayer` / Algorithm 2 with the nearest discarded candidates as entry points (in batches of `ef_search`). The scan terminates when enough tuples are found, `hnsw.ef_stream` elements are visited, or `work_mem` is exceeded.
For IVFFlat, it scans the next closest lists in groups of `ivfflat.probes`, up to `ivfflat.max_probes`.
One issue I'm having trouble addressing is how to terminate scans for queries with distance filters. In the query below, if only 9 records are within the distance, it'll continue scanning the index. I've tried using `xs_orderbyvals` on `IndexScanDesc`, but it doesn't seem to help.
```
SELECT * FROM items WHERE embedding - $1  0.1 ORDER BY embedding - $1 LIMIT 10;
```

👍React with 👍2lovanto and tommyhe6
## Activity
[ankane](https://github.com/ankane)
mentioned this [on Sep 22, 2024](https://github.com/pgvector/pgvector/issues/678#event-1471404140)
  * [Hnsw iterator #282](https://github.com/pgvector/pgvector/pull/282)


### jkatz commented on Sep 22, 2024 
Contributor
More actions
[@ankane](https://github.com/ankane) Isn't that part of the scan key? (`IndexScanDesc->keyData`; type `ScanKeyData`); Maybe checking if there's an explicitly vector distance computation within the scan keys and set that as one of the flags as part of the HNSW/IVFFlat scan so we don't need to continuously recheck.
[ankane](https://github.com/ankane)
mentioned this [on Sep 22, 2024](https://github.com/pgvector/pgvector/issues/678#event-1471423121)
  * [Add search option to better process queries with WHERE clause (relaxed monotonicity) #524](https://github.com/pgvector/pgvector/pull/524)


### ankane commented on Sep 22, 2024 
MemberAuthor
More actions
`scan->numberOfKeys` is always zero in my testing.
[ankane](https://github.com/ankane)
mentioned this in 3 issues [on Sep 23, 2024](https://github.com/pgvector/pgvector/issues/678#event-1471528628)
  * [Understanding HNSW + filtering #259](https://github.com/pgvector/pgvector/issues/259)
  * [No results when using index #263](https://github.com/pgvector/pgvector/issues/263)
  * [HNSW + dead tuples: recall loss/usability issues #244](https://github.com/pgvector/pgvector/issues/244)


[Content truncated...]