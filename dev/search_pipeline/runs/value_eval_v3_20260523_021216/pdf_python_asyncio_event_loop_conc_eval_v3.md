# Value Eval v3 — pdf × python asyncio event loop concurrency

**Mode:** pdf  **Query:** python asyncio event loop concurrency  **Pool (filtered):** 59

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 11 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1929 |
| M7 C3+InstrPrefix | 2016 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1574 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 8791 |
| M12 LLM-Selector | 13420 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.053 | 1/10 |
| M2 RRF post-bucket | 0.053 | 1/10 |
| M3 Structural URL | 0.053 | 1/10 |
| M4 BM25 vanilla | 0.176 | 3/10 |
| M5 BM25-Capped | 0.176 | 3/10 |
| M6 C3 Cross-Encoder | 0.333 | 5/10 |
| M7 C3+InstrPrefix | 0.429 | 6/10 |
| M8 RRF+C3 Hybrid | 0.176 | 3/10 |
| M9 SPLADE | 0.250 | 4/10 |
| M10 SPLADE+C3 | 0.250 | 4/10 |
| M11 C3→LLM-Filter | 0.176 | 3/10 |
| M12 LLM-Selector | 0.111 | 2/10 |

## Pool (oracle input — url/title/snippet)

1. http://103.203.175.90:81/fdScript/RootOfEBooks/E%20Book%20collection%20-%202026%20-%20H/AI%20and%20DS/Python%20Concurrency%20with%20asyncio%20by%20Matthew%20Fowler%20(2022).pdf
   Python Concurrency with asyncio (2022)
   Python Concurrency with asyncio (2022)103.203.175http://103.203.175.90 › fdScript › RootOfEBooks103.203.175http://103.203.175.90 › fdScript › RootOfEBooksPDF... event loop to achieve concurrency using

2. http://aosabook.org/en/500L/a-web-crawler-with-asyncio-coroutines.html
   A Web Crawler With asyncio Coroutines
   aosabook.org

3. http://techspot.zzzeek.org/2015/02/15/asynchronous-python-and-databases/
   Asynchronous Python and Databases
   techspot.zzzeek.org

4. https://archive.fosdem.org/2017/schedule/event/python_coroutines/attachments/slides/1462/export/events/attachments/python_coroutines/slides/1462/AsyncProgrammingInPython.pdf
   Asynchronous programming with Coroutines - in Python
   Asynchronous programming with Coroutines - in PythonFOSDEM 2026https://archive.fosdem.org › attachments › slidesFOSDEM 2026https://archive.fosdem.org › attachments › slidesPDF31 Jan 2017 — asyncio cal

5. https://archive.org/download/python-programming-collection-pdf-ebooks-all-you-need/Using%20Asyncio%20in%20Python%203_%20Understanding%20Python%27s%20Asynchronous%20Programming%20Features%20%28CONV%29%20-%20Caleb%20Hattingh%20%28O%27Reilly%20Media%3BFree%20Programming%20Ebooks%3B2018%29.pdf
   PDF Using Asyncio in Python 3 - Archive.org
   More practical information for shutdown handling is presented later in the book. asyncio in Python exposes a great deal of the underlying machinery around the event loop— and requires you to be aware 

6. https://blog.nelhage.com/post/concurrent-error-handling/
   From error-handling to structured concurrency
   blog.nelhage.com

7. https://charlesleifer.com/blog/asyncio/
   AsyncIO Thoughts
   charlesleifer.com

8. https://concurp.pages.forge.hefr.ch/2022-2023/website/pdf/280_EventLoop.pdf
   Event loops
   Event loopsHES-SO Fribourghttps://concurp.pages.forge.hefr.ch › website › pdfHES-SO Fribourghttps://concurp.pages.forge.hefr.ch › website › pdfPDF• Setup of event-loop in Python → asyncio. Page 3. 3. 

9. https://doi.org/10.1007/978-1-4842-3742-7_9
   Applications with asyncio and Twisted
   Williams, M. et al. (2019), Expert Twisted

10. https://doi.org/10.1007/978-1-4842-4401-2_2
   Working with Event Loops
   Python version 3.4 has adopted a powerful framework to support concurrent execution of code: asyncio. This framework uses event loops to orchestrate the callbacks and asynchronous tasks. Event loops l

11. https://doi.org/10.1007/978-1-4842-8140-6_1
   (A)synchronous Python
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

12. https://doi.org/10.1007/978-1-4842-8140-6_13
   Testing
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

13. https://doi.org/10.1007/978-1-4842-8140-6_17
   History
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

14. https://doi.org/10.1007/978-1-4842-8140-6_2
   Modern Asynchronous Python The Building Blocks
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

15. https://doi.org/10.1007/978-1-4842-8140-6_6
   asyncio Streams
   de Groot, C. (2022), Asynchronous Python Programming with Asyncio and Async/await

16. https://doi.org/10.1007/978-3-030-25943-3_34
   Concurrency with AsyncIO
   Hunt, J. (2019), Undergraduate Topics in Computer Science

17. https://doi.org/10.1007/978-3-031-40336-1
   Advanced Guide to Python 3 Programming
   

18. https://doi.org/10.1007/978-3-031-40336-1_43
   Concurrency with AsyncIO
   Hunt, J. (2023), Undergraduate Topics in Computer Science

19. https://doi.org/10.1007/979-8-8688-1261-3_16
   Asyncio
   Divakaran, A. (2025), Deep Dive Python

20. https://doi.org/10.1007/s41781-021-00053-3
   Performance of Julia for High Energy Physics Analyses
   

21. https://doi.org/10.1109/access.2020.3008954
   Control and Visualisation of a Software Defined Radio System on the Xilinx RFSoC Platform Using the 
   The availability of commercial Radio Frequency System on Chip (RFSoC) devices brings new possibilities for implementing Software Defined Radio (SDR) systems. Such systems are of increasing interest gi

22. https://doi.org/10.1109/ojits.2023.3266800
   Infrastructure-Based Digital Twins for Cooperative, Connected, Automated Driving and Smart Road Serv
   Driving requires continuous decision making from a driver taking into account all available relevant information. Automating driving tasks also automates the related decisions. However, humans are ver

23. https://doi.org/10.1145/3445814.3446701
   Nightcore: efficient and scalable serverless computing for latency-sensitive, interactive microservi
   The microservice architecture is a popular software engineering approach for building flexible, large-scale online services. Serverless functions, or function as a service (FaaS), provide a simple pro

24. https://doi.org/10.3390/en13153770
   Distributed Power Hardware-in-the-Loop Testing Using a Grid-Forming Converter as Power Interface
   This paper presents an approach to extend the capabilities of smart grid laboratories through the concept of Power Hardware-in-the-Loop (PHiL) testing by re-purposing existing grid-forming converters.

25. https://doi.org/10.4018/ijswis.2016100102
   Managing Large Amounts of Data Generated by a Smart City Internet of Things Deployment
   The Smart City concept is being developed from a lot of different axes encompassing multiple areas of social and technical sciences. However, something that is common to all these approaches is the ce

26. https://doi.org/10.47667/ijpasr.v4i2.202
   Python TCP/IP libraries: A Review
   The Internet's core is TCP/IP, which stands for Transmission Control Protocol/Internet Protocol. It connects network devices on the internet via communication protocols. Python has several TCP/IP pack

27. https://doi.org/10.7256/2454-0714.2018.2.25851
   Савостин П.А., Ефремова Н.Э. Практическое применение асинхронного программирования на языке Python п
   (2018), Программные системы и вычислительные методы

28. https://dugarsumit.github.io/files/multi-processing-threading-asyncio.pdf
   Multiprocessing vs Multithreading vs Async IO
   Multiprocessing vs Multithreading vs Async IOGitHubhttps://dugarsumit.github.io › files › multi-process...GitHubhttps://dugarsumit.github.io › files › multi-process...PDFThe general concept of asyncio

29. https://edu.anarcho-copy.org/Programming%20Languages/Python/using-asyncio-python-understanding-asynchronous.pdf
   Using Asyncio in Python
   Using Asyncio in PythonAnarcho-Copyhttps://edu.anarcho-copy.org › Python › using-asy...Anarcho-Copyhttps://edu.anarcho-copy.org › Python › using-asy...PDFThis is how you tell Twisted to use the asynci

30. https://emptysqua.re/blog/why-should-async-get-all-the-love/
   Why Should Async Get All The Love?: Advanced Control Flow With Threads
   emptysqua.re

31. https://fractalideas.com/blog/sans-io-when-rubber-meets-road/
   Sans I/O when rubber meets the road
   fractalideas.com

32. https://github.com/Rishabh-creator601/Books/blob/master/python_books/Python_Concurrency_with_asyncio_Matthew_Fowler.pdf
   Python_Concurrency_with_asyn...
   Python_Concurrency_with_asyn...GitHubhttps://github.com › blob › master › python_books › Pyt...GitHubhttps://github.com › blob › master › python_books › Pyt...Books / PDFS / EPUBS for different fields

33. https://github.com/gegasnake/django_books/blob/main/Python%20Concurrency%20with%20asyncio.pdf
   PDF Python Concurrency with asyncio.pdf - GitHub
   all the books I have about Django, Django rest api and Python - django_books/Python Concurrency with asyncio.pdf at main · gegasnake/django_books

34. https://indico.gsi.de/event/17490/contributions/71045/attachments/43482/61031/Event-driven%20Programming%20with%20Python%20asyncio.pdf
   Event-driven Programming with Python asyncio - GSI Indico
   Web resultsEvent-driven Programming with Python asyncio - GSI IndicoGSI Indicohttps://indico.gsi.de › contributions › attachmentsGSI Indicohttps://indico.gsi.de › contributions › attachmentsPDF○ Event

35. https://link.springer.com/content/pdf/10.1007/978-3-030-25943-3_34.pdf
   PDF Concurrency with AsyncIO - Springer
   The asyncio.run() function was introduced in Python 3.7 (older versions of Python such as Python 3.6 required you to explicitly obtain a reference to the Event Loop and to run the root async function 

36. https://media.githubusercontent.com/media/Rishabh-creator601/Books/refs/heads/master/python_books/Python_Concurrency_with_asyncio_Matthew_Fowler.pdf
   PDF Python Concurrency with asyncio
   This makes asynchronous code easy to read and understand, as it looks like the sequential flow most software engineers are familiar with. asyncio is a library to execute these coroutines in an asynchr

37. https://medium.com/@yeraydiazdiaz/asyncio-for-the-working-python-developer-5c468e6e2e8e
   AsyncIO for the Working Python Developer
   medium.com/@yeraydiazdiaz

38. https://pythonrepo.com/catalog/python-concurrent-and-parallel-execution_newest_1
   Python Concurrency and Parallelism Libraries | PythonRepo
   Awesome asyncio A carefully curated list of awesome Python asyncio frameworks, libraries, software and resources. ... Python library for async ...

39. https://realpython.com/async-io-python/
   Python's asyncio: A Hands-On Walkthrough - Real Python
   Interactive Quiz Python's asyncio: A Hands-On Walkthrough Test your knowledge of `asyncio` concurrency with this quiz that covers coroutines, event loops, and efficient I/O-bound task management.

40. https://realpython.com/lessons/asyncio-event-loop/
   The asyncio Event Loop (Video) – Real Python
   What’s going on here? Well, what needs to happen is I need to actually create what’s called an event loop, and the event loop is what’s going ...

41. https://sciarium.com/file/546119/
   Download Fowler Matthew. Python Concurrency with asyncio [PDF]
   Python Concurrency with asyncio teaches you how to boost Python's performance by applying a variety of concurrency techniques. You'll learn how the complex-but-powerful asyncio library can achieve con

42. https://sschwarzer.com/download/concurrency_pycon_de2018.pdf
   Concurrency in Python Concepts, frameworks and best practices
   Concurrency in Python Concepts, frameworks and best practicessschwarzer.comhttps://sschwarzer.com › download › concurrency...sschwarzer.comhttps://sschwarzer.com › download › concurrency...PDF26 Oct 2

43. https://stackoverflow.com/questions/29269370/how-to-properly-create-and-run-concurrent-tasks-using-pythons-asyncio-module
   How to properly create and run concurrent tasks using python's asyncio module?
   I am trying to properly understand and implement two concurrently running Task objects using Python 3's relatively new asyncio module. In a nutshell, asyncio seems designed to handle asynchronous proc

44. https://stackoverflow.com/questions/49584561/run-infinite-loop-in-asyncio-event-loop-running-off-the-main-thread
   run infinite loop in asyncio event loop running off the main thread
   I wrote code that seems to do what I want, but I'm not sure if it's a good idea since it mixes threads and event loops to run an infinite loop off the main thread. This is a minimal code snippet that 

45. https://stackoverflow.com/questions/53268438/python-asyncio-within-multiprocessing-one-event-loop-per-process
   Python asyncio within Multiprocessing. One event loop per process
   I am writing a function for my team that will download some data from the cloud. The function itself is a regular python function but under the hood, it uses asyncio. So, I create an event loop with i

46. https://stackoverflow.com/questions/57024533/trouble-in-optimizing-asyncio-with-concurrent-futures
   Trouble in Optimizing asyncio with concurrent futures
   I'm trying to run asyncio task concurrently on each worker thread of concurrent.futures Threadpool. However, I couldn't achieve the desired outcome. async def say_after(delay, message): logging.info(f

47. https://stackoverflow.com/questions/60026975/event-loop-error-in-asyncio-lock-when-instantiated-multiple-times
   python - Event loop error in asyncio Lock when instantiated
   So perhaps it has something to do with the event loops state after asyncio.run is called. ... Running event loop (inside asyncio.run ) is meant to be ...

48. https://stackoverflow.com/questions/66247720/understanding-behavior-of-asyncio-set-result-as-it-relates-to-slow-callback-dura
   Understanding behavior of asyncio set_result as it relates to slow_callback_duration
   I'm attempting to debug performance of a running production python web service, built on top of tornado using uvloop as the asyncio event loop. In trying to improve the concurrency, I'm looking to fin

49. https://stackoverflow.com/questions/72715083/pytest-asyncio-event-is-bound-to-a-different-event-loop-event-loop-is-closed
   python - Pytest asyncio event is bound to a different event
   ... event_loop() - > Iterator[asyncio.AbstractEventLoop] : " Initialize the event loop " loop = ... asyncio async def ...

50. https://stackoverflow.com/questions/72919537/runtimeerror-event-loop-is-closed-asyncio-aiohttp-concurrent-request
   Runtimeerror: Event loop is closed - asyncio, aiohttp, concurrent request
   I am very new to async programming. Environment- Win11,Python 3.10.5. I am trying to make concurrent requests and obtain the results in a list simply. I've tried going through the suggestions on stack

51. https://stackoverflow.com/questions/75471729/use-cases-for-threading-and-asyncio-in-python
   Use cases for threading and asyncio in python
   I've read quite a few articles on threading and asyncio modules in python and the major difference I can seem to draw (correct me if I'm wrong) is that in, threading : multiple threads can be used to 

52. https://stackoverflow.com/questions/75988992/how-can-i-inspect-the-internal-state-of-an-asyncio-event-loop
   How can I inspect the internal state of an asyncio event loop?
   I have a Python program that uses asyncio . When concurrency is high, a particular part of the program hangs. I would like to inspect the state of the asyncio event loop myself, to try and understand 

53. https://stackoverflow.com/questions/78171567/is-uvicorn-used-for-an-external-threadpool-or-an-internal-event-loop-which-runs
   Is uvicorn used for an external threadpool or an internal event loop which runs in the main (single)
   FastAPI uses uvicorn package to run the script: main:app --reload The docs explain that: Uvicorn is an ASGI web server implementation for Python... The ASGI specification fills this gap, and means we'

54. https://stackoverflow.com/questions/79626334/what-happens-to-the-asyncio-event-loop-when-multiple-cpu-bound-tasks-run-concurr
   What happens to the asyncio event loop when multiple CPU-bound tasks run concurrently in a ThreadPoo
   I'm working on an asynchronous Python application (using FastAPI/Starlette/asyncio) that needs to offload synchronous, CPU-bound tasks to a thread pool ( ThreadPoolExecutor ) to avoid blocking the eve

55. https://superfastpython.com/asyncio-event-loop-exception-handler/
   Asyncio Event Loop Exception Handler - Super Fast Python
   By default, unhandled exceptions in asyncio programs cause the event loop to emit a warning and are reported using a default exception handler once ...

56. https://superfastpython.com/asyncio-event-loop-separate-thread/
   Asyncio Event Loop in Separate Thread - Super Fast Python
   It also provides a point of change if an alternate approach is preferred for starting the event loop, such as using the low-level asyncio API.

57. https://superfastpython.com/asyncio-multiple-event-loops/
   Asyncio Run Multiple Concurrent Event Loops - Super Fast Python
   Scalability : Running multiple asyncio event loops concurrently allows the program to scale better, especially in scenarios where there are many ...

58. https://superfastpython.com/asyncio-run-forever/
   superfastpython.com/asyncio-run-forever
   

59. https://trent.me/articles/pytorch-and-python-free-threading/
   PyTorch and Python Free-Threading: Unlocking multi-threaded parallel inference on PyTorch models
   trent.me

60. https://welib.org/md5/2a6542ca9655d08c97dacbe92cbce3b0
   Python Concurrency with asyncio ( PDF, 6.4 MB ) - WeLib
   Python Concurrency with asyncio teaches you how to boost Python's performance by applying a variety of concurrency techniques. You'll learn how the complex-but-powerful asyncio library can achieve con

61. https://www.aeracode.org/2018/02/19/python-async-simplified/
   Python & Async Simplified
   aeracode.org

62. https://www.deeplearningdaily.com/quiz-hands-on-python-3-concurrency-with-the-asyncio-module/
   Quiz: Hands-On Python 3 Concurrency With the asyncio Module
   ... asyncio.run() , and concurrent execution ... For a quick refresher before you start, check out Hands-On Python 3 Concurrency With the asyncio Module .

63. https://www.pythonsheets.com/notes/multitasking/python-asyncio.html
   Asyncio — pysheeet
   import asyncio > from concurrent.futures import ThreadPoolExecutor > e = ThreadPoolExecutor () > loop = asyncio .

64. https://www.researchgate.net/publication/329484717_Applications_with_asyncio_and_Twisted_Event-Driven_and_Asynchronous_Programming_with_Python
   Event-Driven and Asynchronous Programming with Python
   Event-Driven and Asynchronous Programming with PythonResearchGatehttps://www.researchgate.net › publication › 32948471...ResearchGatehttps://www.researchgate.net › publication › 32948471...The asyncio

65. https://www.scribd.com/document/680700921/Python-Asyncio
   Mastering Python Asyncio Essentials | PDF | Process (Computing ...
   This document provides a comprehensive guide to using asyncio in Python. It discusses asynchronous programming and how asyncio allows non-blocking I/O and concurrency using coroutines. The guide defin

66. https://www.scribd.com/document/930453718/asyncio
   Understanding Python's asyncio Library | PDF
   Understanding Python's asyncio Library | PDFScribdhttps://www.scribd.com › document › asyncioScribdhttps://www.scribd.com › document › asyncioasyncio is a library to write **concurrent** code using th

67. https://www.semanticscholar.org/paper/Applications-with-asyncio-and-Twisted-Williams-Benfield/870ec0448ec1f037b837438dbd59b59cc740230b
   Applications with asyncio and Twisted
   TLDRThe asyncio package, included with Python implementations since version 3.4, standardizes a suite of APIs for asynchronous, event-driven network programs and specifies an event loop interface that

68. https://www.semanticscholar.org/paper/Event-driven-industrial-robot-control-architecture-Semeniuta-Falkman/a9d766d6fd3d61dbd502da03ae4f818f85898e6e
   Event-driven industrial robot control architecture for the Adept V+ platform
   TLDRThe proposed architecture is based on the robot controller providing a TCP/IP server and a collection of robot skills, and a high-level control module deployed to a dedicated computing device that

69. https://www.semanticscholar.org/paper/Event-driven-industrial-robot-control-architecture-Semeniuta-Falkman/aadab6dee241c636387b932a731caef7de92254e
   Event-driven industrial robot control architecture for the Adept V+ platform.
   TLDRThe architecture is based on the robot controller providing a TCP/IP server and a collection of robot skills, and a high-level control module deployed to a dedicated computing device that facilita

70. https://www.semanticscholar.org/paper/PyHLS%3A-Intermediate-Representation-for-Versatile-Cieszewski/b57ddb7929b674d5343e486ae5c2e18bd652d656
   PyHLS: Intermediate Representation for Versatile High-Level Synthesis
   TLDRAn Intermediate Representation (IR)-centric HLS flow—PyHLS— is proposed that explicitly introduces an abstraction layer between algorithm and Register- Transfer Level (RTL) design, and formalizes 

71. https://www.semanticscholar.org/paper/Pytch-%E2%80%94-an-environment-for-bridging-block-and-text-Strong-North/bde25648da1a1e5904361eecbf409fc503d3418c
   Pytch — an environment for bridging block and text programming styles (Work in progress)
   TLDRThis paper introduces a new programming system, Pytch, which embodies “Scratch-Oriented programming” in Python using a web-based environment that requires no local setup, and offers the programmin

72. https://www.semanticscholar.org/paper/Python-Gets-an-Event-Loop-(Again)-Beazley/3fa75a0063817a91b1c0311470b39dafc110b627
   Python Gets an Event Loop (Again)
   TLDRA bit of historical perspective is given as well as some examples of using the new asyncio module to the standard library in Python 3.4.Expand

73. https://www.semanticscholar.org/paper/Python-Gets-an-Event-Loop-(again)-D.AVIDBEA/c1c7879907a2fd5be8cc1635bb547370e1830341
   Python Gets an Event Loop (again)
   TLDRA bit of historical perspective is given as well as some examples of using the new asyncio module to the standard library, which has been floating around the Python world for much longer than that

74. https://www.semanticscholar.org/paper/The-impact-of-asynchronous-and-multithreaded-query-Makarov-Larin/ce0155a683f5ec546e6edcdc3ff578a01751c578
   The impact of asynchronous and multithreaded query processing models on the performance of server-si
   TLDRThe main conclusions of the study are recommendations on the use of asynchronous technologies in high-load I/O tasks and multithreaded approaches in computationally complex scenarios.Expand

75. https://www.semanticscholar.org/paper/TracktorLive%3A-an-integrated-real-time-object-and-Minasandra-Sridhar/455e405ec2528dd82e5b82aeae11c35109250e72
   TracktorLive: an integrated real-time object tracking and response system
   TLDRTracktorLive is introduced, an open-source Python package designed to overcome challenges through concurrency and a modular, ‘cassette’-based architecture that can help democratize real-time track

76. https://www.semanticscholar.org/paper/Working-with-Event-Loops-Tahrioui/ea267b563f62044458f54907f485893df8d77f02
   Working with Event Loops
   

77. https://yoric.github.io/post/quite-a-few-words-about-async/
   (Quite) A Few Words About Async
   yoric.github.io
