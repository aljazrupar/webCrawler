
import requests
import psycopg2
import urllib
import sys
import argparse
import concurrent.futures
from queue import Queue, Empty
from threading import Thread
from urllib.request import urlparse, urljoin
from bs4 import BeautifulSoup


internal_urls = set() #za vsak slucaj
external_urls = set() #za vsak slucaj

queue = Queue()
visited = set([])
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url): #najde vse linke na enem URL
    
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    print(soup)

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue

        # zdruzi url z domeno ce ni ze cel link.
        href = urljoin(url, href)
        parsed_href = urlparse(href)

        #sparsa link
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href): #ni valid url
            continue
        if href in internal_urls: #je ze v internal link. Popravi na queue pa visited
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                external_urls.add(href)
            continue
        urls.add(href)
        internal_urls.add(href)
    return urls

def scraper(url): #Funkcija za obdelovanje ene strani in dodajenje linkov v queue
    #dodaj se obdelavo strani.
    urls = get_all_website_links(url)
   
    for curr_url in urls:
        queue.put(curr_url)
    print(list(queue.queue))

def crawl():
    finish_count = 0

    while True:
        try:
            finish_count += 1

            if finish_count == 5:
                sys.exit()

            target_url = queue.get(timeout=10) #dobi link iz queue, cakaj 10s

            if target_url not in visited:
                visited.add(target_url)
                print(f'Processing url {target_url}')
                job = executor.submit(scraper,target_url)
                #mogoce je treba se neke callbacke delat in shranjevt nasledne linke prek tega.
                print(job)

            
        except Empty:
            print("All done")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    seed_url = "https://www.gov.si/"
    queue.put(seed_url)

    crawl()