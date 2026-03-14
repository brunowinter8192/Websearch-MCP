# How to use asyncio to scrape websites with Python - ScrapingBee
**URL:** https://www.scrapingbee.com/blog/async-scraping-in-python/
**Domain:** www.scrapingbee.com
**Score:** 60.0
**Source:** scraped
**Query:** python async web scraping tutorial

---

**Alexander M | 13 January 2026 (updated) | 10 min read**
In this article, we'll take a look at how you can use Python and its coroutines, with their `async`/`await` syntax, to efficiently scrape websites, without having to go all-in on threads 🧵 and semaphores 🚦. For this purpose, we'll check out [asyncio](https://docs.python.org/3/library/asyncio.html), along with the asynchronous HTTP library [aiohttp](https://docs.aiohttp.org).
## What is asyncio?
[asyncio](https://docs.python.org/3/library/asyncio.html) is part of Python's standard library (yay, no additional dependency to manage 🥳) which enables the implementation of concurrency using the same asynchronous patterns you may already know from JavaScript and other languages: `async` and `await`
Asynchronous programming is a convenient alternative to [Python threads](https://docs.python.org/3/library/threading.html), as it allows you to run tasks in parallel without the need to fully dive into multi-threading, with all the complexities this might involve.
When using the asynchronous approach, you program your code in a seemingly good-old synchronous/blocking fashion and just sprinkle mentioned keywords at the relevant spots in your code and the Python runtime will automatically take care of your code being executed concurrently.
### Asynchronous Python basics
asyncio uses the following three key concepts to provide asynchronicity:
  * Coroutines
  * Tasks
  * Futures


**Coroutines** are the basic building blocks and allow you to declare asynchronous functions, which are executed concurrently by asyncio's event loop and provide a _Future_ as response (more on that in a second). A coroutine is declared by prefixing the function declaration with `async` (i.e. `async def my_function():`) and it typically uses `await` itself, to invoke other asynchronous functions.
**Tasks** are the components used for scheduling and the actual concurrent execution of coroutines in an asyncio context. They are instantiated with `asyncio.create_task()` and automatically handled by the event loop.
**Futures** are the return value of a coroutine and represent the _future_ value computed by the coroutine.
You can find a full list of technical details at <https://docs.python.org/3/library/asyncio-task.html#awaitables>.
### How does `async`/`await` work?
If you happen to be already familiar with `async`/`await` in JavaScript, you'll feel right at home as the underlying concept is the same. While asynchronous programming per se is not something new, this was usually achieved with callbacks and the eventual [pyramid of doom](https://en.wikipedia.org/wiki/Pyramid_of_doom_%28programming%29) with all the nested and chained callbacks. This was pretty unmanageable in both, JavaScript and Python. `async`/`await` came to the rescue here.
When you have a task which takes longer to compute (typical example when to use multi-threading), you can mark the function with `async` and turn it into a coroutine. Let's take the following code as quick example.
```
import asyncio

async def wait_and_print():
  await asyncio.sleep(1)
  print(str)

async def main():
  tasks = []

  for i in range(1, 10):
    tasks.append(asyncio.create_task(wait_and_print(i)))

  for task in tasks:
    await task

asyncio.run(main())

```

[Content truncated...]