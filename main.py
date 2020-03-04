import requests
from urllib.request import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import psycopg2
import urllib
import sys
import argparse
import urllib.robotparser
from queue import Queue, Empty
from concurrent.futures import ProcessPoolExecutor

colorama.init()
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET

internal_urls = set()
external_urls = set()

total_urls_visited = 0

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests.get(url).content, "html.parser")

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if href in internal_urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        urls.add(href)
        internal_urls.add(href)
    return urls

def crawl(url, max_urls=50): #crawl on specified site
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """
    


    global total_urls_visited
    total_urls_visited += 1
    links = get_all_website_links(url)
    for link in links:
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)

def crawlSite(url, max_urls=50):
    #save site to DB. Site as main website to be crawled. 
    rp = urllib.robotparser.RobotFileParser()
    robotsURL = urljoin(url,"/robots.txt")
    rp.set_url(robotsURL)
    rp.read()
    listSite_Maps = rp.site_maps() #tole ti da sam link do site_maps. Kaj se nj shran v PD?
    textRobots = urllib.request.urlopen(robotsURL).read()

    sys.exit()


    conn = psycopg2.connect(host="localhost", user="postgres", password="ourpass")
    conn.autocommit = True
    
    cur = conn.cursor()
    cur.execute("INSERT INTO crawldb.site VALUES(DEFAULT,%s, %s, %s)",(url,textRobots,listSite_Maps))
    cur.close()

    conn.close()

    crawl(url, max_urls)




seed_url = "https://www.gov.si/"
queued_urls = Queue()
queued_urls.put(seed_url)

processed_urls = set()




crawlSite("https://www.gov.si/", max_urls=100)

print("[+] Total Internal links:", len(internal_urls))
print("[+] Total External links:", len(external_urls))
print("[+] Total URLs:", len(external_urls) + len(internal_urls))

    