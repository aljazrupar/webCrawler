import argparse
import concurrent.futures
import datetime
import sys
import threading
import urllib
from queue import Queue, Empty
from urllib.request import urlparse, urljoin
import urllib.robotparser

import psycopg2
import requests
from bs4 import BeautifulSoup

internal_urls = set()  # za vsak slucaj
external_urls = set()  # za vsak slucaj

queue = Queue()
visited = set([])
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

lock = threading.Lock()

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_website_links(url):  # najde vse linke na enem URL

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

        # sparsa link
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):  # ni valid url
            # TODO
            continue
        if href in internal_urls:  # je ze v internal link. Popravi na queue pa visited
            # TODO
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                external_urls.add(href)
            continue
        urls.add(href)
        internal_urls.add(href)
    return urls


def scraper(target_url, id_of_new_site):  # Funkcija za obdelovanje ene strani in dodajenje linkov v queue
    # dodaj se obdelavo strani.

    response = requests.get(target_url)
    page_type_code = "NOT DEFINED"  # potrebno preverjanje še za druge type- binary...
    if response.headers['content-type'] == 'text/html':
        page_type_code = "HTML"
    status_code = response.status_code
    html_content = response.text

    with lock:
        cur = conn.cursor()
<<<<<<< HEAD
        
        cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT,%s, %s, %s,%s ,%s ,CURRENT_TIMESTAMP )",
        (id_of_new_site,'HTML' ,target_url,html_content,status_code)) #HTML se poprav
        
=======
        print(2.1)
        # to ne dela neki.
        cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT,%s, %s, %s,%s ,%s ,%s ) RETURNING id",
                    (id_of_new_site, page_type_code, target_url, html_content, status_code, timestamp))

        print(2.2)
>>>>>>> 28066cf8b26f7fa8391f4ed0ad52f0374230d6f7
        cur.close()

    print(3)
    urls = get_all_website_links(target_url)

    for curr_url in urls:
        queue.put(curr_url)
<<<<<<< HEAD
=======
    # print(list(queue.queue))

>>>>>>> 28066cf8b26f7fa8391f4ed0ad52f0374230d6f7

def crawl(id_of_new_site):
    finish_count = 0

    while True:
        try:
            finish_count += 1
            #TODO to bo treba popravt

            if finish_count == 5:
                sys.exit()

            #Je to kul da čaka?
            target_url = queue.get(timeout=10)  # dobi link iz queue, cakaj 10s

            if target_url not in visited:
                visited.add(target_url)
                print(f'Processing url {target_url}')

                executor.submit(scraper, target_url, id_of_new_site)

                # mogoce je treba se neke callbacke delat in shranjevt nasledne linke prek tega.
                # print(job)


        except Empty:
            print("All done")
        except Exception as e:
            print(e)


def manage_seed_url(url):
    with lock:
        cur = conn.cursor()
        rp = urllib.robotparser.RobotFileParser()
        robotsURL = urljoin(url, "/robots.txt")
        rp.set_url(robotsURL)
        rp.read()

        listSite_Maps = rp.site_maps()
        textRobots = urllib.request.urlopen(robotsURL).read().decode("utf-8")

        cur.execute("INSERT INTO crawldb.site VALUES(DEFAULT,%s, %s, %s) RETURNING id",
                    (url, textRobots, listSite_Maps))
        id_of_new_site = cur.fetchone()[0]
        cur.close()
        return id_of_new_site


if __name__ == '__main__':
    seed_url = "https://www.gov.si/"
    # globalen dostop do baze in cursorja
    global conn
    conn = psycopg2.connect(host="localhost", user="postgres", password="admin")
    conn.autocommit = True

    queue.put(seed_url)

    id_of_new_site = manage_seed_url(seed_url)
    crawl(id_of_new_site)

    conn.close()
