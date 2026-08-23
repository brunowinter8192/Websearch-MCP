<!-- source: https://github.com/adbar/trafilatura/issues/25 -->

Difference between this and using readability
Difference between this and using readability
Hi!  
Great library, but I am trying to figure out if we should swap from using readability on which this builds.  
Apart from manually checking the quality for our corpus there is no easy way for me to compare performance.  
Would you be able to explain the differences between the actual text extraction approaches?  
Thanks in advance!  
D
* It grounds on a cascade of extraction methods: first a series of heuristics for main text discovery and conversion, then two external libraries, then a baseline extraction if nothing worked (basically all text tags such as`
`).
* Since it defaults to`readability-lxml`if extraction fails or appears to have failed, you'll still benefit from the efficiency of this (very good) library,`justext`is also used as a fallback. In theory (and the benchmarks confirm it)`trafilatura`has a better website coverage without sacrificing precision. Its series of heuristics and`readability-lxml`are mostly used, the rest only applies to rare cases.
* If you're also interested in extracting comments, this library can do it while`readability`cannot.
* fallback does not seem to work as I can get no text from your lib, but text from readability
I am not sure if you will find this useful, but I am providing you some URLs on which the two libs differ the most, the following URLs are where your lib extracts more text:
This batch is where readability extracts more text:
Thank you very much for the lists, I believe they are useful! Could you please clarify the following points? - Which version of trafilatura are you using, with which parameters? I assume you use the last readability-lxml version? (0.8.1) - Sometimes less text is better (boilerplate elements hopefully missing), similarly the fact that there is more text isn't necessary significant. The presence of footers doesn't seem too good, do you have a few examples at hand? - Do you have a list of URLs for which trafilatura doesn't return any text whatsoever (although it probably should)? To sum up, minor differences in text output are not necessarily a concern, I'd say that discrepancies over 5-10% are meaningful.
* within the list I provided of URLs where readability returns more, there are many where trafilatura returns None
Some fixes could be needed for a few patterns found in these webpages (partly addressed in[`62b1e9a`](https://github.com/adbar/trafilatura/commit/62b1e9ab249edc1ca003afb7b86c949c597a4692)and[`25a08ed`](https://github.com/adbar/trafilatura/commit/25a08edec50b300894d033c07ef71f2436d0260e)), that said text extraction remains a balancing act... I added a few pages to the evaluation, things should get slightly better by the next release.
