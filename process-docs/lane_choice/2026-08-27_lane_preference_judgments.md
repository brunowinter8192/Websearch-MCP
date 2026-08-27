# Lane Preference Judgments — chromium vs camoufox, 20 URL pairs

Date: 2026-08-27

## What was judged

Twenty URLs were each scraped twice, minutes apart, through two independent acquisition
lanes: `chromium` (mode `filtered`, a cleaned/extracted text output) and `camoufox` (mode
`markdown`, a closer-to-raw conversion of the rendered page). Both outputs for every URL
were read from `src/logs/scrape_content/`. For six of the pairs the camoufox file was well
over 1 MB (up to 27 MB); those were sampled — head, several offsets through the middle, and
the tail — rather than read end to end, because the Read tool's per-call token budget made a
full read impossible for files that large. Two further camoufox files (venti, threebestrated)
sit just under 1 MB in raw bytes but still exceeded the per-call token budget on a single
read, so they were also sampled in chunks rather than read in one pass; this is noted per
entry below.

Judgment basis: for every pair I read both files and decided, as the agent that requested
the scrape to answer a user's question about that page, which output I would rather have
received. No metric, script, or automatic scoring was used — the verdict is a direct reading
judgment. Verdict is one of `chromium`, `camoufox`, `equivalent`, `neither-usable`.

---

## 1. https://www.terminland.de/hiv-sti-beratung-ffm/

- chromium: 229 bytes, HTTP 200 — camoufox: 2,241 bytes, HTTP 200
- **Verdict: camoufox**
- chromium extracted only the boilerplate line "TLS-Verschlüsselte Datenübertragung" and
  nothing else — the actual appointment-booking content never made it through the filter.
  camoufox captured the full page: consultation hours, HIV/STI test conditions, phone,
  email, room number, and address. For a question about this health service, chromium is
  functionally empty; camoufox is the only usable answer.
- No flip condition — chromium's output has no content to prefer under any question.

## 2. https://www.idealo.de/preisvergleich/ProductCategory/2926F183265.html

- chromium: 581 bytes, HTTP 403 — camoufox: 352 bytes, HTTP 200
- **Verdict: neither-usable**
- Neither carries any of the requested price-comparison content. chromium returns a genuine
  403 with a human-readable "Sorry! Something has gone wrong" message and a support
  reference ID — an honest, self-explanatory failure. camoufox returns HTTP 200 but the body
  is only "Powered and protected by Akamai" — a bot-challenge page masquerading as a
  successful fetch. For a question about product prices, both are blank.
- Flip: if the question were "is idealo currently blocking this scraper," chromium's
  explicit 403 + error text is the more informative artifact; camoufox's fake-200 is worse
  for that diagnostic question specifically.

## 3. https://www.olymp.com/de/de/hemden

- chromium: 967 bytes, HTTP 200 — camoufox: 226 bytes, HTTP 403
- **Verdict: neither-usable**
- chromium's body is a Cloudflare "Sorry, you have been blocked" challenge page (with Ray ID)
  even though the stored HTTP code is 200 — content and status disagree, but the block is at
  least explained in prose. camoufox is a bare loading-spinner alt text ("Olymp loader") with
  HTTP 403 — the page never got past the JS bootstrap. Neither gives the shirt catalog the
  question would need.
- Flip: none meaningful — both fail equally for a shopping question; chromium is marginally
  more legible about *why* it failed.

## 4. https://www.zweidigital.de/team/

- chromium: 268 bytes, HTTP 404 — camoufox: 3,306,189 bytes, HTTP 404 (camoufox sampled: head
  150 lines, offsets 2,000 / 4,000 / 6,700 of 6,856 total lines)
- **Verdict: chromium**
- Both correctly report the page is gone. chromium's extraction is the clean, complete
  answer: "Computer says no / 404 / Page not found" plus the back-link — 268 bytes. camoufox
  is a 3.3 MB dump of the full rendered page: the entire WordPress mega-menu markup repeated,
  a multi-thousand-line Cookiebot cookie declaration (individually listing dozens of tracking
  cookies with descriptions), inline minified JS bundles, and global CSS custom-property
  blocks — the same 404 message appears once, buried near line 6,820. 12,000x the bytes for
  identical information.
- No flip condition for a page-content question; the noise is pure boilerplate regardless of
  intent.

## 5. https://www.ikea.com/de/de/p/boaxel-kleiderstange-weiss-70448742/

- chromium: 7,241 bytes, HTTP 200 — camoufox: 14,604,098 bytes, HTTP 200 (camoufox sampled:
  head 100 lines and tail near line 3,767 of 3,867 total lines; two middle offsets errored
  out of the read budget and were not recovered)
- **Verdict: chromium**
- chromium is a well-formed product page: title, price, size options, care instructions,
  assembly-manual link, a handful of representative customer reviews, and related-category
  links — everything a shopping question needs. camoufox's head shows the same core product
  text is present, but the file balloons to 14.6 MB through embedded 3D-model manifest JSON,
  a full JSON-LD review block enumerating every review individually, and — notably — a
  literal `raw:<!DOCTYPE html>...` string containing an entire second copy of the page's HTML
  pasted inline as anchor text inside a bullet item near the end of the visible content. That
  is leftover/corrupted markup, not just verbosity.
- Flip: if the question needed the exhaustive review history or the 3D-model asset URLs,
  camoufox is the only lane carrying that data — but it is unusable to read directly at this
  size and would need further processing first.

## 6. https://www.bahn.de/angebot/regio/deutschland-ticket/faq-deutschlandticket

- chromium: 528 bytes, HTTP 404 — camoufox: 10,080 bytes, HTTP 404
- **Verdict: chromium**
- Both correctly show the Deutschland-Ticket FAQ page no longer exists. chromium gives the
  minimal, accurate "Fehler 404 - Seite nicht gefunden" plus the on-page search prompt.
  camoufox reproduces the same 404 message but wrapped in the full site header, the entire
  multi-level "Tickets & Angebote" navigation tree, and a full connection-search widget and
  footer — real navigation, not corrupted markup, but none of it answers the FAQ question and
  it is ~19x larger for the same non-answer.
- Flip: if the follow-up task were "find where on bahn.de this FAQ moved to," camoufox's full
  nav tree is more useful groundwork than chromium's terse output, though it does not itself
  contain the corrected URL.

## 7. https://www.hornbach.de/p/traeger-fuer-kleiderstange-1-reihig-330-mm-silber/7023243/

- chromium: 4,215 bytes, HTTP 200 — camoufox: 24,050 bytes, HTTP 200
- **Verdict: chromium**
- Both contain the same substantive product facts: price, article number, stock/pickup
  status, dimensions, material, description, and the cookie-gated reviews notice. camoufox
  adds the full store-locator header, the entire top-level category mega-menu, and an
  extensive footer (payment logos, shipping partners, app-store badges) around the identical
  product block — none of that is needed to answer a price/availability/spec question, and it
  is ~5.7x the bytes for the same core answer.
- Flip: a question like "what other product categories does Hornbach carry" would favor
  camoufox, since its full category menu is intact there and absent from chromium.

## 8. https://www.venti.com/de/de/hemden

- chromium: 1,376 bytes, HTTP 404 — camoufox: 613,042 bytes, HTTP 404 (camoufox sampled in
  three chunks of 800/400/281 lines across the 5,381-line file: head, mid, tail)
- **Verdict: chromium**
- Both report the page is unavailable with the identical "Da stimmt etwas nicht!" message and
  the same newsletter-signup block. chromium delivers this cleanly in под 1.4 KB. camoufox's
  613 KB is almost entirely the desktop mega-navigation markup repeated for every clothing
  category/flyout (Sets, Sakkos & Westen, Hemden, Strick, Shirts, Sale — each with its own
  full HTML block), with the actual "Da stimmt etwas nicht!" text appearing twice near the
  very end. ~445x the bytes for the same non-answer.
- No flip condition specific to this page — the extra content is generic site chrome, not
  page-relevant data.

## 9. https://olat.server.uni-frankfurt.de

- chromium: 1,526 bytes, HTTP 302 — camoufox: 2,981 bytes, HTTP 200
- **Verdict: camoufox**
- Both show the OLAT login landing page with the same maintenance-window announcements in
  German and English. camoufox additionally captures the "Guest Access" link, the
  language-toggle affordance, and a footer with data-privacy/imprint/accessibility links and
  the platform version — genuinely more complete, at a modest ~2x size increase with no
  garbage. For a question like "how do I get into OLAT without an account," only camoufox has
  the answer (guest access link).
- Flip: if the question is only "is there a maintenance notice today," chromium's 302 landing
  content already answers it and camoufox's extra links are not needed — but camoufox is
  never worse here, just marginally larger.

## 10. https://www.kik.de/suche/?q=duschtuch

- chromium: 6,463 bytes, HTTP 301 — camoufox: 9,627 bytes, HTTP 404
- **Verdict: equivalent**
- Neither returns actual search results for "duschtuch" — both land on kik.de's own
  "Das tut uns leid! Diese Seite ist leider nicht mehr verfügbar" (search no longer
  available) fallback, with the same Sale-redirect link and newsletter box. camoufox is
  somewhat larger due to header banner images and a slightly fuller footer/category link
  list, but carries no additional substantive information relevant to the shopping question.
  Both fail identically at the one thing the question needed.
- Flip: none — this looks like a site-side search deprecation, not a lane difference; a
  different question (e.g., "what does kik's sale banner currently promote") would find
  marginally more in camoufox's banner references, but that is incidental.

## 11. https://www.offen.net/frankfurt-main/dhl-paketshop-2AMQUI/

- chromium: 2,229 bytes, HTTP 200 — camoufox: 2,528 bytes, HTTP 200
- **Verdict: equivalent**
- Both fully answer a "where and when is this DHL Paketshop open" question: full address,
  day-by-day opening hours, nearby alternative shops with distances, and the descriptive
  footer text. camoufox additionally keeps the "Über uns" / "Presse" footer links and slightly
  cleaner line-broken address formatting, but the size difference (~13%) reflects genuinely
  equivalent content, not noise or missing material on either side.
- No meaningful flip condition — this is a small, well-behaved page in both lanes.

## 12. https://threebestrated.de/de-chemische-reinigung-in-frankfurt

- chromium: 14,356 bytes, HTTP 200 — camoufox: 900,093 bytes, HTTP 200 (camoufox sampled in
  three chunks of ~1,000 lines across the 8,966-line file: head, mid, tail; this file is
  under the 1 MB byte threshold but still exceeded the read tool's token budget on a single
  call)
- **Verdict: chromium**
- Both contain the identical substantive content: the three ranked cleaning businesses with
  specialties, prices, contact details, TBR inspection scores, and customer review quotes —
  confirmed by comparing chromium's full text against camoufox's head and tail samples, which
  match almost verbatim. The 60x size difference in camoufox comes entirely from inlined
  JavaScript in the middle of the file (a price-table-building script, Bootstrap tooltip
  initialization, review-rating widget code) that produces zero additional visible content.
- No flip condition — the extra material is pure client-side script, never rendered text.

## 13. https://www.eterna.de/versand-und-lieferung

- chromium: 4,929 bytes, HTTP 404 — camoufox: 5,311,586 bytes, HTTP 404 (camoufox sampled:
  head 150 lines, offsets 40,000 / 80,000 of 102,468 total lines, and tail 200 lines)
- **Verdict: chromium**
- The requested shipping-policy page 404s in both lanes and both fall back to the same
  generic ETERNA homepage content (bestseller teasers, OEKO-TEX blurb) rather than any
  shipping information — the chromium and camoufox head text match near-verbatim. camoufox's
  5.3 MB is the full homepage HTML: complete `<head>` with every font-face declaration, a
  huge middle section of generated "emotion" widget grid markup with almost no text, and a
  footer that includes (buried at line ~102,443) a link labeled "Versandkosten und
  Lieferzeiten" pointing to the *correct* live shipping page. chromium carries none of that
  bonus link but is 1,000x smaller for the same non-answer to the original question.
- Flip: if the task were "find a working link to the real shipping page," camoufox's buried
  footer link is the only lane that has it — but extracting it means wading through 100K+
  lines first.

## 14. http://www.praxis-am-marbachweg.de/

- chromium: 290 bytes, HTTP 200 — camoufox: 9,784 bytes, HTTP 200
- **Verdict: camoufox**
- chromium extracted only the page's `<title>`-equivalent line and nothing else — no hours,
  no contact info, no notices. camoufox captured the full practice homepage: opening hours,
  phone/fax, closure notice with a substitute practice named, the PatMed app transition
  explanation, service teasers (vaccinations, checkups, prescriptions), and the full cookie
  settings panel. For a "when is this doctor's office open / how do I book" question,
  chromium gives nothing usable; camoufox is the only real answer.
- No flip condition — chromium's output is essentially empty regardless of the question asked.

## 15. https://www.hemden.de/service/versand-und-retoure

- chromium: 9,612 bytes, HTTP 404 — camoufox: 27,470,094 bytes, HTTP 404 (camoufox sampled:
  head 150 lines, offsets 150,000 / 300,000 of 490,967 total lines, and tail 200 lines — the
  largest file in the set)
- **Verdict: chromium**
- Same pattern as the ETERNA versand page (hemden.de and eterna.de share a platform): the
  requested shipping/returns page 404s and both lanes fall back to the generic Hemden.de
  homepage marketing copy, confirmed matching between chromium and camoufox's head sample.
  camoufox's 27 MB consists overwhelmingly of the homepage's category-banner grid — hundreds
  of near-identical `<div>` blocks each wrapping a base64 placeholder GIF and a lazy-load
  image tag for a different clothing category — with a footer at the very end that, like the
  ETERNA case, contains a working "Versandkosten und Lieferzeiten" link. chromium answers the
  same non-question with ~3,000x fewer bytes.
- Flip: identical to entry 13 — a link-recovery task would need camoufox's footer, but
  reading it directly is impractical at this size.

## 16. https://www.pin-ruecksetzbrief-bestellen.de/

- chromium: 1,608 bytes, HTTP 200 — camoufox: 2,317 bytes, HTTP 200
- **Verdict: equivalent**
- Both fully explain, in German and English, that the PIN-reset-letter service was
  discontinued in February 2024 and where to go instead (citizens' office, servicesuche.bund.de,
  personalausweisportal.de). camoufox adds a small header image and a short "Kontakt" section
  with a support phone number/link that chromium lacks, but the core answer to "can I still
  order a PIN reset letter" is complete and identical in both.
- Flip: a question specifically needing the support contact number would favor camoufox by a
  small margin; otherwise the two are interchangeable.

## 17. https://www.dm.de/search?query=perwoll%20color

- chromium: 4,428 bytes, HTTP 200 — camoufox: 17,745 bytes, HTTP 200
- **Verdict: chromium**
- Both list the identical 8 Perwoll products with the same prices, unit prices, availability
  status, and review counts. camoufox repeats a row of 5 star-icon image links per product
  (40 extra image tags total) and a fuller category/footer nav, none of which changes the
  product data itself. For a "which Perwoll Color products are available and what do they
  cost" question, chromium gives the same answer in a quarter of the space.
- Flip: none — the extra material is decorative iconography and generic footer links.

## 18. https://de.linkedin.com/jobs/view/praktikant-werkstudent-m-w-d-at-verto-gmbh-4447677311

- chromium: 26,093 bytes, HTTP 200 — camoufox: 45,928 bytes, HTTP 200
- **Verdict: equivalent**
- Both contain the complete job posting: title, company, location, full task list,
  requirements, "bonus" qualifications, benefits, the application-process steps, and an
  extensive list of similar/also-viewed jobs. camoufox renders the sign-in prompt and login
  form twice (once as a bare block, once with all placeholder text) and carries a broken CSS
  class fragment leaked into the visible text ("svg]:size-3 gap-1 ..."), which is a minor
  rendering leftover, but the actual job content a user would ask about is fully present and
  equally readable in both.
- Flip: if the question needed the exact list of "similar searches" or company-follow counts,
  camoufox's slightly longer tail has marginally more of those; not decisive either way.

## 19. https://www.eterna.de/hemden

- chromium: 4,914 bytes, HTTP 301 — camoufox: 5,309,216 bytes, HTTP 200
- **Verdict: chromium**
- This URL redirects/falls through to the same generic ETERNA homepage content seen in entry
  13 (bestseller teasers, "seit mehr als 160 Jahren" copy) rather than an actual shirt catalog
  — confirmed identical between chromium's full text and camoufox's head sample. camoufox is
  again a 5.3 MB dump of the same homepage template (full font-face CSS, generated widget
  grid markup, footer with real shop-service links). For a "what shirts does ETERNA sell"
  question neither lane answers it, but chromium reaches the same non-answer at 1/1,000th the
  size.
- Flip: same as entry 13 — link-recovery tasks would need camoufox's footer.

## 20. https://www.hornbach.de/c/maschinen-werkzeug-werkstatt/regale/S866/f/Marke=Dolle%20Regale

- chromium: 29,953 bytes, HTTP 301 — camoufox: 65,100 bytes, HTTP 200
- **Verdict: chromium**
- Both list the same ~40+ Dolle-brand shelving products with prices, ratings, and stock
  status, plus embedded "Ratgeber" (advice-article) teasers. camoufox additionally renders
  the subcategory tile images/links, full breadcrumb trail, and complete site header/footer
  around the identical product list — real content, not corruption, but roughly double the
  bytes for the same product listing.
- Flip: a "what subcategories exist under Regale" navigation question would favor camoufox,
  since its subcategory tiles (Metallregale, Holzregale, Kunststoffregale, etc.) are absent
  from chromium's output.

---

## Aggregate

**Verdict tally (20 pairs):**
- chromium: 11 (entries 4, 5, 6, 7, 8, 12, 13, 15, 17, 19, 20)
- camoufox: 3 (entries 1, 9, 14)
- equivalent: 4 (entries 10, 11, 16, 18)
- neither-usable: 2 (entries 2, 3)

**Which class of page favours which lane.**
- camoufox wins on pages where chromium's content-filtering step failed to extract anything
  meaningful from a JS-rendered page — terminland's booking widget and the doctor-practice
  homepage both came back near-empty from chromium (229 and 290 bytes) while camoufox
  captured the full rendered text. camoufox also edges ahead on the OLAT login page by
  picking up a genuinely extra affordance (guest access) that chromium's filter dropped.
- chromium wins decisively — often by 2–3 orders of magnitude in size — on every page where
  the underlying site returned a 404/redirect-to-homepage or a working product/category
  page. In both cases the substantive text is identical between lanes; camoufox's markdown
  mode carries the full DOM instead of extracted content, so cookie-consent declarations,
  mega-menus, inlined scripts, font-face CSS blocks, and (on Shopware-based shops) entire
  generated image-banner grids ride along for free.
- The two "neither-usable" cases (idealo, olymp) are both anti-bot challenge pages
  (Akamai and Cloudflare respectively); neither lane got past the block, and the lane choice
  made no difference to the outcome.
- The four "equivalent" cases are pages that are small and well-behaved in both lanes to
  begin with (a static info page, a store-locator page, a search-fallback page, and a
  LinkedIn job posting) — the byte-size gap between lanes on these pages is modest (1.1x–1.8x)
  and does not correspond to any missing or corrupted content on either side.

**Failure modes observed.**
- *Filter-drop*: chromium's extraction pass returns only a title fragment or boilerplate
  line, dropping the entire body (terminland, praxis-am-marbachweg, idealo's error copy is
  the exception where chromium's filtered text was actually the most complete artifact).
- *Homepage fallback masquerading as content*: on the two Shopware-based shops (eterna.de,
  hemden.de), a 404/redirect on a specific sub-page silently serves the generic homepage in
  both lanes — this is a site behavior, not a lane artifact, but it means three of the twenty
  URLs never returned the content the question actually asked about, in either lane.
- *Raw-DOM bloat*: camoufox's markdown mode is a near-literal serialization of the rendered
  page, so cookie-consent frameworks (Cookiebot, custom Shopware consent panels), mega-menus,
  inlined tracking scripts, and font-face declarations are captured verbatim and can inflate
  a file 100x–3,000x over the chromium equivalent with zero net gain in usable content.
- *Leftover/corrupted markup*: the IKEA page contained a literal second copy of the page's
  raw HTML pasted as anchor text inside the visible content stream (a `raw:<!DOCTYPE html>...`
  string) — this is not just verbosity but a genuine extraction defect specific to camoufox's
  output for that page.
- *Anti-bot block pages*: idealo (Akamai) and olymp (Cloudflare) blocked both lanes; camoufox
  reported a misleading HTTP 200 on the Akamai block while the body was clearly a
  challenge page — a case where the stored status code cannot be trusted without reading the
  body.

**What surprised me.**
- The sheer size ratio on the worst cases — 27 MB vs 9.6 KB for the *same 404 fallback
  content* (hemden.de) — was more extreme than expected; the bloat is not proportional to
  page complexity but to how much client-side tooling (image lazy-load grids, consent
  managers) the target site runs.
- Three separate URLs in a 20-URL sample (eterna/versand, eterna/hemden, hemden.de/service)
  turned out to be dead sub-pages silently serving their site's homepage — a site-side pattern
  worth flagging to whoever curated the URL list, independent of lane choice.
- camoufox was never the worse choice by a wide margin — its losses are all "same content,
  much more noise," never "missing content chromium had." Its wins, by contrast, are cases
  where chromium returned essentially nothing. This suggests camoufox is the safer fallback
  when chromium's extraction looks suspiciously short, even though it is the worse default
  for routine use due to its verbosity.
