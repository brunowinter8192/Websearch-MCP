# Effective rank aggregation for metasearching - ScienceDirect
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0164121210002438
**Domain:** www.sciencedirect.com
**Score:** 2.3
**Source:** scraped
**Query:** metasearch engine result fusion ranking paper

---

## [Journal of Systems and Software](https://www.sciencedirect.com/journal/journal-of-systems-and-software "Go to Journal of Systems and Software on ScienceDirect")
[Volume 84, Issue 1](https://www.sciencedirect.com/journal/journal-of-systems-and-software/vol/84/issue/1 "Go to table of contents for this volume/issue"), January 2011, Pages 130-143
# Effective rank aggregation for metasearching
Leonidas Akritidis, [Dimitrios Katsaros](https://www.sciencedirect.com/author/7005894738/dimitrios-s-katsaros)[Panayiotis Bozanis](https://www.sciencedirect.com/author/6602302218/panayiotis-bozanis)
Show more
Add to Mendeley
Share
Cite
[https://doi.org/10.1016/j.jss.2010.09.001](https://doi.org/10.1016/j.jss.2010.09.001 "Persistent link using digital object identifier")[Get rights and content](https://s100.copyright.com/AppDispatchServlet?publisherName=ELS&contentID=S0164121210002438&orderBeanReset=true)
## Abstract
Nowadays, mashup services and especially [metasearch engines](https://www.sciencedirect.com/topics/computer-science/metasearch-engine) play an increasingly important role on the Web. Most of users use them directly or indirectly to access and aggregate information from more than one data sources. Similarly to the rest of the search systems, the effectiveness of a metasearch engine is mainly determined by the quality of the results it returns in response to user queries. Since these services do not maintain their own document index, they exploit multiple search engines using a rank aggregation method in order to classify the collected results. However, the rank aggregation methods which have been proposed until now, utilize a very limited set of parameters regarding these results, such as the total number of the exploited resources and the rankings they receive from each individual resource. In this paper we present _QuadRank_ , a new rank aggregation method, which takes into consideration additional information regarding the query terms, the collected results and the [data correlated](https://www.sciencedirect.com/topics/computer-science/correlated-data) to each of these results (title, textual snippet, [URL](https://www.sciencedirect.com/topics/computer-science/uniform-resource-locator), individual ranking and others). We have implemented and tested _QuadRank_ in a real-world metasearch engine, _QuadSearch_ , a system developed as a [testbed](https://www.sciencedirect.com/topics/computer-science/testbed) for algorithms related to the wide problem of metasearching. The name _QuadSearch_ is related to the current number of the exploited engines (four). We have exhaustively tested _QuadRank_ for both effectiveness and efficiency in the real-world search environment of _QuadSearch_ and also, using a task from the recent TREC-2009 conference. The results we present in our experiments reveal that in most cases _QuadRank_ outperformed all component engines, another metasearch engine (Dogpile) and two successful rank aggregation methods, Borda Count and the Outranking Approach.
## Introduction
The lack of any specific structure and the vast amount of information published on the Web, makes it extremely difficult for the user to find the information s/he desires without any external help. As of February 2010, there are at least 19 general-purpose search engines1, as well as numerous special-purpose search engines. Their population is mainly justified by two reasons: (a) no ranking algorithm is broadly acceptable, although many users tend to consider _Google_ 's ranking method as the most successful; (b) no engine can achieve large coverage and high scalability. It is a common belief (Sugiura and Etzioni, 2000, Manning et al., 2008) that a single general purpose search engine for all Web data is unrealistic, since its processing power cannot scale up to the rapidly increasing and unlimited amount of Web data.
The tool which rapidly gains acceptance among the users is _metasearch engines_ (Meng et al., 2002). These systems operate like 

[Content truncated...]