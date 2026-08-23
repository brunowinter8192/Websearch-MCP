[FETCH]... ↓ https://seirdy.one/posts/2020/11/23/website-best-practices/        
| ✓ | ⏱: 1.55s 
[SCRAPE].. ◆ https://seirdy.one/posts/2020/11/23/website-best-practices/        
| ✓ | ⏱: 0.25s 
[COMPLETE] ● https://seirdy.one/posts/2020/11/23/website-best-practices/        
| ✓ | ⏱: 1.80s 
# Content from: https://seirdy.one/posts/2020/11/23/website-best-practices/

## Before you begin
The following applies to minimal websites that focus primarily on text. It does not apply to websites that have a lot of non-textual content. It also does not apply to websites that focus more on generating revenue or pleasing investors than being inclusive.
This is a “living document” that I add to as I receive feedback. See the updated date and changelog after the post title.
If you find the article too long, just read the introduction and conclusion. The table of contents should help you skim.
Toggle table of contents
## Intro­duction
I realize not everybody’s going to ditch the Web and switch to Gemini or Gopher today (that’ll take, like, at least a month /s). Until that happens, here’s a non-exhaustive, highly-opinionated list of best practices for websites that focus primarily on text. I don’t expect anybody to fully agree with the list; nonetheless, the article should have at least some useful information for any web content author or front-end web developer.
### Inclusive design
My primary focus is [inclusive design](https://100daysofa11y.com/2019/12/03/accommodation-versus-inclusive-design/). Specifically, I focus on supporting _underrepresented ways to read a page_. Not all users load a page in a common web-browser and navigate effortlessly with their eyes and hands. Authors often neglect people who read through accessibility tools, tiny viewports, machine translators, “reading mode” implementations, the Tor network, printouts, hostile networks, and uncommon browsers, to name a few. I list more niches in [the conclusion](https://seirdy.one/posts/2020/11/23/website-best-practices/#conclusion). Compatibility with so many niches sounds far more daunting than it really is: if you only selectively override browser defaults and use plain-old, semantic HTML (POSH), you’ve done half of the work already.
One of the core ideas behind the flavor of inclusive design I present is inclusivity by default. Web pages shouldn’t use accessible overlays, reduced-data modes, or other personalizations if these features can be available all the time. Personalization isn’t always possible: Tor users, students using school computers, and people with restrictive corporate policies can’t “make websites work for them”; that’s a webmaster’s responsibility.
At the same time, many users do apply personalizations; sites should respect those personalizations whenever possible. Balancing these two needs is difficult. Some features conflict; you can’t display a light and dark color scheme simultaneously. Personalization is a fallback strategy to resolve conflicting needs. Dis­proportionately underrepresented needs deserve disproportionately greater attention, so they come before personal preferences instead of being relegated to a separate lane.
### Restricted enhancement
Another focus is minimalism. [Progressive enhancement](https://en.wikipedia.org/wiki/Progressive_enhancement) is a simple, safe idea that tries to incorporate some responsibility into the design process without rocking the boat too much. I don’t find it radical enough. I call my alternative approach “restricted enhancement”.
Restricted enhancement limits all enhancements to those that solve specific accessibility, security, performance, or significant usability problems faced by people besides the author. These enhancements must be made progressively when possible, with a preference for using older or more widespread features, taking into account unorthodox user agents. Purely-cosmetic changes should be kept to a minimum.
I’d like to re-iterate yet another time that this only applies to websites that primarily focus on text. If graphics, interactivity, etc. are an important part of your website, less of the article applies. My hope is for readers to consider a subset of this page the next time they build a website, and _address the trade-offs they make when they deviate._ I don’t expect—or want—anybody to follow all of my advice, because doing so would make the Web quite a boring place!
Our goal: make a textual website maximally inclusive, using restricted enhancement.
### Prior art
You can regard this article as an elaboration on existing work by the Web Accessibility Initiative (WAI).
I’ll cite the WAI’s [Techniques for WCAG 2.2](https://www.w3.org/WAI/WCAG22/Techniques/) a number of times. Each “Success Criterion” (requirement) of the WCAG has possible techniques. Unlike the Web Content Accessibility Guidelines (WCAG), the Techniques document does not list requirements; rather, it serves to non-exhaustively educate authors about _how_ to use specific technologies to comply with the WCAG. I don’t find much utility in the technology-agnostic goals enumerated by the WCAG without the accompanying technology-specific techniques to meet those goals.
I’ll also cite [Making Content Usable for People with Cognitive and Learning Disabilities](https://www.w3.org/TR/coga-usable/), by the WAI. The document lists eight objectives. Each objective has associated personas, and can be met by several design patterns.
### Why this article exists
Performance and accessibility guidelines are scattered across multiple WAI documents and blog posts. Moreover, guidelines tend to be overly general and avoid giving specific advice. Guidelines from different places tend to contradict each other, especially when they have different goals (e.g., security and accessibility). They also tend to be focused on large corporate sites rather than the simple text-oriented content the Web was made for.
I wanted to create a single reference with non-contradictory guidelines, containing advice more specific and opinionated than existing material. I also wanted to approach the very different aspects of site design from the same perspective and in the same place, allowing readers to draw connections between them.
## Security and privacy
One of the defining differences between textual websites and advanced Web 2.0 sites/apps is safety. Most browser vulnerabilities are related to modern Web features like JavaScript and WebGL. The simplicity of basic textual websites should guarantee some extra safety; however, webmasters need to take additional measures to ensure limited use of “modern” risky features.
### TLS
Hostile networks are the norm, and [your site is an attack vector](https://seirdy.one/notes/2022/08/03/on-enforcing-https/). All of the simplicity in the world won’t protect a page from unsafe content injection by an intermediary. Proper use of TLS protects against page alteration in transit and ensures a limited degree of privacy. Test your TLS setup with [testssl.sh](https://testssl.sh/) and [Webbkoll](https://webbkoll.dataskydd.net/).
If your OpenSSL (or equivalent) version is outdated or you don’t want to download and run a shell script, SSL Labs’ [SSL Server Test](https://www.ssllabs.com/ssltest/) should be equivalent to testssl.sh. Mozilla’s [HTTP Observatory](https://observatory.mozilla.org/) offers a subset of Webbkoll’s features and is a bit out of date (and requires JavaScript), but it also gives a beginner-friendly score. Most sites should strive for at least a 50, but a score of 100 or even 120 shouldn’t be too hard to reach.
A false sense of security is far worse than transparent insecurity. Don’t offer broken TLS ciphers, including TLS 1.0 and 1.1. Vintage computers can run TLS 1.2 implementations such as BearSSL surprisingly efficiently, leverage a TLS terminator, or they can use a plain unencrypted connection. [Ancienne 2.0 brings TLS 1.3 to 90s-era machines](https://oldvcr.blogspot.com/2022/07/crypto-ancienne-20-now-brings-tls-13-to.html). A broken cipher suite is security theater.
### Scripts and the Content Security Policy
Consider taking hardening measures to maximize the security benefits made possible by the simplicity of textual websites, starting with script removal.
JavaScript and WebAssembly are responsible for the bulk of modern web exploits. If that isn’t reason enough, most [non-mainstream search indexes](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/) have little to no support for JavaScript. Ideally, a text-oriented site can enforce a scripting ban at the [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) (CSP) level.
**Code snippet 1**: this is the CSP for my main website, with hashes removed for readability.  
```
default-src 'none';
img-src 'self';
media-src 'self';
style-src 'sha256-HASH';
frame-ancestors 'none';
base-uri 'none';
form-action FORM_DESTS;
manifest-src 'self';
upgrade-insecure-requests;
sandbox allow-same-origin allow-forms

```

`default-src: 'none'` implies `script-src: 'none'`, causing a compliant browser to forbid the loading of scripts. Furthermore, the `sandbox` CSP directive forbids a [wide variety of risky actions](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/sandbox). While `script-src` restricts script loading, `sandbox` can also restrict script execution with stronger defenses against script injection (e.g. by a browser add-on). I added the `allow-same-origin` parameter so that signed scripts (e.g. from add-ons) will still be able to function.
If you’re able to control your HTTP headers, then use headers instead of a `<meta http=equiv>` tag. In addition to not supporting certain directives, a CSP in a `<meta>` tag might let some items slip through.
> At the time of inserting the `meta` element to the document, it is possible that some resources have already been fetched. For example, images might be stored in the [list of available images](https://html.spec.whatwg.org/multipage/images.html#list-of-available-images) prior to dynamically inserting a `meta` element with an `http-equiv` attribute in the Content security policy state. Resources that have already been fetched are not guaranteed to be blocked by a Content Security Policy that’s enforced late. 
—HTML Living Standard, section 4.2.5.3: Pragma directives, [Content Security Policy state](https://html.spec.whatwg.org/multipage/semantics.html#attr-meta-http-equiv-content-security-policy)
### If you must enable scripts
Please use progressive enhancement (PE) throughout your site; every feature possible should be optional, and scripting is no exception.
I’m sure you’re a great person, but your readers might not know that; don’t expect them to trust your website. Your scripts should look as safe as possible to an untrusting eye. Avoid requesting permissions or using [sensitive APIs](https://browserleaks.com/javascript).
Finally, consider using your CSP to restrict script loading. If you must use inline scripts, selectively allow them with a hash or nonce. [Some recent CSP directives](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/trusted-types) restrict and enforce proper use of [trusted types](https://web.dev/trusted-types/).
### Third-party content
Third-party content will complicate the CSP, allow more actors to track users, possibly slow page loading, and create more points of failure. Some privacy-conscious users actually block third-party content: while doing so is fingerprintable, it can [reduce the amount of data collected about an already-identified user](https://seirdy.one/posts/2022/06/25/two-types-of-privacy/). Avoid third-party content, if at all possible.
Some web developers deliver resources using a third-party content delivery network (CDN), such as jsDelivr or Unpkg. Traditional wisdom held that doing so would allow different websites to re-use cached resources; however, [mainstream browsers partition their caches](https://privacycg.github.io/storage-partitioning/) to prevent this behavior.
If you must use third-party content, use [subresource integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity) (check the [SRI specification](https://www.w3.org/TR/SRI/)). This prevents alteration without your consent. If you wish to be extra careful, you could use SRI for first-party resources too.
Be sure to check the privacy policies for the third party services and subscribe to updates, as their practices could impact the privacy of all your users.
For embedded third-party content (e.g. images), give extra consideration to the [“Beyond alt-text” section](https://seirdy.one/posts/2020/11/23/website-best-practices/#beyond-alt-text). Your page should be as useful as possible if the embedded content becomes inaccessible.
## Optimal loading
Nearly every Internet user has to deal with unreliable connections every now and then, even the most privileged. Developing regions lack modern Internet infrastructure; high-ranking executives travel frequently. Everybody hits the worst end of the bell-curve.
Reducing load time is especially useful to poorly-connected users. For much of the world, connectivity comes in short bursts during which loading time is precious. Chances of a connection failure or packet loss increase with time.
Optimal loading is a complex topic. Broadly, it covers three overlapping categories: reducing payload size, delivering content early, and reducing the number of requests and round trips.
### Blocking resources
HTML is a blocking resource: images and stylesheets will not load until the user agent loads and parses the HTML that calls them. To start loading above-the-fold images before the HTML parsing finishes, send a `link` HTTP header.
**Code snippet 2**: my website includes a `link` header to load the image that serves as my IndieWeb photo and favicon. The header includes a [priority hint](https://wicg.github.io/priority-hints/) so the browser starts downloading the resource right away.  
```
link: </favicon.HASH.svg>; rel=preload; as=image; fetchpriority=high

```

[Content truncated...]
