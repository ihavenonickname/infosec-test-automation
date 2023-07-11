# Handling duplicated sources in subdomain enumeration

## Premise

Subdomain enumeration tools have a list of sources that they scrap in order to extract information about subdomains. Common sources, such as [DNSdumbster](https://dnsdumpster.com/) and [Common Crawl](https://commoncrawl.org/), are scraped by several tools. Intuitively, it's a good idea to restrict the sources so that only one tool scraps each source in order to optimize the time spent. But that begs the question, what tool should scrap the common sources?

## Methodology

For this study, `amass` and `subfinder` are used.

The test contains 3 steps:

1. Execute both tools with all sources. This step exists so that there's a baseline to judge the results of the next steps.
2. Execute both tools but only `amass` uses the duplicate sources.
2. Execute both tools but only `subfinder` uses the duplicate sources.

`amass` is executed with the `-passive` flag so it doesn't probe the target. This ensures that both tools have the same overall behavior.

For completeness, here's the sources available for `amass`:

```
abuseipdb
active crawl
active dns
alienvault
alterations
anubisdb
arquivo
ask
askdns
baidu
bgptools
bgpview
bing
brute forcing
certspotter
commoncrawl
crtsh
digitorus
dns srv
dnsdumpster
dnshistory
dnsspy
duckduckgo
gists
google
grepapp
greynoise
hackerone
hackertarget
haw
hyperstat
leakix
maltiverse
mnemonic
pkey
pulsedive
rapiddns
reverse dns
riddler
searchcode
searx
shadowserver
sitedossier
spyonweb
sublist3rapi
synapsint
teamcymru
threatminer
ukwebarchive
urlscan
wayback
yahoo
```

And here's the sources available for `subfinder`:

```
alienvault
archiveis
bufferover
censys
certspotterold
commoncrawl
crtsh
dnsdumpster
entrust
hackertarget
intelx
ipv4info
passivetotal
rapiddns
sitedossier
sublist3r
threatcrowd
threatminer
waybackarchive
zoomeye
```

The duplicate sources (that is, the sources available for both tools) are:

```
alienvault
commoncrawl
crtsh
dnsdumpster
hackertarget
rapiddns
sitedossier
threatminer
```

Note that only public sources are listed; sources that require any type of key are ignored in this study.

## Results

### Baseline

* `amass`: 27.3 seconds
* `subfinder`: 30.9 seconds
* Total: 58.2 seconds

### Prefer amass

* `amass`: 25.6 seconds
* `subfinder`: 2.6 seconds
* Total: 28.2 seconds

### Prefer subfinder

* `amass`: 25.2 seconds
* `subfinder`: 30.7 seconds
* Total: 55.9 seconds

## Discussion

The results show that `subfinder` drastically reduces the execution time when it doesn't scrap the common sources. On the other hand, `amass` takes roughly the same amount of time regardless of the sources.

With that in mind, it's advantageous to let `amass` scrap the common sources while `subfinder` scraps its exclusive sources only.

It's important to note that the very same subdomains were found in all tests, meaning that the 3 strategies are equivalent in terms of result, varying only in performance.
