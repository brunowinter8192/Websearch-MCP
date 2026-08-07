# The raw: prefix does not degrade link resolution — 2026-08-06

Orchestrator-side record: probes run in chat, no worker counterpart. Written after the `raw://` →
`raw:` switch in this area had been merged, when output from a later live run looked like a
regression caused by it.

## The suspicion

A Camoufox run against a guenstiger.de challenge page returned 343542 bytes whose markdown opened
with an image link containing the entire captured document as its URL:

```
![guenstiger.de](raw:<!DOCTYPE html><html lang="de" dir="ltr"><head> …
```

Read at first glance as a side effect of the prefix change: crawl4ai resolves relative asset URLs
against a base URL, and with the `//` removed that base is the whole document instead of a netloc.

## What the probes showed

Two synthetic pages through crawl4ai 0.9.2, only the prefix varied.

Relative and absolute URLs — byte-identical output, 72 bytes each:

```
![site](/logo.svg)[link](/next)[abs](https://abs.example/x)
hello world
```

Empty and self-referential `src` — the artifact appears under BOTH prefixes:

| prefix | md bytes | first image link |
|---|---|---|
| `raw://` | 176 | `![empty-src](raw://<html>…</html>)` |
| `raw:` | 174 | `![empty-src](raw:<html>…</html>)` |

The two-byte difference is the prefix itself. `<img src="#">` renders as `![hash-src](#)` in both.

## Conclusion recorded at the time

The artifact is triggered by `<img src="">`, not by the prefix: an empty `src` resolves to the base
URL, and for a raw pseudo-URL the base URL IS the document. Pre-existing crawl4ai behaviour,
independent of which raw form is used, and not introduced by the switch. The idealo.de page captured
the same day carries zero such artifacts; the guenstiger challenge page has an image without a `src`.

Not investigated: whether crawl4ai should special-case an empty `src` at all, and whether the same
resolution path affects `<a href="">`. Neither was needed to answer the question that prompted the
probes.
