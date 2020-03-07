import argparse
import concurrent.futures
import datetime
import sys
import threading
import urllib
from queue import Queue, Empty
from urllib.request import urlparse, urljoin
import urllib.robotparser
import time
import psycopg2
import requests
from bs4 import BeautifulSoup

"""
GENERAL TODOs:

1.Narest lockse in threading
2.Poročilo
3.Narest hash strani in preverjat za duplikate
4.Za linke najdt še onclick javascript
5.Narest nekako da se dodajajo linki v db
????To make sure that you correctly gather all the needed content placed into the DOM by Javascript, you should use headless browsers. Googlebot implements this as a two-step process or expects to retrieve dynamically built web page from an HTTP server.
Za preveriti:
5 sec na IP delay
crawl-delay - kaj je kako ga preveriti
"""

#num_workers = int(sys.argv[1])


queue = Queue()
visited = set([])
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
schemes = ["", "www", "http", "https"]
lock = threading.Lock()
visitedPages = set()

def get_all_website_links(url,id_of_new_page): # najde vse linke na enem URL

    urls = set()
    # domain name of the URL without the protocol
    soup = BeautifulSoup(requests.get(url).content, "html.parser")

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue

        # zdruzi url z domeno ce ni ze cel link.
        href = urljoin(url, href)
        parsed_href = urlparse(href)

        # sparsa link
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        if("gov.si" in href):
            urls.add(href)

    img_tags = soup.find_all('img')

    ImgUrls = [img['src'] for img in img_tags]
    cur = conn.cursor()
    for imgUrl in ImgUrls:

        # zdruzi url z domeno ce ni ze cel link.
        imgCleanUrl = urljoin(url, imgUrl)
        parsed_img = urlparse(imgCleanUrl)
        print(parsed_img)
        # sparsa link
        imgCleanUrl = parsed_img.scheme + "://" + parsed_img.netloc + parsed_img.path
        filename = imgCleanUrl.split("/")[-1]
        content_type = filename.split(".")[-1]

        if parsed_img.scheme in schemes:
            response = requests.get(imgCleanUrl)

            cur.execute("INSERT INTO crawldb.image VALUES(DEFAULT,%s, %s, %s,%s ,CURRENT_TIMESTAMP)",
                (id_of_new_page, filename, content_type, "BINARY"))
    cur.close()
    return urls


def scraper(url, id_of_new_site):  # Funkcija za obdelovanje ene strani in dodajenje linkov v queue

    response = requests.get(url)

    status_code = response.status_code
    html_content = response.text

    #TODO dodat še za duplicate page
    if 'html' in response.headers['content-type']:

        #with lock:

        cur = conn.cursor()
        cur.execute("SELECT id FROM crawldb.page WHERE url=" + "'" + url + "'")
        data = cur.fetchone()
        if not data:

            cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT,%s, %s, %s,%s ,%s ,CURRENT_TIMESTAMP )",
                    (id_of_new_site, "HTML", url, html_content, status_code))
            id_of_new_page = cur.fetchone()[0]

        else:
            id_of_new_page = data[0]

    else:
        #with lock:

        cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT,%s, %s, %s,%s ,%s ,CURRENT_TIMESTAMP )",
                        (id_of_new_site, 'BINARY', url, "NULL", status_code))
        id_of_new_page = cur.fetchone()[0]

        response = requests.get(url)

        cur.execute("INSERT INTO crawldb.page_data VALUES(DEFAULT,%s, %s,%s ,%s )",
                    (id_of_new_page,  response.headers['content-type'], "BINARY"))

        cur.close()

    urls = get_all_website_links(url, id_of_new_page)
    for curr_url in urls:
        queue.put(curr_url)

    if(not queue.empty()):
        crawlNext()
    else:
        return

def crawlNext():

    target_url = queue.get(block=True)
    print(target_url)
    if target_url not in visited:

        visited.add(target_url)
        #executor.submit(checkPermissions, target_url)
        time.sleep(5)
        checkPermissions(target_url)
    crawlNext()
    if (queue.empty()):
        return


def addSiteToDB(base_url, rp, robotsURL):

    # Dodaj domensko stran v db, če je tam še ni
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM crawldb.site WHERE domain=" + "'" + base_url + "'")
    data = cur.fetchall()
    if not data:

        if rp != "":
            listSite_Maps = rp.site_maps()
            textRobots = urllib.request.urlopen(robotsURL).read().decode("utf-8")
        else:
            listSite_Maps = ""
            textRobots = ""
        cur.execute("INSERT INTO crawldb.site VALUES(DEFAULT,%s, %s, %s) RETURNING id",
            (base_url, textRobots, listSite_Maps))

        id_of_new_site = cur.fetchone()[0]

        cur.close()

    else:
        #Ce je domenska stran ze notri jo najdemo
        cur = conn.cursor()
        cur.execute("SELECT id FROM crawldb.site WHERE domain=" + "'" + base_url + "'")

        id_of_new_site = cur.fetchone()[0]

    return id_of_new_site

def checkPermissions(url):

    #Kreiramo base URL strani
    u = urlparse(url)

    base_url = u.scheme + "://" + u.netloc
    robotsURL = urljoin(base_url, "/robots.txt")

    #Preverimo ali stran ima robots.txt
    r = requests.get(robotsURL)

    if (r.status_code < 400):

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robotsURL)
        rp.read()

        if (rp.can_fetch("*", url)):

            #Robot.txt dovoli crawlanje
            id_of_new_site = addSiteToDB(base_url, rp, robotsURL)
            scraper(url, id_of_new_site)
    else:
        # Robots.txt ne obstaja na strani

        id_of_new_site = addSiteToDB(base_url, "", robotsURL)
        scraper(url, id_of_new_site)
    return

if __name__ == '__main__':

    # Povezava z pgAdmin
    global conn
    conn = psycopg2.connect(host="localhost", user="postgres", password="admin")
    conn.autocommit = True

    #TODO DODAT ŠE DRUGE STRANI

    #Dodaj začetni URL
    seed_url = "http://www.gov.si/"
    #seed_url = "http://evem.gov.si/info/sistem-spot/"
    queue.put(seed_url)
    crawlNext()

    conn.close()
