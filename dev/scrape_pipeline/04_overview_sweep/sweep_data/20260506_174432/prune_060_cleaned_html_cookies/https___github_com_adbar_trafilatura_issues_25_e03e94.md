<!-- source: https://github.com/adbar/trafilatura/issues/25 -->

[Skip to content](https://github.com/adbar/trafilatura/issues/25#start-of-content)
You signed in with another tab or window. [Reload](https://github.com/adbar/trafilatura/issues/25) to refresh your session. You signed out in another tab or window. [Reload](https://github.com/adbar/trafilatura/issues/25) to refresh your session. You switched accounts on another tab or window. [Reload](https://github.com/adbar/trafilatura/issues/25) to refresh your session. Dismiss alert
/ Public
  * #  Sponsor adbar/trafilatura 
##### GitHub Sponsors
[Learn more about Sponsors](https://github.com/sponsors)
##### External links
[ko-fi.com/**adbarbaresi**](https://ko-fi.com/adbarbaresi)
[Learn more about funding links in repositories](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository). 
  * You must be signed in to change notification settings


#  Difference between this and using readability #25
Copy link
Copy link
Labels
[Further information is requested](https://github.com/adbar/trafilatura/issues?q=state%3Aopen%20label%3A%22question%22)Further information is requested
## Description
opened [on Oct 24, 2020](https://github.com/adbar/trafilatura/issues/25#issue-728829225)
Issue body actions
Hi! Great library, but I am trying to figure out if we should swap from using readability on which this builds. Apart from manually checking the quality for our corpus there is no easy way for me to compare performance. Would you be able to explain the differences between the actual text extraction approaches? Thanks in advance! D
## Activity
### adbar commented on Oct 26, 2020 
More actions
Hi, thanks for your interest.
According to [my benchmark](https://trafilatura.readthedocs.io/en/latest/evaluation.html) and this [external one](https://github.com/scrapinghub/article-extraction-benchmark) `trafilatura` should work better than `readability-lxml` on average. This can be explained by the way the library is designed:
  * It grounds on a cascade of extraction methods: first a series of heuristics for main text discovery and conversion, then two external libraries, then a baseline extraction if nothing worked (basically all text tags such as ).
  * Since it defaults to `readability-lxml` if extraction fails or appears to have failed, you'll still benefit from the efficiency of this (very good) library, `justext` is also used as a fallback. In theory (and the benchmarks confirm it) `trafilatura` has a better website coverage without sacrificing precision. Its series of heuristics and `readability-lxml` are mostly used, the rest only applies to rare cases.
  * If you're also interested in extracting comments, this library can do it while `readability` cannot.
  * It performs a conversion and can output "homogeneous" (clean) text and tags in XML format, which `readability-lxml` doesn't, sometimes leaving you with "exotic" HTML tags within the content.


I hope it helps!
### ydennisy commented on Oct 26, 2020 
More actions
[@adbar](https://github.com/adbar) Thank you very much for your reply!
I tried a comparison today, and it seems that the libs differ quite a bit on their extraction, but it is not clear to me when and why.
Some information I think I have is that:
  * `trafilatura` seems to pick up footers more often
  * fallback does not seem to work as I can get no text from your lib, but text from readability


I am not sure if you will find this useful, but I am providing you some URLs on which the two libs differ the most, the following URLs are where your lib extracts more text:

```
['https://www.awesomeinventions.com/my-house-not-my-cat-photos',
 'https://youhadmeatgardening.com/lemon-tree-from-seed',
 'https://www.dailymail.co.uk/money/markets/article-8805521/BUSINESS-LIVE-Stimulus-hopes-boost-markets.html',
 'https://www.historychronicle.com/view/90s-vintage-pics-hc/',
 'https://pawszilla.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/28/',
 'https://www.calcalist.co.il/internet/articles/0,7340,L-3835935,00.html',
 'https://www.onthemarket.com/farms-land/property/cornwall/',
 'https://www.theguardian.com/world/live/2020/oct/08/coronavirus-live-news-brazil-cases-pass-5m-trump-calls-catching-covid-a-blessing-in-disguise',
 'https://www.walesonline.co.uk/news/wales-news/coronavirus-live-updates-lockdown-gething-19049119',
 'https://www.nottinghampost.com/news/local-news/live-nottinghamshire-lockdown-tighter-restrictions-4585870',
 'https://www.graduatez.com/view/scientists-are-in-awe-after-finding-a-bewildering-creature-beached-on-the-californian-shore/',
 'https://www.loksatta.com',
 'https://www.lefigaro.fr',
 'https://www.theyeshivaworld.com',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/everton-transfer-news-live-rodriguez-19087404',
 'https://mydailymagazine.com/post-a1e720df/',
 'https://www.historychronicle.com/view/history-discovery-secrets-hc/',
 'https://www.manchestereveningnews.co.uk/sport/football/football-news/leeds-vs-man-city-live-19043874',
 'https://www.dailymail.co.uk/travel/escape/article-8814663/The-worlds-best-hotels-islands-cities-ski-resorts-revealed-Conde-Nast-Traveller.html',
 'https://www.business-live.co.uk/economic-development/boris-johnson-unveil-lockdown-restrictions-19088918',
 'https://www.dailyrecord.co.uk/news/politics/nicola-sturgeon-coronavirus-update-live-22799031',
 'https://musiccritic.com/equipment/guitars/best-acoustic-electric-guitar',
 'https://www.dailyrecord.co.uk/sport/football/football-transfer-news/transfer-deadline-live-rangers-celtic-22792735',
 'https://www.gumtree.com/dogs/scotland/page6',
 'https://www.moneycontrol.com',
 'https://www.getreading.co.uk/news/reading-berkshire-news/live-homes-west-reading-suffer-19062352',
 'https://www.hulldailymail.co.uk/news/hull-east-yorkshire-news/3-tier-lockdown-live-updates-4597247',
 'https://www.nature.com/articles/ncomms4887',
 'https://www.dailyrecord.co.uk/sport/football/football-news/europa-league-draw-live-celtic-22779308',
 'https://www.gumtree.com/dogs/uk/dogs+northern+ireland/page2',
 'https://alphamom.com',
 'https://www.domesticatedcompanion.com/actors-havent-done-anything-in-years/2/',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/liverpool-transfer-news-rumours-butland-19055637',
 'https://www.insider.com/hard-brainteasers-riddles-for-smart-people-2017-9',
 'https://www.catster.com/lifestyle/bringing-an-adult-cat-into-your-home',
 'https://www.express.co.uk/life-style/science-technology/1340039/iPhone-12-Release-Date-October-13-2020-Apple-Fans-Not-Long-Left-To-Wait-UK/amp',
 'https://www.pinkvilla.com/entertainment/news/saif-ali-khan-talks-about-sara-ali-khan-and-how-if-he-s-hurt-her-taimur-can-t-make-him-feel-better-566895',
 'https://reviews.mtbr.com',
 'https://www.dailymail.co.uk/news/article-8803493/Trump-administrations-fear-leaks-leaves-White-House-staff-dark.html',
 'https://kit.honestjohn.co.uk',
 'https://www.trivia.com/view/a-letter-from-this-womans-biological-mother-changed-her-life-forever/',
 'https://www.gumtree.com/dogs/uk/puppies/page12',
 'https://www.essexlive.news/news/essex-news/live-coronavirus-updates-essex-awaits-4604321',
 'https://www.dailymail.co.uk/sport/football/article-8797665/Europa-League-group-stage-draw-2020-21-LIVE-Result.html',
 'https://www.lefigaro.fr/politique',
 'https://www.chocolate.com/view/life-of-steven-mcqueen-cho/',
 'https://www.gumtree.com/dogs/uk/page2',
 'https://www.examinerlive.co.uk/sport/football/transfer-news/huddersfield-town-transfer-news-live-19112945',
 'https://www.walesonline.co.uk/sport/football/transfer-news/cardiff-city-transfer-news-live-19112387',
 'https://www.gumtree.com/cars/uk/audi/a6/page2',
 'https://www.thespruce.com/ingenious-ikea-billy-bookcase-hacks-4006865',
 'https://iamafoodblog.com/birria-tacos-recipe',
 'https://bestofmachinery.com/best-hearing-protection-for-lawn-mowing',
 'https://www.wallstreetmojo.com/preferred-shares',
 'https://parentinfluence.com',
 'https://www.grimsbytelegraph.co.uk/news/uk-world-news/live-boris-johnson-press-conference-4561866',
 'https://www.autoscout24.de/lst/',
 'https://www.msn.com/en-za',
 'https://www.lefigaro.fr/societes',
 'https://www.devonlive.com/news/devon-news/planning-applications-submitted-devon-week-4506950',
 'https://www.oversixty.com.au',
 'https://www.dailypost.co.uk/news/north-wales-news/coronavirus-live-press-conference-take-19099922.amp',
 'https://www.trivia.com/view/cool-google-earth-finds-trv/',
 'https://www.pinkvilla.com/tv/news-gossip/bigg-boss-6-s-sana-khan-bids-goodbye-showbiz-industry-forever-decides-spend-life-serving-humanity-567296',
 'https://www.dailymail.co.uk/sport/football/article-8772027/Crystal-Palace-vs-Everton-Premier-League-Live-result.html',
 'https://www.hulldailymail.co.uk/sport/rugby-league/rugby-league-live-transfer-news-4560871',
 'https://www.manchestereveningnews.co.uk/sport/football/transfer-news/man-utd-transfer-news-recap-19042171',
 'https://www.yardbarker.com/entertainment/gallery/the_most_talked_about_movie_moments_of_the_2010s/s1__30411269',
 'https://www.historychronicle.com/view/thomas-jeffersons-hidden-rooms-hc/',
 'https://www.gumtree.com/property-to-rent/plymouth/page2',
 'https://www.dailymail.co.uk/sport/football/article-8803121/Transfer-News-LIVE-Latest-Premier-League-European-signings-deals-rumours.html',
 'https://www.hulldailymail.co.uk/news/uk-world-news/live-coronavirus-uk-lockdown-rules-4579067',
 'https://www.buzzfeed.com/quizzes',
 'https://www.liverpoolecho.co.uk/news/liverpool-news/live-coronavirus-boris-vaccine-tests-19049134',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/everton-news-transfer-rumours-godfrey-19025712',
 'https://www.dailyrecord.co.uk/sport/football/football-transfer-news/transfer-news-live-celtic-rangers-22765511',
 'https://www.mabelandmoxie.com/amp/These+Are+The+Smartest+Dog+Breeds+In+The+World,+Ranked',
 'https://www.pinkvilla.com/entertainment/news/kangana-ranaut-reacts-karan-srk-other-productions-uniting-against-media-houses-file-case-me-also-567902',
 'https://www.vielfliegertreff.de',
 'https://www.gumtree.com/cars/uk/left+hand+drive/page7',
 'https://www.gumtree.com/cats/uk/kittens/page2',
 'https://www.chroniclelive.co.uk/news/north-east-news/uk-deaths-coronavirus-live-updates-18935120',
 'https://www.manchestereveningnews.co.uk/news/greater-manchester-news/live-mayor-andy-burnham-holds-19023674',
 'https://www.telegraph.co.uk/news/2020/10/07/travel-latest-covid-passport-greece-italy-turkey-quarantine',
 'https://historicalpost.com/anthropology-and-history/places/niagara-falls-runs-dry-reveals-bodies-1969-united-states-canada/12/',
 'https://www.pinkvilla.com/entertainment/news/shabana-azmi-opens-unrest-bollywood-and-kangana-ranauts-outrageous-remarks-566625',
 'https://www.simbaly.com/view/the-jackson-kids-now-sim/',
 'https://www.dailymail.co.uk/sport/football/article-8784211/Transfer-news-LIVE-Latest-Premier-League-European-club-signings-deals-rumours.html',
 'https://www.gumtree.com/dogs/uk/french+bulldog/page3',
 'https://powerlisting.fandom.com/wiki/List_of_Supernatural_Powers_and_Abilities',
 'https://www.standard.co.uk/news/uk/uk-coronavirus-live-latest-updates-boris-johnson-threetier-lockdown-a4568406.html',
 'https://m.khaleejtimes.com',
 'https://divinityoriginalsin2.wiki.fextralife.com',
 'https://forums.civfanatics.com',
 'https://www.gumtree.com/dogs/uk/page6',
 'https://www.insider.com/what-are-healing-crystals-how-to-use-them-2018-7',
 'https://www.msn.com/fr-fr',
 'https://www.gumtree.com/cars/northern-ireland/page2',
 'https://www.birminghammail.co.uk/sport/football/transfer-news/wolves-deadline-day-transfers-live-19037027',
 'https://www.leeds-live.co.uk/news/uk-world-news/live-coronavirus-sheffield-leeds-rates-19042623',
 'https://itsfoss.com/best-linux-desktop-environments',
 'https://www.historychronicle.com/view/cleaning-lady-shock-prank/',
 'https://flawlessfood.co.uk/olive-herb-focaccia-bread',
 'https://www.luxandlush.com/view/woman-sells-a-house-nobody-expected-to-find-this-inside-lux/',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/live-liverpool-transfer-news-rumours-19074803',
 'https://www.everydayhealth.com/healthy-living/fascinating-facts-about-body-temperature.aspx',
 'https://rus.delfi.lv',
 'https://www.birminghammail.co.uk/sport/football/transfer-news/villa-live-king-transfer-latest-19062357',
 'https://hu.motorsport.com',
 'https://www.foxyfolksy.com/chocolate-buttercream-frosting-without-powdered-sugar-ermine-icing',
 'https://toppoptoday.com',
 'https://bap.navigator.web.de',
 'https://trends.bibamagazine.fr/en/prince-william-and-harry-technically-have-a-sister-and-they-completely-ignore-her-2/20',
 'https://www.telegraph.co.uk/business/2020/10/06/joe-bidens-war-economy-policies-radical-break-status-quo',
 'https://www.gumtree.com/dogs/scotland/page4',
 'https://www.birminghammail.co.uk/sport/football/transfer-news/aston-villa-transfers-rashica-benrahma-19037412',
 'https://www.standard.co.uk/news/uk/coronavirus-live-latest-updates-pubs-close-a4566031.html',
 'https://www.gumtree.com/cars/uk/page5',
 'https://www.euronews.com',
 'https://www.graduatez.com/view/surprising-findings-pipes/',
 'https://www.msn.com/de-ch/',
 'https://pawszilla.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/65/',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/live-everton-transfer-news-bernard-19075370',
 'https://www.historychronicle.com/view/ozzy-osbourne-facts-hc/',
 'https://zenherald.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/30/',
 'https://www.manchestereveningnews.co.uk/news/uk-news/pmqs-live-prime-minister-boris-19101281',
 'https://www.mirror.co.uk/sport/football/transfer-news/transfer-news-live-smalling-dele-22721256',
 'https://sportowefakty.wp.pl/zuzel/relacja/110331/fogo-unia-leszno-rm-solar-falubaz-zielona-gora',
 'https://www.gumtree.com/cars/scotland/page3',
 'https://guides.gamepressure.com',
 'https://www.msn.com/en-gb',
 'https://www.chroniclelive.co.uk/news/north-east-news/coronavirus-restrictions-uk-live-updates-19026811',
 'https://hipertextual.com',
 'https://www.luxandlush.com/view/celeb-kids-are-not-little-anymore-fb-lux/',
 'https://www.historychronicle.com/view/70s-80s-celebs-kids-fb-hc/',
 'https://m.sportowefakty.wp.pl/pilka-nozna/relacja/106622/polska-finlandia',
 'https://www.gumtree.com/cars/uk/range+rover+sport/page2',
 'https://www.stokesentinel.co.uk/news/stoke-on-trent-news/live-covid-19-updates-across-4588547',
 'https://www.bristolpost.co.uk/sport/football/football-news/bristol-rovers-transfer-questions-garner-4555153',
 'https://www.visitlancashire.com/things-to-do/animal-and-farm-attractions',
 'https://www.mirror.co.uk/sport/football/transfer-news/transfer-news-live-arsenal-sancho-22752560',
 'https://www.lesechos.fr',
 'https://www.gumtree.com/for-sale/uk/page2',
 'https://www.bristolpost.co.uk/news/health/coronavirus-cases-lockdown-bristol-live-4597246',
 'https://www.simbaly.com/view/celeb-daughters-grown-up-co-sim/',
 'https://www.buzzfeed.com/alliehayes/weird-house-rules-parents-reddit',
 'https://www.gumtree.com/dogs/northern-ireland/page4',
 'https://www.autosport.com',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/everton-news-transfer-rumours-live-19025712',
 'https://www.rtl.be',
 'https://www.standard.co.uk/news/uk/coronavirus-live-latest-updates-lockdown-vaccine-a4567091.html',
 'https://www.gazettelive.co.uk/news/teesside-news/coronavirus-live-boris-johnson-set-19088101',
 'https://cookieandkate.com/perfect-quinoa',
 'https://www.chroniclelive.co.uk/sport/football/football-news/newcastle-transfer-news-live-mourinho-19007685',
 'https://www.gumtree.com/cars/uk/land-rover/defender/page3',
 'https://www.lakesideloops.com/watson-cardigan',
 'https://www.chocolate.com/view/woman-sees-a-car-stop-for-pregnant-beggar-this-is-what-she-finds-when-she-follows/',
 'https://www.chroniclelive.co.uk/news/north-east-news/boris-johnson-announcement-live-updates-19090211',
 'https://www.sports.fr/direct-foot/50918/177512/lorient-olympique-lyonnais.html',
 'https://www.pinkvilla.com/entertainment/news/sushant-singh-rajputs-flatmate-siddharth-pithani-states-late-actor-did-not-meet-rhea-chakraborty-june-13-566132',
 'https://www.cornwalllive.com/news/cornwall-news/live-storm-alex-weather-traffic-4567887',
 'https://www.yourrulingplanet.com/view/instagram-golfer-paige/',
 'https://www.dublinlive.ie/news/health/level-5-lockdown-nphet-dublin-19053662',
 'https://www.thelist.com/214894/when-you-take-a-multivitamin-every-day-this-is-what-happens-to-your-body',
 'https://beta.southglos.gov.uk/new-south-gloucestershire-local-plan-2018-2036',
 'https://www.latest-hairstyles.com/mens/thin.html',
 'https://www.healthline.com/nutrition/ways-to-measure-body-fat',
 'https://www.themakeupdummy.com',
 'https://www.audi-sport.net/xf',
 'https://www.cheshire-live.co.uk/news/chester-cheshire-news/live-cheshire-coronavirus-national-lockdown-19049856.amp',
 'https://www.chroniclelive.co.uk/news/north-east-news/north-east-news-live-latest-19112705',
 'https://www.edinburghlive.co.uk/news/edinburgh-news/coronavirus-scotland-live-rules-latest-19046171',
 'https://www.ccna7.com/ccna2-v6-0/ccna2-v6-0-chapter-2-exam-answer-2017',
 'https://www.autocar.co.uk/slideshow/biggest-flops-automotive-history-0',
 'https://www.telegraph.co.uk/news/0/matt-favourite-covid-19-cartoons-think-laughing-something-makes',
 'https://www.pinkvilla.com/tv/news-gossip/exclusive-here-s-why-salman-khan-s-bigg-boss-14-will-air-half-hour-there-good-news-565189',
 'https://www.manchestereveningnews.co.uk/news/uk-news/live-boris-johnson-leads-downing-19091296',
 'https://www.gumtree.com/caravans/uk/page3',
 'https://www.cheshire-live.co.uk/news/chester-cheshire-news/live-cheshire-lockdown-coronavirus-council-19021297',
 'https://happyyouhappyfamily.com',
 'https://thepostpartumparty.com/how-to-set-up-a-baby-nursery-in-a-small-space',
 'https://www.realsimple.com/home-organizing/gardening/outdoor/hydrangea-care',
 'https://www.devonlive.com/news/local-news/live-m5-fire-bristol-avonmouth-4575486',
 'https://www.historychronicle.com/view/priest-sues-millions-hc/',
 'https://www.cadena100.es',
 'https://www.minq.com/lifestyle/2553886/students-recall-the-absolute-dumbest-thing-theyve-ever-heard-a-teacher-say/',
 'https://www.levante-emv.com',
 'https://www.authenticfoodquest.com/popular-portuguese-dishes',
 'https://www.instyle.com/beauty/wigs-for-black-women-cancer',
 'https://www.theprimarymarket.com/view/pizza-delivery-employee-tpm/',
 'http://www.msn.com/en-gb/',
 'https://www.dailymail.co.uk/sport/football/article-8772175/Sheffield-United-vs-Leeds-Premier-League-Live-result.html',
 'https://www.minq.com/lifestyle/2495316/students-share-the-rudest-thing-a-teacher-ever-said-to-them/',
 'https://www.nottinghampost.com/sport/football/football-news/nottingham-forest-transfer-news-live-4597836',
 'https://www.msn.com/es-es',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/liverpool-transfer-news-rumours-kabak-19042594',
 'https://wiadomosci.gazeta.pl',
 'https://www.nationalrail.co.uk/service_disruptions/245738.aspx',
 'https://www.domesticatedcompanion.com/actors-havent-done-anything-in-years/',
 'https://www.caughtoffside.com/2020/09/27/agreement-reached-man-united-look-set-to-sign-defender-as-they-reach-an-agreement-on-the-final-details/',
 'https://www.corkbeo.ie/news/local-news/level-3-live-cork-ireland-19056312',
 'https://www.historychronicle.com/view/single-celebs-hc/',
 'https://www.historychronicle.com/view/donny-osmond-confession-hc/',
 'https://www.somersetlive.co.uk/news/somerset-news/live-storm-alex-weather-traffic-4568051',
 'https://www.theprimarymarket.com/view/elderly-house-sell/',
 'https://www.luxandlush.com/view/behind-the-scenes-with-barbi-benton/',
 'https://magellantimes.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/37/',
 'https://www.nerfplz.com',
 'https://www.disneytouristblog.com/disney-world-news-star-wars-permit-frozen-ride-refurbishment-restaurants-returning',
 'https://trendscatchers.co.uk/index.php/en/2020/07/09/prince-harry-claims-that-meghan-markle-might-not-be-the-one-2/31',
 'https://www.ign.com/articles/the-best-ssd-for-gaming',
 'https://www.birminghammail.co.uk/sport/football/transfer-news/villa-live-deadline-day-king-19062357',
 'https://www.telegraph.co.uk/opinion/2020/10/04/lettersgps-have-worked-crisis-often-personal-cost',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/live-everton-transfer-news-rumours-19061794',
 'https://www.liverpoolecho.co.uk/sport/football/football-news/liverpool-transfer-news-rumours-live-19025709',
 'https://cookieandkate.com/mujaddara-recipe',
 'https://trendscatchers.co.uk/index.php/en/2020/07/09/prince-harry-claims-that-meghan-markle-might-not-be-the-one-2/30',
 'https://www.theguardian.com/society',
 'https://www.nature.com/articles/s41467-018-04619-5',
 'https://www.birminghammail.co.uk/sport/football/transfer-news/transfer-news-west-brom-live-19036796',
 'https://www.divein.com',
 'https://www.historychronicle.com/view/real-noahs-ark-hc/',
 'https://www.preloved.co.uk/classifieds/furniture-fittings/kitchen-furniture/all/uk/used+kitchen+cabinets+sale',
 'http://wiadomosci.gazeta.pl',
 'https://www.dailyrecord.co.uk/sport/football/football-news/celtic-vs-rangers-live-score-22860327',
 'https://www.domesticatedcompanion.com/each-state-perfectly-portrayed-in-one-photograph/2/',
 'https://www.gumtree.com/dogs/uk/northern+ireland+pets/page2',
 'https://www.hertfordshiremercury.co.uk/news/hertfordshire-news/live-boris-johnson-speech-updates-4597736',
 'https://www.gazettelive.co.uk/sport/football/transfer-news/middlesbrough-transfers-yannick-bolasie-striker-19111028',
 'https://www.cambridge-news.co.uk/news/uk-world-news/live-updates-boris-johnson-tierlockdown-19117181',
 'http://www.msn.com/',
 'https://www.kentlive.news/news/kent-news/live-updates-covid-infection-rates-4597748',
 'https://www.goodhousekeeping.com/holidays/gift-ideas/g1266/handmade-gifts',
 'https://www.walesonline.co.uk/news/wales-news/wales-breaking-news-traffic-weather-19075607',
 'https://www.visitwiltshire.co.uk/accommodation/self-catering',
 'https://www.historychronicle.com/view/bing-crosby-life-hc/',
 'https://www.liverpoolecho.co.uk/news/liverpool-news/live-uk-coronavirus-updates-merseyside-19002010',
 'https://crinacle.com/2020/02/19/the-audiophiles-perspective-samsung-galaxy-buds',
 'https://www.mirror.co.uk/sport/football/transfer-news/arsenal-transfer-news-live-partey-22790130',
 'https://www.chocolate.com/view/70s-80s-celebs-kids-fb-cho/',
 'https://www.domesticatedcompanion.com/actors-havent-done-anything-in-years/11/',
 'https://www.gumtree.com/dogs/uk/jack+russell/page4',
 'https://www.haaretz.com/israel-news/business/.premium-this-year-israeli-energy-finally-went-green-but-the-revolution-is-just-beginning-1.9214282',
 'https://natashaskitchen.com/chicken-stir-fry-recipe',
 'https://www.hulldailymail.co.uk/news/uk-world-news/coronavirus-live-cases-lockdown-updates-4573922',
 'https://www.primandprep.com',
 'https://www.organizationobsessed.com/20-amazing-organization-hacks-will-transform-bedroom',
 'https://www.bakewithpaws.com',
 'https://www.oprahmag.com/entertainment/g28335655/best-halloween-books',
 'https://www.trivia.com/view/61-of-the-best-red-carpet-mishaps/',
 'https://www.examinerlive.co.uk/news/west-yorkshire-news/live-coronavirus-sheffield-leeds-kirklees-19056079',
 'https://www.telegraph.co.uk/news/2020/10/10/return-students-caused-inevitable-spike-covid-cases',
 'https://www.leeds-live.co.uk/sport/leeds-united/leeds-united-u23s-live-highlights-19036388']

```

This batch is where readability extracts more text:

```
['https://redtri.com/best-jokes-for-kids/slide/1',
 'https://www.msn.com/en-gb/news/uknews/uk-university-student-halls-too-full-to-be-safe-experts-warn/ar-BB19DUqK',
 'https://www.babysleepsite.com/schedules/toddler-schedule/',
 'https://www.msn.com/en-gb/foodanddrink/other/slow-cooker-turkey-chilli-is-healthier-but-just-as-comforting/ar-BB19KDYg',
 'https://www.dailymail.co.uk/sport/teampages/leicester.html',
 'https://www.msn.com/en-gb/lifestyle/travel/can-you-guess-these-capital-cities-from-up-high/ss-BB19DxUe',
 'https://www.independent.co.uk/news/uk/politics/coronavirus-false-reporting-contact-fine-penalty-b671230.html',
 'https://www.msn.com/en-gb/lifestyle/style/prince-louis-adorable-striped-knit-is-a-10-john-lewis-bargain/ar-BB19HUbk',
 'https://www.dailymail.co.uk/tvshowbiz/love-island/index.html',
 'https://www.discogs.com/sell/list',
 'https://www.msn.com/en-gb/travel/tripideas/these-are-the-world-s-most-beautiful-national-parks/ss-BB19FnGx',
 'https://www.msn.com/en-gb/travel/tripideas/this-enchanted-fairytale-treehouse-in-kent-is-the-perfect-autumn-staycation/ar-BB19I6Wz',
 'https://www.msn.com/en-gb/lifestyle/style/super-organised-star-closets-we-d-love-to-copy/ss-BB19IOde',
 'https://www.futbin.com/21/player/25735/leroy-sane',
 'https://www.msn.com/en-gb/news/techandscience/scientists-discover-24-planets-with-conditions-even-more-suitable-for-life-than-earth/ar-BB19HZlb',
 'https://www.mirror.co.uk/news/uk-news/breaking-englands-worst-schools-revealed-13899939',
 'https://relieved.co/brilliant-kitchen-tips-cooking-easier/',
 'https://www.standard.co.uk/news/uk/three-tier-lockdown-system-coronavirus-london-medium-risk-a4570041.html',
 'https://www.lifewire.com/screen-mirroring-lg-smart-tvs-4770959',
 'https://minecraft-server-list.com',
 'https://www.standard.co.uk/news/uk/boris-johnson-coronavirus-nation-briefing-100-a4559471.html',
 'https://www.fifplay.com/fifa-21-game-settings',
 'https://www.independent.co.uk/news/uk/politics/brexit-boris-johnson-michael-gove-northern-ireland-border-b669752.html',
 'https://www.theguardian.com/uk-news/2020/oct/09/rishi-sunak-expands-wage-subsidies-to-head-off-winter-surge-in-job-losses',
 'https://www.futbin.com/21/player/25374/thomas-partey',
 'https://www.standard.co.uk/news/uk/turkey-poland-caribbean-islands-added-to-uk-quarantine-list-a4561256.html',
 'https://www.dailymail.co.uk/news/article-8747257/Is-England-heading-HALF-TERM-lockdown.html',
 'https://www.independent.co.uk/news/uk/politics/brexit-no-deal-summit-boris-johnson-eu-fishing-state-aid-von-der-leyen-michel-b1041344.html',
 'https://www.msn.com/en-gb/lifestyle/style/kate-middleton-breaks-the-internet-with-her-35-linen-shirt/ar-BB19AQ57',
 'https://ext.theperspective.com/items-we-never-knew-we-wanted/1/',
 'https://www.futbin.com/21/player/681/ferland-mendy',
 'https://www.popsugar.co.uk/smart-living/Cheap-Homemade-Halloween-Costumes-42432483/amp',
 'https://www.msn.com/en-gb/money/homeandproperty/celebrity-real-estate-in-october-chris-hemsworth-demi-lovato-and-more/ss-BB19BHew',
 'https://spotlightstories.co/50-hilarious-exam-answers-students-given/',
 'https://www.futbin.com/21/player/612/leroy-san%C3%A9',
 'https://www.tomshardware.com/uk/reviews/best-gpus,4380.html',
 'https://harrypotter.fandom.com/wiki/Hufflepuff',
 'https://docplayer.net',
 'https://www.theguardian.com/us-news/2020/jun/23/millions-of-americans-cant-afford-water-bills-rise',
 'https://www.msn.com/en-gb/news/uknews/hospitality-bailout-scheme-branded-a-con-as-firms-struggle-to-get-1-500-grant/ar-BB19HTbc',
 'https://deardesigner.co.uk',
 'https://www.crowdyfan.com/worldwide/wedding-gown/42',
 'https://homehacks.co/50-useful-beauty-hacks/',
 'https://www.theguardian.com/football/live/2020/sep/27/manchester-city-v-leicester-city-premier-league-live',
 'https://www.futbin.com/21/player/573/fabinho',
 'https://www.crowdyfan.com/worldwide/wedding-gown/13',
 'https://www.crowdyfan.com/worldwide/wedding-gown/23',
 'https://www.futbin.com/21/player/612/leroy-sane',
 'https://www.eadt.co.uk/sport/league-one-transfer-guide-2020-21-1-6881725',
 'https://www.t3.com/features/best-running-shoes',
 'https://www.crowdyfan.com/worldwide/wedding-gown/6',
 'https://www.msn.com/pl-pl/styl-zycia/travel/cudowny-%C5%9Bwiat-zapieraj%C4%85ce-dech-w-piersiach-widoki-z-r%C3%B3%C5%BCnych-miejsc-naszej-planety/ss-AAGnBMi',
 'https://ext.theperspective.com/clever-and-creative-graffiti/4/',
 'https://www.standard.co.uk/news/world/donald-trump-coronavirus-pandemic-comments-timeline-a4561601.html',
 'https://www.msn.com/en-gb/foodanddrink/other/james-martin-s-incredible-outdoor-kitchen-will-blow-your-mind/ar-BB19z8ih',
 'https://www.cornwalllive.com/news/cornwall-news/confirmed-coronavirus-cases-fall-across-4614786',
 'https://www.futbin.com/21/player/570/roberto-firmino',
 'https://www.dailymail.co.uk/sport/teampages/southampton.html',
 'https://www.standard.co.uk/news/uk/lockdown-measures-north-east-hancock-a4558186.html',
 'https://www.independent.co.uk/arts-entertainment/comedy/features/sian-gibson-interview-call-centre-worker-peter-kay-s-car-share-a6811026.html',
 'https://www.futbin.com/21/player/25736/nelson-semedo',
 'https://www.independent.co.uk/news/uk/politics/brexit-no-deal-tactic-boris-johnson-david-lidington-b599750.html',
 'https://www.msn.com/en-gb/lifestyle/other/can-i-leave-a-local-lockdown-to-go-on-holiday/ar-BB19wRic',
 'https://www.msn.com/en-gb/entertainment/celebrity/rita-ora-sparks-engagement-speculation-with-ring-on-her-wedding-finger/ar-BB19HfZE',
 'https://www.msn.com/en-gb/entertainment/movies/joaquin-phoenix-from-tragedy-to-happy-fatherhood/ss-BB19uYnN',
 'https://www.msn.com/en-gb/entertainment/tv/gemma-atkinson-wells-up-live-on-air-after-gorka-marquezs-emotional-surprise/ar-BB19InRs',
 'https://www.dailymail.co.uk/news/boris_johnson/index.html',
 'https://www.msn.com/en-gb/news/royal-family/claim-meghan-allowed-details-of-her-private-life-to-be-fed-to-authors-of-finding-freedom/ar-BB19CCAp',
 'https://www.biblegateway.com/passage/',
 'https://www.theguardian.com/football/live/2020/oct/05/transfer-deadline-day-2020-cavani-partey-sancho-and-more-news-live',
 'https://www.msn.com/en-gb/lifestyle/style/kate-middleton-breaks-the-internet-with-her-%c2%a335-linen-shirt/ar-BB19AQ57',
 'https://www.dailymail.co.uk/news/article-8772683/Chef-Jamie-Oliver-joins-Mail-Sundays-war-toxic-food.html',
 'https://stardewvalleywiki.com/Penny',
 'https://www.plymouthherald.co.uk/news/plymouth-news/confirmed-coronavirus-cases-fall-across-4614786',
 'https://www.msn.com/en-gb/money/other/these-amazing-homes-cost-nothing-to-run/ss-BB19CboF',
 'https://www.hertfordshiremercury.co.uk/news/hertfordshire-news/38-breathtaking-hertfordshire-walks-perfect-4263258',
 'https://ext.theperspective.com/clever-and-creative-graffiti/6/',
 'https://www.msn.com/en-gb/entertainment/celebrity/naga-munchetty-looks-wildly-different-with-long-hair-transformation-%e2%80%93-see-photo/ar-BB19uzj3',
 'https://www.standard.co.uk/news/uk/closing-schools-increase-coronavirus-deaths-edinburgh-study-a4566076.html',
 'https://www.standard.co.uk/news/uk/uk-coronavirus-cases-today-deaths-a4572002.html',
 'https://www.futbin.com/21/player/671/david-alaba',
 'https://www.standard.co.uk/news/uk/emergency-lockdown-london-north-england-socialising-household-mixing-a4557601.html',
 'https://www.futbin.com/21/player/25701/ansu-fati',
 'https://www.msn.com/en-gb/travel/tripideas/25-fictional-places-we-d-love-to-visit/ss-BB19EOWK',
 'https://www.standard.co.uk/news/london/london-coronavirus-cases-latest-figures-tier-two-lockdown-a4568481.html',
 'https://www.msn.com/en-gb/news/world/floods-in-france-italy-swept-bodies-out-of-cemeteries/ar-BB19KCeT',
 'https://www.msn.com/en-gb/news/brexit/with-its-legal-action-over-this-uk-bill-the-eu-is-showing-it-means-business/ar-BB19Dh5D',
 'https://www.dailymail.co.uk/news/new_zealand/index.html',
 'https://www.independent.co.uk/life-style/food-and-drink/coronavirus-restrictions-three-tier-lockdown-boris-johnson-restaurants-bars-pubs-hospitality-b990820.html',
 'https://www.standard.co.uk/showbiz/celebrity-news/nicola-adams-lesbian-gay-strictly-come-dancing-a4542561.html',
 'https://www.msn.com/pl-pl/styl-zycia/podroze/na-zdj%C4%99ciach-majestatyczne-g%C3%B3ry-z-ca%C5%82ego-%C5%9Bwiata/ss-BBYaukt',
 'https://www.futbin.com/squad-building-challenges/ALL/21/Give%20Me%20Five',
 'https://www.op.gg/champion/statistics',
 'https://statisticsglobe.com/change-font-size-of-ggplot2-plot-in-r-axis-text-main-title-legend']

```

### adbar commented on Oct 26, 2020 
More actions
Thank you very much for the lists, I believe they are useful! Could you please clarify the following points? - Which version of trafilatura are you using, with which parameters? I assume you use the last readability-lxml version? (0.8.1) - Sometimes less text is better (boilerplate elements hopefully missing), similarly the fact that there is more text isn't necessary significant. The presence of footers doesn't seem too good, do you have a few examples at hand? - Do you have a list of URLs for which trafilatura doesn't return any text whatsoever (although it probably should)? To sum up, minor differences in text output are not necessarily a concern, I'd say that discrepancies over 5-10% are meaningful.
On 10/26/20 6:35 PM, Dennis wrote: [@adbar](https://github.com/adbar) <<https://github.com/adbar>> Thank you very much for your reply! I tried a comparison today, and it seems that the libs differ quite a bit on their extraction, but it is not clear to me when and why. Some information I think I have is that: * |trafilatura| seems to pick up footers more often * fallback does not seem to work as I can get no text from your lib, but text from readability I am not sure if you will find this useful, but I am providing you some URLs on which the two libs differ the most, the following URLs are where your lib extracts more text: |['<https://www.awesomeinventions.com/my-house-not-my-cat-photos>', '<https://youhadmeatgardening.com/lemon-tree-from-seed>', '<https://www.dailymail.co.uk/money/markets/article-8805521/BUSINESS-LIVE-Stimulus-hopes-boost-markets.html>', '<https://www.historychronicle.com/view/90s-vintage-pics-hc/>', '<https://pawszilla.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/28/>', '<https://www.calcalist.co.il/internet/articles/0,7340,L-3835935,00.html>', '<https://www.onthemarket.com/farms-land/property/cornwall/>', '<https://www.theguardian.com/world/live/2020/oct/08/coronavirus-live-news-brazil-cases-pass-5m-trump-calls-catching-covid-a-blessing-in-disguise>', '<https://www.walesonline.co.uk/news/wales-news/coronavirus-live-updates-lockdown-gething-19049119>', '<https://www.nottinghampost.com/news/local-news/live-nottinghamshire-lockdown-tighter-restrictions-4585870>', '<https://www.graduatez.com/view/scientists-are-in-awe-after-finding-a-bewildering-creature-beached-on-the-californian-shore/>', '<https://www.loksatta.com>', '<https://www.lefigaro.fr>', '<https://www.theyeshivaworld.com>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/everton-transfer-news-live-rodriguez-19087404>', '<https://mydailymagazine.com/post-a1e720df/>', '<https://www.historychronicle.com/view/history-discovery-secrets-hc/>', '<https://www.manchestereveningnews.co.uk/sport/football/football-news/leeds-vs-man-city-live-19043874>', '<https://www.dailymail.co.uk/travel/escape/article-8814663/The-worlds-best-hotels-islands-cities-ski-resorts-revealed-Conde-Nast-Traveller.html>', '<https://www.business-live.co.uk/economic-development/boris-johnson-unveil-lockdown-restrictions-19088918>', '<https://www.dailyrecord.co.uk/news/politics/nicola-sturgeon-coronavirus-update-live-22799031>', '<https://musiccritic.com/equipment/guitars/best-acoustic-electric-guitar>', '<https://www.dailyrecord.co.uk/sport/football/football-transfer-news/transfer-deadline-live-rangers-celtic-22792735>', '<https://www.gumtree.com/dogs/scotland/page6>', '<https://www.moneycontrol.com>', '<https://www.getreading.co.uk/news/reading-berkshire-news/live-homes-west-reading-suffer-19062352>', '<https://www.hulldailymail.co.uk/news/hull-east-yorkshire-news/3-tier-lockdown-live-updates-4597247>', '<https://www.nature.com/articles/ncomms4887>', '<https://www.dailyrecord.co.uk/sport/football/football-news/europa-league-draw-live-celtic-22779308>', '<https://www.gumtree.com/dogs/uk/dogs+northern+ireland/page2>', '<https://alphamom.com>', '<https://www.domesticatedcompanion.com/actors-havent-done-anything-in-years/2/>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/liverpool-transfer-news-rumours-butland-19055637>', '<https://www.insider.com/hard-brainteasers-riddles-for-smart-people-2017-9>', '<https://www.catster.com/lifestyle/bringing-an-adult-cat-into-your-home>', '<https://www.express.co.uk/life-style/science-technology/1340039/iPhone-12-Release-Date-October-13-2020-Apple-Fans-Not-Long-Left-To-Wait-UK/amp>', '<https://www.pinkvilla.com/entertainment/news/saif-ali-khan-talks-about-sara-ali-khan-and-how-if-he-s-hurt-her-taimur-can-t-make-him-feel-better-566895>', '<https://reviews.mtbr.com>', '<https://www.dailymail.co.uk/news/article-8803493/Trump-administrations-fear-leaks-leaves-White-House-staff-dark.html>', '<https://kit.honestjohn.co.uk>', '<https://www.trivia.com/view/a-letter-from-this-womans-biological-mother-changed-her-life-forever/>', '<https://www.gumtree.com/dogs/uk/puppies/page12>', '<https://www.essexlive.news/news/essex-news/live-coronavirus-updates-essex-awaits-4604321>', '<https://www.dailymail.co.uk/sport/football/article-8797665/Europa-League-group-stage-draw-2020-21-LIVE-Result.html>', '<https://www.lefigaro.fr/politique>', '<https://www.chocolate.com/view/life-of-steven-mcqueen-cho/>', '<https://www.gumtree.com/dogs/uk/page2>', '<https://www.examinerlive.co.uk/sport/football/transfer-news/huddersfield-town-transfer-news-live-19112945>', '<https://www.walesonline.co.uk/sport/football/transfer-news/cardiff-city-transfer-news-live-19112387>', '<https://www.gumtree.com/cars/uk/audi/a6/page2>', '<https://www.thespruce.com/ingenious-ikea-billy-bookcase-hacks-4006865>', '<https://iamafoodblog.com/birria-tacos-recipe>', '<https://bestofmachinery.com/best-hearing-protection-for-lawn-mowing>', '<https://www.wallstreetmojo.com/preferred-shares>', '<https://parentinfluence.com>', '<https://www.grimsbytelegraph.co.uk/news/uk-world-news/live-boris-johnson-press-conference-4561866>', '<https://www.autoscout24.de/lst/>', '<https://www.msn.com/en-za>', '<https://www.lefigaro.fr/societes>', '<https://www.devonlive.com/news/devon-news/planning-applications-submitted-devon-week-4506950>', '<https://www.oversixty.com.au>', '<https://www.dailypost.co.uk/news/north-wales-news/coronavirus-live-press-conference-take-19099922.amp>', '<https://www.trivia.com/view/cool-google-earth-finds-trv/>', '<https://www.pinkvilla.com/tv/news-gossip/bigg-boss-6-s-sana-khan-bids-goodbye-showbiz-industry-forever-decides-spend-life-serving-humanity-567296>', '<https://www.dailymail.co.uk/sport/football/article-8772027/Crystal-Palace-vs-Everton-Premier-League-Live-result.html>', '<https://www.hulldailymail.co.uk/sport/rugby-league/rugby-league-live-transfer-news-4560871>', '<https://www.manchestereveningnews.co.uk/sport/football/transfer-news/man-utd-transfer-news-recap-19042171>', '<https://www.yardbarker.com/entertainment/gallery/the_most_talked_about_movie_moments_of_the_2010s/s1__30411269>', '<https://www.historychronicle.com/view/thomas-jeffersons-hidden-rooms-hc/>', '<https://www.gumtree.com/property-to-rent/plymouth/page2>', '<https://www.dailymail.co.uk/sport/football/article-8803121/Transfer-News-LIVE-Latest-Premier-League-European-signings-deals-rumours.html>', '<https://www.hulldailymail.co.uk/news/uk-world-news/live-coronavirus-uk-lockdown-rules-4579067>', '<https://www.buzzfeed.com/quizzes>', '<https://www.liverpoolecho.co.uk/news/liverpool-news/live-coronavirus-boris-vaccine-tests-19049134>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/everton-news-transfer-rumours-godfrey-19025712>', '<https://www.dailyrecord.co.uk/sport/football/football-transfer-news/transfer-news-live-celtic-rangers-22765511>', '<https://www.mabelandmoxie.com/amp/These+Are+The+Smartest+Dog+Breeds+In+The+World,+Ranked>', '<https://www.pinkvilla.com/entertainment/news/kangana-ranaut-reacts-karan-srk-other-productions-uniting-against-media-houses-file-case-me-also-567902>', '<https://www.vielfliegertreff.de>', '<https://www.gumtree.com/cars/uk/left+hand+drive/page7>', '<https://www.gumtree.com/cats/uk/kittens/page2>', '<https://www.chroniclelive.co.uk/news/north-east-news/uk-deaths-coronavirus-live-updates-18935120>', '<https://www.manchestereveningnews.co.uk/news/greater-manchester-news/live-mayor-andy-burnham-holds-19023674>', '<https://www.telegraph.co.uk/news/2020/10/07/travel-latest-covid-passport-greece-italy-turkey-quarantine>', '<https://historicalpost.com/anthropology-and-history/places/niagara-falls-runs-dry-reveals-bodies-1969-united-states-canada/12/>', '<https://www.pinkvilla.com/entertainment/news/shabana-azmi-opens-unrest-bollywood-and-kangana-ranauts-outrageous-remarks-566625>', '<https://www.simbaly.com/view/the-jackson-kids-now-sim/>', '<https://www.dailymail.co.uk/sport/football/article-8784211/Transfer-news-LIVE-Latest-Premier-League-European-club-signings-deals-rumours.html>', '<https://www.gumtree.com/dogs/uk/french+bulldog/page3>', '<https://powerlisting.fandom.com/wiki/List_of_Supernatural_Powers_and_Abilities>', '<https://www.standard.co.uk/news/uk/uk-coronavirus-live-latest-updates-boris-johnson-threetier-lockdown-a4568406.html>', '<https://m.khaleejtimes.com>', '<https://divinityoriginalsin2.wiki.fextralife.com>', '<https://forums.civfanatics.com>', '<https://www.gumtree.com/dogs/uk/page6>', '<https://www.insider.com/what-are-healing-crystals-how-to-use-them-2018-7>', '<https://www.msn.com/fr-fr>', '<https://www.gumtree.com/cars/northern-ireland/page2>', '<https://www.birminghammail.co.uk/sport/football/transfer-news/wolves-deadline-day-transfers-live-19037027>', '<https://www.leeds-live.co.uk/news/uk-world-news/live-coronavirus-sheffield-leeds-rates-19042623>', '<https://itsfoss.com/best-linux-desktop-environments>', '<https://www.historychronicle.com/view/cleaning-lady-shock-prank/>', '<https://flawlessfood.co.uk/olive-herb-focaccia-bread>', '<https://www.luxandlush.com/view/woman-sells-a-house-nobody-expected-to-find-this-inside-lux/>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/live-liverpool-transfer-news-rumours-19074803>', '<https://www.everydayhealth.com/healthy-living/fascinating-facts-about-body-temperature.aspx>', '<https://rus.delfi.lv>', '<https://www.birminghammail.co.uk/sport/football/transfer-news/villa-live-king-transfer-latest-19062357>', '<https://hu.motorsport.com>', '<https://www.foxyfolksy.com/chocolate-buttercream-frosting-without-powdered-sugar-ermine-icing>', '<https://toppoptoday.com>', '<https://bap.navigator.web.de>', '<https://trends.bibamagazine.fr/en/prince-william-and-harry-technically-have-a-sister-and-they-completely-ignore-her-2/20>', '<https://www.telegraph.co.uk/business/2020/10/06/joe-bidens-war-economy-policies-radical-break-status-quo>', '<https://www.gumtree.com/dogs/scotland/page4>', '<https://www.birminghammail.co.uk/sport/football/transfer-news/aston-villa-transfers-rashica-benrahma-19037412>', '<https://www.standard.co.uk/news/uk/coronavirus-live-latest-updates-pubs-close-a4566031.html>', '<https://www.gumtree.com/cars/uk/page5>', '<https://www.euronews.com>', '<https://www.graduatez.com/view/surprising-findings-pipes/>', '<https://www.msn.com/de-ch/>', '<https://pawszilla.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/65/>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/live-everton-transfer-news-bernard-19075370>', '<https://www.historychronicle.com/view/ozzy-osbourne-facts-hc/>', '<https://zenherald.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/30/>', '<https://www.manchestereveningnews.co.uk/news/uk-news/pmqs-live-prime-minister-boris-19101281>', '<https://www.mirror.co.uk/sport/football/transfer-news/transfer-news-live-smalling-dele-22721256>', '<https://sportowefakty.wp.pl/zuzel/relacja/110331/fogo-unia-leszno-rm-solar-falubaz-zielona-gora>', '<https://www.gumtree.com/cars/scotland/page3>', '<https://guides.gamepressure.com>', '<https://www.msn.com/en-gb>', '<https://www.chroniclelive.co.uk/news/north-east-news/coronavirus-restrictions-uk-live-updates-19026811>', '<https://hipertextual.com>', '<https://www.luxandlush.com/view/celeb-kids-are-not-little-anymore-fb-lux/>', '<https://www.historychronicle.com/view/70s-80s-celebs-kids-fb-hc/>', '<https://m.sportowefakty.wp.pl/pilka-nozna/relacja/106622/polska-finlandia>', '<https://www.gumtree.com/cars/uk/range+rover+sport/page2>', '<https://www.stokesentinel.co.uk/news/stoke-on-trent-news/live-covid-19-updates-across-4588547>', '<https://www.bristolpost.co.uk/sport/football/football-news/bristol-rovers-transfer-questions-garner-4555153>', '<https://www.visitlancashire.com/things-to-do/animal-and-farm-attractions>', '<https://www.mirror.co.uk/sport/football/transfer-news/transfer-news-live-arsenal-sancho-22752560>', '<https://www.lesechos.fr>', '<https://www.gumtree.com/for-sale/uk/page2>', '<https://www.bristolpost.co.uk/news/health/coronavirus-cases-lockdown-bristol-live-4597246>', '<https://www.simbaly.com/view/celeb-daughters-grown-up-co-sim/>', '<https://www.buzzfeed.com/alliehayes/weird-house-rules-parents-reddit>', '<https://www.gumtree.com/dogs/northern-ireland/page4>', '<https://www.autosport.com>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/everton-news-transfer-rumours-live-19025712>', '<https://www.rtl.be>', '<https://www.standard.co.uk/news/uk/coronavirus-live-latest-updates-lockdown-vaccine-a4567091.html>', '<https://www.gazettelive.co.uk/news/teesside-news/coronavirus-live-boris-johnson-set-19088101>', '<https://cookieandkate.com/perfect-quinoa>', '<https://www.chroniclelive.co.uk/sport/football/football-news/newcastle-transfer-news-live-mourinho-19007685>', '<https://www.gumtree.com/cars/uk/land-rover/defender/page3>', '<https://www.lakesideloops.com/watson-cardigan>', '<https://www.chocolate.com/view/woman-sees-a-car-stop-for-pregnant-beggar-this-is-what-she-finds-when-she-follows/>', '<https://www.chroniclelive.co.uk/news/north-east-news/boris-johnson-announcement-live-updates-19090211>', '<https://www.sports.fr/direct-foot/50918/177512/lorient-olympique-lyonnais.html>', '<https://www.pinkvilla.com/entertainment/news/sushant-singh-rajputs-flatmate-siddharth-pithani-states-late-actor-did-not-meet-rhea-chakraborty-june-13-566132>', '<https://www.cornwalllive.com/news/cornwall-news/live-storm-alex-weather-traffic-4567887>', '<https://www.yourrulingplanet.com/view/instagram-golfer-paige/>', '<https://www.dublinlive.ie/news/health/level-5-lockdown-nphet-dublin-19053662>', '<https://www.thelist.com/214894/when-you-take-a-multivitamin-every-day-this-is-what-happens-to-your-body>', '<https://beta.southglos.gov.uk/new-south-gloucestershire-local-plan-2018-2036>', '<https://www.latest-hairstyles.com/mens/thin.html>', '<https://www.healthline.com/nutrition/ways-to-measure-body-fat>', '<https://www.themakeupdummy.com>', '<https://www.audi-sport.net/xf>', '<https://www.cheshire-live.co.uk/news/chester-cheshire-news/live-cheshire-coronavirus-national-lockdown-19049856.amp>', '<https://www.chroniclelive.co.uk/news/north-east-news/north-east-news-live-latest-19112705>', '<https://www.edinburghlive.co.uk/news/edinburgh-news/coronavirus-scotland-live-rules-latest-19046171>', '<https://www.ccna7.com/ccna2-v6-0/ccna2-v6-0-chapter-2-exam-answer-2017>', '<https://www.autocar.co.uk/slideshow/biggest-flops-automotive-history-0>', '<https://www.telegraph.co.uk/news/0/matt-favourite-covid-19-cartoons-think-laughing-something-makes>', '<https://www.pinkvilla.com/tv/news-gossip/exclusive-here-s-why-salman-khan-s-bigg-boss-14-will-air-half-hour-there-good-news-565189>', '<https://www.manchestereveningnews.co.uk/news/uk-news/live-boris-johnson-leads-downing-19091296>', '<https://www.gumtree.com/caravans/uk/page3>', '<https://www.cheshire-live.co.uk/news/chester-cheshire-news/live-cheshire-lockdown-coronavirus-council-19021297>', '<https://happyyouhappyfamily.com>', '<https://thepostpartumparty.com/how-to-set-up-a-baby-nursery-in-a-small-space>', '<https://www.realsimple.com/home-organizing/gardening/outdoor/hydrangea-care>', '<https://www.devonlive.com/news/local-news/live-m5-fire-bristol-avonmouth-4575486>', '<https://www.historychronicle.com/view/priest-sues-millions-hc/>', '<https://www.cadena100.es>', '<https://www.minq.com/lifestyle/2553886/students-recall-the-absolute-dumbest-thing-theyve-ever-heard-a-teacher-say/>', '<https://www.levante-emv.com>', '<https://www.authenticfoodquest.com/popular-portuguese-dishes>', '<https://www.instyle.com/beauty/wigs-for-black-women-cancer>', '<https://www.theprimarymarket.com/view/pizza-delivery-employee-tpm/>', '<http://www.msn.com/en-gb/>', '<https://www.dailymail.co.uk/sport/football/article-8772175/Sheffield-United-vs-Leeds-Premier-League-Live-result.html>', '<https://www.minq.com/lifestyle/2495316/students-share-the-rudest-thing-a-teacher-ever-said-to-them/>', '<https://www.nottinghampost.com/sport/football/football-news/nottingham-forest-transfer-news-live-4597836>', '<https://www.msn.com/es-es>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/liverpool-transfer-news-rumours-kabak-19042594>', '<https://wiadomosci.gazeta.pl>', '<https://www.nationalrail.co.uk/service_disruptions/245738.aspx>', '<https://www.domesticatedcompanion.com/actors-havent-done-anything-in-years/>', '<https://www.caughtoffside.com/2020/09/27/agreement-reached-man-united-look-set-to-sign-defender-as-they-reach-an-agreement-on-the-final-details/>', '<https://www.corkbeo.ie/news/local-news/level-3-live-cork-ireland-19056312>', '<https://www.historychronicle.com/view/single-celebs-hc/>', '<https://www.historychronicle.com/view/donny-osmond-confession-hc/>', '<https://www.somersetlive.co.uk/news/somerset-news/live-storm-alex-weather-traffic-4568051>', '<https://www.theprimarymarket.com/view/elderly-house-sell/>', '<https://www.luxandlush.com/view/behind-the-scenes-with-barbi-benton/>', '<https://magellantimes.com/pop-culture/celebrities/fans-expressed-fears-celine-dions-appearance-savagely-responded/37/>', '<https://www.nerfplz.com>', '<https://www.disneytouristblog.com/disney-world-news-star-wars-permit-frozen-ride-refurbishment-restaurants-returning>', '<https://trendscatchers.co.uk/index.php/en/2020/07/09/prince-harry-claims-that-meghan-markle-might-not-be-the-one-2/31>', '<https://www.ign.com/articles/the-best-ssd-for-gaming>', '<https://www.birminghammail.co.uk/sport/football/transfer-news/villa-live-deadline-day-king-19062357>', '<https://www.telegraph.co.uk/opinion/2020/10/04/lettersgps-have-worked-crisis-often-personal-cost>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/live-everton-transfer-news-rumours-19061794>', '<https://www.liverpoolecho.co.uk/sport/football/football-news/liverpool-transfer-news-rumours-live-19025709>', '<https://cookieandkate.com/mujaddara-recipe>', '<https://trendscatchers.co.uk/index.php/en/2020/07/09/prince-harry-claims-that-meghan-markle-might-not-be-the-one-2/30>', '<https://www.theguardian.com/society>', '<https://www.nature.com/articles/s41467-018-04619-5>', '<https://www.birminghammail.co.uk/sport/football/transfer-news/transfer-news-west-brom-live-19036796>', '<https://www.divein.com>', '<https://www.historychronicle.com/view/real-noahs-ark-hc/>', '<https://www.preloved.co.uk/classifieds/furniture-fittings/kitchen-furniture/all/uk/used+kitchen+cabinets+sale>', '<http://wiadomosci.gazeta.pl>', '<https://www.dailyrecord.co.uk/sport/football/football-news/celtic-vs-rangers-live-score-22860327>', '<https://www.domesticatedcompanion.com/each-state-perfectly-portrayed-in-one-photograph/2/>', '<https://www.gumtree.com/dogs/uk/northern+ireland+pets/page2>', '<https://www.hertfordshiremercury.co.uk/news/hertfordshire-news/live-boris-johnson-speech-updates-4597736>', '<https://www.gazettelive.co.uk/sport/football/transfer-news/middlesbrough-transfers-yannick-bolasie-striker-19111028>', '<https://www.cambridge-news.co.uk/news/uk-world-news/live-updates-boris-johnson-tierlockdown-19117181>', '<http://www.msn.com/>', '<https://www.kentlive.news/news/kent-news/live-updates-covid-infection-rates-4597748>', '<https://www.goodhousekeeping.com/holidays/gift-ideas/g1266/handmade-gifts>', '<https://www.walesonline.co.uk/news/wales-news/wales-breaking-news-traffic-weather-19075607>', '<https://www.visitwiltshire.co.uk/accommodation/self-catering>', '<https://www.historychronicle.com/view/bing-crosby-life-hc/>', '<https://www.liverpoolecho.co.uk/news/liverpool-news/live-uk-coronavirus-updates-merseyside-19002010>', '<https://crinacle.com/2020/02/19/the-audiophiles-perspective-samsung-galaxy-buds>', '<https://www.mirror.co.uk/sport/football/transfer-news/arsenal-transfer-news-live-partey-22790130>', '<https://www.chocolate.com/view/70s-80s-celebs-kids-fb-cho/>', '<https://www.domesticatedcompanion.com/actors-havent-done-anything-in-years/11/>', '<https://www.gumtree.com/dogs/uk/jack+russell/page4>', '<https://www.haaretz.com/israel-news/business/.premium-this-year-israeli-energy-finally-went-green-but-the-revolution-is-just-beginning-1.9214282>', '<https://natashaskitchen.com/chicken-stir-fry-recipe>', '<https://www.hulldailymail.co.uk/news/uk-world-news/coronavirus-live-cases-lockdown-updates-4573922>', '<https://www.primandprep.com>', '<https://www.organizationobsessed.com/20-amazing-organization-hacks-will-transform-bedroom>', '<https://www.bakewithpaws.com>', '<https://www.oprahmag.com/entertainment/g28335655/best-halloween-books>', '<https://www.trivia.com/view/61-of-the-best-red-carpet-mishaps/>', '<https://www.examinerlive.co.uk/news/west-yorkshire-news/live-coronavirus-sheffield-leeds-kirklees-19056079>', '<https://www.telegraph.co.uk/news/2020/10/10/return-students-caused-inevitable-spike-covid-cases>', '<https://www.leeds-live.co.uk/sport/leeds-united/leeds-united-u23s-live-highlights-19036388>'] | This batch is where readability extracts more text: |['<https://redtri.com/best-jokes-for-kids/slide/1>', '<https://www.msn.com/en-gb/news/uknews/uk-university-student-halls-too-full-to-be-safe-experts-warn/ar-BB19DUqK>', '<https://www.babysleepsite.com/schedules/toddler-schedule/>', '<https://www.msn.com/en-gb/foodanddrink/other/slow-cooker-turkey-chilli-is-healthier-but-just-as-comforting/ar-BB19KDYg>', '<https://www.dailymail.co.uk/sport/teampages/leicester.html>', '<https://www.msn.com/en-gb/lifestyle/travel/can-you-guess-these-capital-cities-from-up-high/ss-BB19DxUe>', '<https://www.independent.co.uk/news/uk/politics/coronavirus-false-reporting-contact-fine-penalty-b671230.html>', '<https://www.msn.com/en-gb/lifestyle/style/prince-louis-adorable-striped-knit-is-a-10-john-lewis-bargain/ar-BB19HUbk>', '<https://www.dailymail.co.uk/tvshowbiz/love-island/index.html>', '<https://www.discogs.com/sell/list>', '<https://www.msn.com/en-gb/travel/tripideas/these-are-the-world-s-most-beautiful-national-parks/ss-BB19FnGx>', '<https://www.msn.com/en-gb/travel/tripideas/this-enchanted-fairytale-treehouse-in-kent-is-the-perfect-autumn-staycation/ar-BB19I6Wz>', '<https://www.msn.com/en-gb/lifestyle/style/super-organised-star-closets-we-d-love-to-copy/ss-BB19IOde>', '<https://www.futbin.com/21/player/25735/leroy-sane>', '<https://www.msn.com/en-gb/news/techandscience/scientists-discover-24-planets-with-conditions-even-more-suitable-for-life-than-earth/ar-BB19HZlb>', '<https://www.mirror.co.uk/news/uk-news/breaking-englands-worst-schools-revealed-13899939>', '<https://relieved.co/brilliant-kitchen-tips-cooking-easier/>', '<https://www.standard.co.uk/news/uk/three-tier-lockdown-system-coronavirus-london-medium-risk-a4570041.html>', '<https://www.lifewire.com/screen-mirroring-lg-smart-tvs-4770959>', '<https://minecraft-server-list.com>', '<https://www.standard.co.uk/news/uk/boris-johnson-coronavirus-nation-briefing-100-a4559471.html>', '<https://www.fifplay.com/fifa-21-game-settings>', '<https://www.independent.co.uk/news/uk/politics/brexit-boris-johnson-michael-gove-northern-ireland-border-b669752.html>', '<https://www.theguardian.com/uk-news/2020/oct/09/rishi-sunak-expands-wage-subsidies-to-head-off-winter-surge-in-job-losses>', '<https://www.futbin.com/21/player/25374/thomas-partey>', '<https://www.standard.co.uk/news/uk/turkey-poland-caribbean-islands-added-to-uk-quarantine-list-a4561256.html>', '<https://www.dailymail.co.uk/news/article-8747257/Is-England-heading-HALF-TERM-lockdown.html>', '<https://www.independent.co.uk/news/uk/politics/brexit-no-deal-summit-boris-johnson-eu-fishing-state-aid-von-der-leyen-michel-b1041344.html>', '<https://www.msn.com/en-gb/lifestyle/style/kate-middleton-breaks-the-internet-with-her-35-linen-shirt/ar-BB19AQ57>', '<https://ext.theperspective.com/items-we-never-knew-we-wanted/1/>', '<https://www.futbin.com/21/player/681/ferland-mendy>', '<https://www.popsugar.co.uk/smart-living/Cheap-Homemade-Halloween-Costumes-42432483/amp>', '<https://www.msn.com/en-gb/money/homeandproperty/celebrity-real-estate-in-october-chris-hemsworth-demi-lovato-and-more/ss-BB19BHew>', '<https://spotlightstories.co/50-hilarious-exam-answers-students-given/>', '<https://www.futbin.com/21/player/612/leroy-san%C3%A9>', '<https://www.tomshardware.com/uk/reviews/best-gpus,4380.html>', '<https://harrypotter.fandom.com/wiki/Hufflepuff>', '<https://docplayer.net>', '<https://www.theguardian.com/us-news/2020/jun/23/millions-of-americans-cant-afford-water-bills-rise>', '<https://www.msn.com/en-gb/news/uknews/hospitality-bailout-scheme-branded-a-con-as-firms-struggle-to-get-1-500-grant/ar-BB19HTbc>', '<https://deardesigner.co.uk>', '<https://www.crowdyfan.com/worldwide/wedding-gown/42>', '<https://homehacks.co/50-useful-beauty-hacks/>', '<https://www.theguardian.com/football/live/2020/sep/27/manchester-city-v-leicester-city-premier-league-live>', '<https://www.futbin.com/21/player/573/fabinho>', '<https://www.crowdyfan.com/worldwide/wedding-gown/13>', '<https://www.crowdyfan.com/worldwide/wedding-gown/23>', '<https://www.futbin.com/21/player/612/leroy-sane>', '<https://www.eadt.co.uk/sport/league-one-transfer-guide-2020-21-1-6881725>', '<https://www.t3.com/features/best-running-shoes>', '<https://www.crowdyfan.com/worldwide/wedding-gown/6>', '<https://www.msn.com/pl-pl/styl-zycia/travel/cudowny-%C5%9Bwiat-zapieraj%C4%85ce-dech-w-piersiach-widoki-z-r%C3%B3%C5%BCnych-miejsc-naszej-planety/ss-AAGnBMi>', '<https://ext.theperspective.com/clever-and-creative-graffiti/4/>', '<https://www.standard.co.uk/news/world/donald-trump-coronavirus-pandemic-comments-timeline-a4561601.html>', '<https://www.msn.com/en-gb/foodanddrink/other/james-martin-s-incredible-outdoor-kitchen-will-blow-your-mind/ar-BB19z8ih>', '<https://www.cornwalllive.com/news/cornwall-news/confirmed-coronavirus-cases-fall-across-4614786>', '<https://www.futbin.com/21/player/570/roberto-firmino>', '<https://www.dailymail.co.uk/sport/teampages/southampton.html>', '<https://www.standard.co.uk/news/uk/lockdown-measures-north-east-hancock-a4558186.html>', '<https://www.independent.co.uk/arts-entertainment/comedy/features/sian-gibson-interview-call-centre-worker-peter-kay-s-car-share-a6811026.html>', '<https://www.futbin.com/21/player/25736/nelson-semedo>', '<https://www.independent.co.uk/news/uk/politics/brexit-no-deal-tactic-boris-johnson-david-lidington-b599750.html>', '<https://www.msn.com/en-gb/lifestyle/other/can-i-leave-a-local-lockdown-to-go-on-holiday/ar-BB19wRic>', '<https://www.msn.com/en-gb/entertainment/celebrity/rita-ora-sparks-engagement-speculation-with-ring-on-her-wedding-finger/ar-BB19HfZE>', '<https://www.msn.com/en-gb/entertainment/movies/joaquin-phoenix-from-tragedy-to-happy-fatherhood/ss-BB19uYnN>', '<https://www.msn.com/en-gb/entertainment/tv/gemma-atkinson-wells-up-live-on-air-after-gorka-marquezs-emotional-surprise/ar-BB19InRs>', '<https://www.dailymail.co.uk/news/boris_johnson/index.html>', '<https://www.msn.com/en-gb/news/royal-family/claim-meghan-allowed-details-of-her-private-life-to-be-fed-to-authors-of-finding-freedom/ar-BB19CCAp>', '<https://www.biblegateway.com/passage/>', '<https://www.theguardian.com/football/live/2020/oct/05/transfer-deadline-day-2020-cavani-partey-sancho-and-more-news-live>', '<https://www.msn.com/en-gb/lifestyle/style/kate-middleton-breaks-the-internet-with-her-%c2%a335-linen-shirt/ar-BB19AQ57>', '<https://www.dailymail.co.uk/news/article-8772683/Chef-Jamie-Oliver-joins-Mail-Sundays-war-toxic-food.html>', '<https://stardewvalleywiki.com/Penny>', '<https://www.plymouthherald.co.uk/news/plymouth-news/confirmed-coronavirus-cases-fall-across-4614786>', '<https://www.msn.com/en-gb/money/other/these-amazing-homes-cost-nothing-to-run/ss-BB19CboF>', '<https://www.hertfordshiremercury.co.uk/news/hertfordshire-news/38-breathtaking-hertfordshire-walks-perfect-4263258>', '<https://ext.theperspective.com/clever-and-creative-graffiti/6/>', '<https://www.msn.com/en-gb/entertainment/celebrity/naga-munchetty-looks-wildly-different-with-long-hair-transformation-%e2%80%93-see-photo/ar-BB19uzj3>', '<https://www.standard.co.uk/news/uk/closing-schools-increase-coronavirus-deaths-edinburgh-study-a4566076.html>', '<https://www.standard.co.uk/news/uk/uk-coronavirus-cases-today-deaths-a4572002.html>', '<https://www.futbin.com/21/player/671/david-alaba>', '<https://www.standard.co.uk/news/uk/emergency-lockdown-london-north-england-socialising-household-mixing-a4557601.html>', '<https://www.futbin.com/21/player/25701/ansu-fati>', '<https://www.msn.com/en-gb/travel/tripideas/25-fictional-places-we-d-love-to-visit/ss-BB19EOWK>', '<https://www.standard.co.uk/news/london/london-coronavirus-cases-latest-figures-tier-two-lockdown-a4568481.html>', '<https://www.msn.com/en-gb/news/world/floods-in-france-italy-swept-bodies-out-of-cemeteries/ar-BB19KCeT>', '<https://www.msn.com/en-gb/news/brexit/with-its-legal-action-over-this-uk-bill-the-eu-is-showing-it-means-business/ar-BB19Dh5D>', '<https://www.dailymail.co.uk/news/new_zealand/index.html>', '<https://www.independent.co.uk/life-style/food-and-drink/coronavirus-restrictions-three-tier-lockdown-boris-johnson-restaurants-bars-pubs-hospitality-b990820.html>', '<https://www.standard.co.uk/showbiz/celebrity-news/nicola-adams-lesbian-gay-strictly-come-dancing-a4542561.html>', '<https://www.msn.com/pl-pl/styl-zycia/podroze/na-zdj%C4%99ciach-majestatyczne-g%C3%B3ry-z-ca%C5%82ego-%C5%9Bwiata/ss-BBYaukt>', '<https://www.futbin.com/squad-building-challenges/ALL/21/Give%20Me%20Five>', '<https://www.op.gg/champion/statistics>', '<https://statisticsglobe.com/change-font-size-of-ggplot2-plot-in-r-axis-text-main-title-legend>'] | — You are receiving this because you were mentioned. Reply to this email directly, view it on GitHub <[#25 (comment)](https://github.com/adbar/trafilatura/issues/25#issuecomment-716710049)>, or unsubscribe <<https://github.com/notifications/unsubscribe-auth/AAQHAKX323JPNCFP5XNXOMDSMWXNTANCNFSM4S5WOLJQ>>. 
### ydennisy commented on Oct 26, 2020 
More actions
Hey [@adbar](https://github.com/adbar) to answer your points:
  * I am using the latest version from pypi 0.5.2 (settings; both comment and tables set to false)
  * yes using the latest of reareadability-lxml 0.8.1
  * yes I agree, less can be better! I am only including URLs where the difference was over 6k chars
  * within the list I provided of URLs where readability returns more, there are many where trafilatura returns None


### adbar commented on Oct 27, 2020 
More actions
Some fixes could be needed for a few patterns found in these webpages (partly addressed in [`62b1e9a`](https://github.com/adbar/trafilatura/commit/62b1e9ab249edc1ca003afb7b86c949c597a4692) and [`25a08ed`](https://github.com/adbar/trafilatura/commit/25a08edec50b300894d033c07ef71f2436d0260e)), that said text extraction remains a balancing act... I added a few pages to the evaluation, things should get slightly better by the next release.
I'd say that for most webpages in your list nothing is really wrong, what to do with pages like <https://www.futbin.com/21/player/25374/thomas-partey> remains a open for discussion. I'd say `trafilatura` remains more efficient overall in terms of precision and recall. Thanks again for the input!
### ydennisy commented on Oct 27, 2020 
More actions
Yeah I get that its a non exact process and maybe impossible to handle all cases.
When is the next release due?
Thanks for looking into this!
### adbar commented on Oct 28, 2020 
More actions
I plan to ship the next release by the end of next week at the latest.
ydennisy
### adbar commented on Nov 6, 2020 
More actions
The new release is out, if you have the occasion could you please confirm it's gotten better? It does in my benchmark.
### ydennisy commented on Nov 16, 2020 
More actions
Yeah will give it a try and come back to you!
added 
[Further information is requested](https://github.com/adbar/trafilatura/issues?q=state%3Aopen%20label%3A%22question%22)Further information is requested
[on Dec 7, 2020](https://github.com/adbar/trafilatura/issues/25#event-4080588132)
[Sign up for free](https://github.com/signup?return_to=https://github.com/adbar/trafilatura/issues/25)**to join this conversation on GitHub.** Already have an account? [Sign in to comment](https://github.com/login?return_to=https://github.com/adbar/trafilatura/issues/25)
## Metadata
## Metadata
No one assigned
[Further information is requested](https://github.com/adbar/trafilatura/issues?q=state%3Aopen%20label%3A%22question%22)Further information is requested
No projects
No milestone
None yet
No branches or pull requests
## Issue actions
