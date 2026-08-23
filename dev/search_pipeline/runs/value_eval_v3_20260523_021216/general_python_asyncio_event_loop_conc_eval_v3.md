# Value Eval v3 — general × python asyncio event loop concurrency

**Mode:** general  **Query:** python asyncio event loop concurrency  **Pool (filtered):** 56

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 11 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1975 |
| M7 C3+InstrPrefix | 1912 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1886 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 7502 |
| M12 LLM-Selector | 11640 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.250 | 4/10 |
| M2 RRF post-bucket | 0.250 | 4/10 |
| M3 Structural URL | 0.176 | 3/10 |
| M4 BM25 vanilla | 0.250 | 4/10 |
| M5 BM25-Capped | 0.176 | 3/10 |
| M6 C3 Cross-Encoder | 0.333 | 5/10 |
| M7 C3+InstrPrefix | 0.250 | 4/10 |
| M8 RRF+C3 Hybrid | 0.333 | 5/10 |
| M9 SPLADE | 0.538 | 7/10 |
| M10 SPLADE+C3 | 0.538 | 7/10 |
| M11 C3→LLM-Filter | 0.176 | 3/10 |
| M12 LLM-Selector | 0.111 | 2/10 |

## Pool (oracle input — url/title/snippet)

1. http://aosabook.org/en/500L/a-web-crawler-with-asyncio-coroutines.html
   A Web Crawler With asyncio Coroutines
   aosabook.org

2. http://techspot.zzzeek.org/2015/02/15/asynchronous-python-and-databases/
   Asynchronous Python and Databases
   techspot.zzzeek.org

3. https://blog.nelhage.com/post/concurrent-error-handling/
   From error-handling to structured concurrency
   blog.nelhage.com

4. https://charlesleifer.com/blog/asyncio/
   AsyncIO Thoughts
   charlesleifer.com

5. https://dev.to/imsushant12/asyncio-architecture-in-python-event-loops-tasks-and-futures-explained-4pn3
   Asyncio Architecture in Python: Event Loops, Tasks, and Futures ...
   Asyncio: Single thread, single process. It uses an event loop to run many tasks concurrently by switching between them when one task is waiting (for example, waiting for network or file I/O). It is be

6. https://dhirendrabiswal.com/advanced-python-concurrency-asyncio-event-loop-optimization-and-concurrent-futures-patterns/
   Advanced Python Concurrency: Asyncio Event Loop Optimization and ...
   TL;DR: In this guide, I dive deep into advanced Python concurrency using asyncio and concurrent.futures. You'll learn how to optimize the event loop for high-performance I/O-bound and mixed workloads,

7. https://docs.python.org/3/library/asyncio-eventloop.html
   Event loop — Python 3.14.5 documentation
   Preface The event loop is the core of every asyncio application. Event loops run asynchronous tasks and callbacks, perform network IO operations, and run subprocesses. Application developers should ty

8. https://doi.org/10.1007/978-1-4842-3742-7_9
   Applications with asyncio and Twisted
   Williams, M. et al. (2019), Expert Twisted

9. https://doi.org/10.1007/978-1-4842-4401-2_2
   Working with Event Loops
   Python version 3.4 has adopted a powerful framework to support concurrent execution of code: asyncio. This framework uses event loops to orchestrate the callbacks and asynchronous tasks. Event loops l

10. https://doi.org/10.1007/978-1-4842-8140-6_1
   (A)synchronous Python
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

11. https://doi.org/10.1007/978-1-4842-8140-6_13
   Testing
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

12. https://doi.org/10.1007/978-1-4842-8140-6_17
   History
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

13. https://doi.org/10.1007/978-1-4842-8140-6_2
   Modern Asynchronous Python The Building Blocks
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

14. https://doi.org/10.1007/978-1-4842-8140-6_6
   asyncio Streams
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

15. https://doi.org/10.1007/978-3-030-25943-3_34
   Concurrency with AsyncIO
   Hunt, J. (2019), Undergraduate Topics in Computer Science

16. https://doi.org/10.1007/978-3-031-40336-1
   Advanced Guide to Python 3 Programming
   

17. https://doi.org/10.1007/978-3-031-40336-1_43
   Concurrency with AsyncIO
   Hunt, J. (2023), Undergraduate Topics in Computer Science

18. https://doi.org/10.1007/979-8-8688-1261-3_16
   Asyncio
   Divakaran, A. (2025), Deep Dive Python

19. https://doi.org/10.1007/s41781-021-00053-3
   Performance of Julia for High Energy Physics Analyses
   

20. https://doi.org/10.1109/access.2020.3008954
   Control and Visualisation of a Software Defined Radio System on the Xilinx RFSoC Platform Using the 
   The availability of commercial Radio Frequency System on Chip (RFSoC) devices brings new possibilities for implementing Software Defined Radio (SDR) systems. Such systems are of increasing interest gi

21. https://doi.org/10.1109/ojits.2023.3266800
   Infrastructure-Based Digital Twins for Cooperative, Connected, Automated Driving and Smart Road Serv
   Driving requires continuous decision making from a driver taking into account all available relevant information. Automating driving tasks also automates the related decisions. However, humans are ver

22. https://doi.org/10.1145/3445814.3446701
   Nightcore: efficient and scalable serverless computing for latency-sensitive, interactive microservi
   The microservice architecture is a popular software engineering approach for building flexible, large-scale online services. Serverless functions, or function as a service (FaaS), provide a simple pro

23. https://doi.org/10.3390/en13153770
   Distributed Power Hardware-in-the-Loop Testing Using a Grid-Forming Converter as Power Interface
   This paper presents an approach to extend the capabilities of smart grid laboratories through the concept of Power Hardware-in-the-Loop (PHiL) testing by re-purposing existing grid-forming converters.

24. https://doi.org/10.4018/ijswis.2016100102
   Managing Large Amounts of Data Generated by a Smart City Internet of Things Deployment
   The Smart City concept is being developed from a lot of different axes encompassing multiple areas of social and technical sciences. However, something that is common to all these approaches is the ce

25. https://doi.org/10.47667/ijpasr.v4i2.202
   Python TCP/IP libraries: A Review
   The Internet's core is TCP/IP, which stands for Transmission Control Protocol/Internet Protocol. It connects network devices on the internet via communication protocols. Python has several TCP/IP pack

26. https://doi.org/10.7256/2454-0714.2018.2.25851
   Савостин П.А., Ефремова Н.Э. Практическое применение асинхронного программирования на языке Python п
   (2018), Программные системы и вычислительные методы

27. https://emptysqua.re/blog/why-should-async-get-all-the-love/
   Why Should Async Get All The Love?: Advanced Control Flow With Threads
   emptysqua.re

28. https://fractalideas.com/blog/sans-io-when-rubber-meets-road/
   Sans I/O when rubber meets the road
   fractalideas.com

29. https://medium.com/@yeraydiazdiaz/asyncio-for-the-working-python-developer-5c468e6e2e8e
   AsyncIO for the Working Python Developer
   medium.com/@yeraydiazdiaz

30. https://realpython.com/async-io-python/
   Python's asyncio: A Hands-On Walkthrough - Real Python
   Python's asyncio library enables you to write concurrent code using the async and await keywords. The core building blocks of async I/O in Python are awaitable objects—most often coroutines—that an ev

31. https://stackoverflow.com/questions/26270681/can-an-asyncio-event-loop-run-in-the-background-without-suspending-the-python-in
   concurrency - Can an asyncio event loop run in the background
   Can an asyncio event loop run in the background without suspending the Python interpreter? ... Note that you must call asyncio.set_event_loop on the ...

32. https://stackoverflow.com/questions/29269370/how-to-properly-create-and-run-concurrent-tasks-using-pythons-asyncio-module
   How to properly create and run concurrent tasks using python's asyncio module?
   I am trying to properly understand and implement two concurrently running Task objects using Python 3's relatively new asyncio module. In a nutshell, asyncio seems designed to handle asynchronous proc

33. https://stackoverflow.com/questions/48483348/how-to-limit-concurrency-with-python-asyncio
   How to limit concurrency with Python asyncio? - Stack Overflow
   This pauses the generator when there are enough active tasks, and lets the event loop clean up finished tasks. Note, for older python versions, replace create_task with ensure_future.

34. https://stackoverflow.com/questions/49584561/run-infinite-loop-in-asyncio-event-loop-running-off-the-main-thread
   python - run infinite loop in asyncio event loop running off
   Instead, you can await an asyncio.Event , and set it using something like loop.call_soon_threadsafe(event.set) from the other thread.

35. https://stackoverflow.com/questions/53268438/python-asyncio-within-multiprocessing-one-event-loop-per-process
   Python asyncio within Multiprocessing. One event loop per process
   I am writing a function for my team that will download some data from the cloud. The function itself is a regular python function but under the hood, it uses asyncio. So, I create an event loop with i

36. https://stackoverflow.com/questions/57024533/trouble-in-optimizing-asyncio-with-concurrent-futures
   Trouble in Optimizing asyncio with concurrent futures
   I'm trying to run asyncio task concurrently on each worker thread of concurrent.futures Threadpool. However, I couldn't achieve the desired outcome. async def say_after(delay, message): logging.info(f

37. https://stackoverflow.com/questions/66247720/understanding-behavior-of-asyncio-set-result-as-it-relates-to-slow-callback-dura
   Understanding behavior of asyncio set_result as it relates to slow_callback_duration
   I'm attempting to debug performance of a running production python web service, built on top of tornado using uvloop as the asyncio event loop. In trying to improve the concurrency, I'm looking to fin

38. https://stackoverflow.com/questions/72919537/runtimeerror-event-loop-is-closed-asyncio-aiohttp-concurrent-request
   Runtimeerror: Event loop is closed - asyncio, aiohttp, concurrent request
   I am very new to async programming. Environment- Win11,Python 3.10.5. I am trying to make concurrent requests and obtain the results in a list simply. I've tried going through the suggestions on stack

39. https://stackoverflow.com/questions/75471729/use-cases-for-threading-and-asyncio-in-python
   Use cases for threading and asyncio in python
   I've read quite a few articles on threading and asyncio modules in python and the major difference I can seem to draw (correct me if I'm wrong) is that in, threading : multiple threads can be used to 

40. https://stackoverflow.com/questions/75988992/how-can-i-inspect-the-internal-state-of-an-asyncio-event-loop
   How can I inspect the internal state of an asyncio event loop?
   I have a Python program that uses asyncio . When concurrency is high, a particular part of the program hangs. I would like to inspect the state of the asyncio event loop myself, to try and understand 

41. https://stackoverflow.com/questions/78171567/is-uvicorn-used-for-an-external-threadpool-or-an-internal-event-loop-which-runs
   Is uvicorn used for an external threadpool or an internal event loop which runs in the main (single)
   FastAPI uses uvicorn package to run the script: main:app --reload The docs explain that: Uvicorn is an ASGI web server implementation for Python... The ASGI specification fills this gap, and means we'

42. https://stackoverflow.com/questions/79626334/what-happens-to-the-asyncio-event-loop-when-multiple-cpu-bound-tasks-run-concurr
   What happens to the asyncio event loop when multiple CPU-bound tasks run concurrently in a ThreadPoo
   I'm working on an asynchronous Python application (using FastAPI/Starlette/asyncio) that needs to offload synchronous, CPU-bound tasks to a thread pool ( ThreadPoolExecutor ) to avoid blocking the eve

43. https://superfastpython.com/asyncio-event-loop-separate-thread/
   Asyncio Event Loop in Separate Thread - Super Fast Python
   We can create coroutines and send them to the event loop for execution via the asyncio.run_coroutine_threadsafe() method.

44. https://superfastpython.com/asyncio-multiple-event-loops/
   Asyncio Run Multiple Concurrent Event Loops - Super Fast Python
   We can run multiple concurrent asyncio event loops by starting and running each new event loop in a separate thread. Each thread can host and manage one event loop.

45. https://superfastpython.com/category/asyncio/page/3/
   Python Asyncio Archives - Page 3 of 20 - Super Fast Python
   Tutorials on the asyncio module for concurrency in Python. ... We can run an asyncio event loop " forever " , until explicitly stopped or ...

46. https://trent.me/articles/pytorch-and-python-free-threading/
   PyTorch and Python Free-Threading: Unlocking multi-threaded parallel inference on PyTorch models
   trent.me

47. https://tutorialedge.net/python/concurrency/asyncio-event-loops-tutorial/
   Asyncio Event Loops Tutorial | TutorialEdge.net
   The main component of any asyncio based Python program has to be the underlying event loop. ... event loop we ’ ll use asyncio.get_event_loop() ...

48. https://www.aeracode.org/2018/02/19/python-async-simplified/
   Python & Async Simplified
   aeracode.org

49. https://www.c-sharpcorner.com/article/python-asyncio-complete-practical-guide-for-concurrent-io/
   Python asyncio — Complete Practical Guide for Concurrent I/O
   Unlock Python's concurrency potential with asyncio! This practical guide covers coroutines, event loops, and non-blocking I/O for building high-performance applications. Learn to handle multiple tasks

50. https://www.codersjungle.com/2025/09/11/how-to-understand-and-use-the-asyncio-event-loop-in-python/
   How to understand and use the asyncio event loop in Python
   The asyncio event loop is at the heart of asynchronous programming in Python. ... www.pythonfaq.net/how-to-understand-and-use-the-asyncio-event-loop ...

51. https://www.educative.io/blog/concurrency-in-python
   Python Concurrency: Making sense of asyncio - Educative
   Python's asyncio module achieves high concurrency on a single thread by using an event loop that switches between tasks at await points, avoiding the complexity of thread-safe code and the memory over

52. https://www.iamraghuveer.com/posts/python-asyncio-event-loop-internals/
   I am Raghuveer | Python AsyncIO: Event Loop Internals and
   Home / Python / Python AsyncIO: Event Loop Internals and Practi... ... AsyncIO is Python's built-in concurrency model for I/O-bound workloads.

53. https://www.inexture.com/blog/python-async-await-concurrency-optimization/
   Python AsyncIO & Concurrency Guide | async/await, Tasks
   Learn how to use Python AsyncIO for high-performance applications. Covers async/await, event loops, tasks, concurrency models, FastAPI, async databases, benchmarks, and best practices.

54. https://www.pythonfaq.net/how-to-understand-and-use-the-asyncio-event-loop-in-python/
   How to understand and use the asyncio event loop in Python
   The asyncio event loop is at the heart of asynchronous programming in Python. ... into asyncio, consider how coroutines interact with event loops and ...

55. https://www.pythontutorial.net/python-concurrency/python-event-loop/
   Python Event Loop
   Python Event Loop Summary: in this tutorial, you'll learn about the Python event loop and how Python uses it to achieve the concurrency model using a single thread. Introduction to the Python event lo

56. https://www.semanticscholar.org/paper/Applications-with-asyncio-and-Twisted-Williams-Benfield/870ec0448ec1f037b837438dbd59b59cc740230b
   Applications with asyncio and Twisted
   TLDRThe asyncio package, included with Python implementations since version 3.4, standardizes a suite of APIs for asynchronous, event-driven network programs and specifies an event loop interface that

57. https://www.semanticscholar.org/paper/Event-driven-industrial-robot-control-architecture-Semeniuta-Falkman/a9d766d6fd3d61dbd502da03ae4f818f85898e6e
   Event-driven industrial robot control architecture for the Adept V+ platform
   TLDRThe proposed architecture is based on the robot controller providing a TCP/IP server and a collection of robot skills, and a high-level control module deployed to a dedicated computing device that

58. https://www.semanticscholar.org/paper/Event-driven-industrial-robot-control-architecture-Semeniuta-Falkman/aadab6dee241c636387b932a731caef7de92254e
   Event-driven industrial robot control architecture for the Adept V+ platform.
   TLDRThe architecture is based on the robot controller providing a TCP/IP server and a collection of robot skills, and a high-level control module deployed to a dedicated computing device that facilita

59. https://www.semanticscholar.org/paper/PyHLS%3A-Intermediate-Representation-for-Versatile-Cieszewski/b57ddb7929b674d5343e486ae5c2e18bd652d656
   PyHLS: Intermediate Representation for Versatile High-Level Synthesis
   TLDRAn Intermediate Representation (IR)-centric HLS flow—PyHLS— is proposed that explicitly introduces an abstraction layer between algorithm and Register- Transfer Level (RTL) design, and formalizes 

60. https://www.semanticscholar.org/paper/Pytch-%E2%80%94-an-environment-for-bridging-block-and-text-Strong-North/bde25648da1a1e5904361eecbf409fc503d3418c
   Pytch — an environment for bridging block and text programming styles (Work in progress)
   TLDRThis paper introduces a new programming system, Pytch, which embodies “Scratch-Oriented programming” in Python using a web-based environment that requires no local setup, and offers the programmin

61. https://www.semanticscholar.org/paper/Python-Gets-an-Event-Loop-(Again)-Beazley/3fa75a0063817a91b1c0311470b39dafc110b627
   Python Gets an Event Loop (Again)
   TLDRA bit of historical perspective is given as well as some examples of using the new asyncio module to the standard library in Python 3.4.Expand

62. https://www.semanticscholar.org/paper/Python-Gets-an-Event-Loop-(again)-D.AVIDBEA/c1c7879907a2fd5be8cc1635bb547370e1830341
   Python Gets an Event Loop (again)
   TLDRA bit of historical perspective is given as well as some examples of using the new asyncio module to the standard library, which has been floating around the Python world for much longer than that

63. https://www.semanticscholar.org/paper/The-impact-of-asynchronous-and-multithreaded-query-Makarov-Larin/ce0155a683f5ec546e6edcdc3ff578a01751c578
   The impact of asynchronous and multithreaded query processing models on the performance of server-si
   TLDRThe main conclusions of the study are recommendations on the use of asynchronous technologies in high-load I/O tasks and multithreaded approaches in computationally complex scenarios.Expand

64. https://www.semanticscholar.org/paper/TracktorLive%3A-an-integrated-real-time-object-and-Minasandra-Sridhar/455e405ec2528dd82e5b82aeae11c35109250e72
   TracktorLive: an integrated real-time object tracking and response system
   TLDRTracktorLive is introduced, an open-source Python package designed to overcome challenges through concurrency and a modular, ‘cassette’-based architecture that can help democratize real-time track

65. https://www.semanticscholar.org/paper/Working-with-Event-Loops-Tahrioui/ea267b563f62044458f54907f485893df8d77f02
   Working with Event Loops
   

66. https://yoric.github.io/post/quite-a-few-words-about-async/
   (Quite) A Few Words About Async
   yoric.github.io
