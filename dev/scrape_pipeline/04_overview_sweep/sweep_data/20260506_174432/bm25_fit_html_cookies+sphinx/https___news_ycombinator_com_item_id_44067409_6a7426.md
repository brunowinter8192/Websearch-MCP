<!-- source: https://news.ycombinator.com/item?id=44067409 -->

I built Defuddle while working on Obsidian Web Clipper[1] (also MIT-licensed) because Mozilla's Readability[2] appears to be mostly abandoned, and didn't work well for many sites.  
In the end I found the python trifatura library to extract the best quality content with accurate meta data.
If you're using Go, I maintain Go ports of Readability[0] and Trafilatura[1]. They're actively maintained, and for Trafilatura, the extraction performance is comparable to the Python version.
for the curious: Trafilatura means "extrusion" in Italian.
(btw I think you meant trafilatura not trifatura)
It's a bit old, but I bench marked a number of the web extraction tools years ago,https://github.com/Nootka-io/wee-benchmarking-tool, resiliparse-plain was my clear winner at the time.
Even if you are not a obsidian user, the markdown extraction quality is the most reliable Ive seen.
Question: How did you validate this? You say it works better than readability but I don’t see any tests or datasets in the repo to evaluate accuracy or coverage. Would it be possible to share that as well?
Defuddle works quite differently from Readability. Readability tends to be overly conservative and tends to remove useful content because it tests blocks to find the beginning and end of the "main" content.
Defuddle is able to run multiple passes and detect if it returned no content to try and expand its results. It also uses a greater variety of techniques to clean the content — for example, by using a page's mobile styles to detect content that can be hidden.
Lastly, Defuddle is not only extracting the content but also standardizing the output (which Readability doesn't do). For example footnotes and code blocks all aim to output a single format, whereas Readability keeps the original DOM intact.
I would love to give Defuddle a try as a Readability replacement. However, for my use case I want to do in a Chrome extension background script (service worker). I have not been able to get Defuddle to work, while readability does (when combining with linkedom). So basically, while this works:
Is Mozilla's Readability really abandoned? The latest release (v0.6.0) is just 2 months ago, and its maintainer (Gijs) is pretty active on responding issues.
The Python analogues seem to be well maintained. I did my own implementation of the Readability algorithm years ago and dropped it in favor them, and I have a few scrapers going strong with regular updates.
[^0]:https://substance.reorx.com/
Is this the website intentionally obscuring the content to ensure they can serve their ads? If so how do they go about it?
Thank you for picking up this work :-)
i started working on my own alternative but life (and web clipper) derailed the work.
I would love something which reliably extracted a markdown back/forth from all the main LLM providers. I tried `defuddle` on a shared Gemini URL and it returned nothing but the "Sign In" link. Maybe I'm using your extractor wrong? How are you managing to get the rendered conversation HTML?
And with Pocket going away I might have to add save it later to it...
Excellent work. A modern alternative to readability was much needed. This is especially useful for building clean web context for LLMs. Thanks for open-sourcing this!
