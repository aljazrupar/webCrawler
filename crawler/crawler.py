import argparse
import concurrent.futures
import datetime
import hashlib
import socket
import ssl
import sys
import threading
import urllib
from multiprocessing.context import Process
from multiprocessing import Queue as MultiProcessingQueue
from os import path
from queue import Queue, Empty
from urllib.request import urlparse, urljoin
import urllib.robotparser
import time
import psycopg2
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import ssl
import hashlib

"""
GENERAL TODOs:

1.Narest lockse in threading
2.Poročilo naspisat
3.Za linke najdt onclick javascript (neki že narjeno v get_Javascript_onclick funkciji)
4. Testirat kodo če vse dela in morda kj zoptimizirat, če dela prepočas

"""

num_workers = int(sys.argv[1])


WEB_DRIVER_LOCATION = "/Users/Administrator/Documents/FAX/2.Letnik MAG/WIER/chromedriver"
TIMEOUT = 5
queue = Queue()
visited = set([])
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
schemes = ["", "www", "http", "https"]
lock            = threading.Lock()
worker_ip_lock  = threading.Lock()
visitedPages = set()
workers = []
ips = {}

class Worker:
    def __init__(self, index):
        self.index = index
        self.currentIp = ""
        self.queue = MultiProcessingQueue()

        self.p = threading.Thread(target=crawlNext, args=(self,))
        self.p.start()

    def join(self):
        self.p.join()

    def set_current_ip(self, ip):
        with(worker_ip_lock):
            self.currentIp = ip

    def get_current_ip(self):
        with(worker_ip_lock):
            return self.currentIp

    def __str__(self):
        "[{}] {}".format(self.index, self.currentIp)

#TA ZADEVA ŠE NE DELA ČISTO, KER VRNE NEK ID NAMEST URL-JA.. MORDA JE TREBA NAREDIT DRUGAČE
#--------------------------------------------
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

def get_Javascript_Onclick(url):

    #TO ŠE NE DELA
    """"
    urls = set()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=fri-ieps-CrawlingStones")
    driver = webdriver.Chrome(WEB_DRIVER_LOCATION, options=chrome_options)
    driver.get(url)
    time.sleep(TIMEOUT)
    html = driver.page_source
    ch = driver.find_elements_by_xpath("//*[(@onclick)]")
    #TODO treba nekak dobit link kle???

    driver.close()
    """
    #for curr_url in urls:
    #    queue.put(curr_url)

#----------------------------------------

#TA FUNKCIJA GRE PO ENI SPLETNI STRANI IN IŠČE URLJE IN SLIKE
def get_all_website_links(url,id_of_new_page, crawlDelay): # najde vse linke na enem URL

    urls = set()
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    time.sleep(crawlDelay)

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue

        # zdruzi url z domeno ce ni ze cel link.
        href = urljoin(url, href)
        parsed_href = urlparse(href)

        # sparsa link
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        #Preveri če je .gov.si
        if("gov.si" in href):
            urls.add(href)

    #TODO
    get_Javascript_Onclick(url)

    #Najde vse like na strani in jih shrani v bazo image
    img_tags = soup.find_all('img')

    ImgUrls = [img['src'] for img in img_tags]
    with lock:
        cur = conn.cursor()
        for imgUrl in ImgUrls:

            # zdruzi url z domeno ce ni ze cel link.
            imgCleanUrl = urljoin(url, imgUrl)
            parsed_img = urlparse(imgCleanUrl)

            # sparsa link
            imgCleanUrl = parsed_img.scheme + "://" + parsed_img.netloc + parsed_img.path
            filename = imgCleanUrl.split("/")[-1]
            content_type = filename.split(".")[-1]

            if parsed_img.scheme in schemes:
                response = requests.get(imgCleanUrl)
                time.sleep(crawlDelay)
                cur.execute("INSERT INTO crawldb.image VALUES(DEFAULT,%s, %s, %s,%s ,CURRENT_TIMESTAMP)",
                    (id_of_new_page, filename, content_type, "BINARY"))
        cur.close()

    return urls


def scraper(url, id_of_new_site, crawlDelay):  # Funkcija za obdelovanje ene strani in dodajenje linkov v queue

    #Dobimo spletno stran
    response = requests.get(url)

    status_code = response.status_code
    html_content = response.text
    time.sleep(crawlDelay)

    cur = conn.cursor()

    #Preverjamo ali je HTML, Binary ali duplikat
    if 'html' in response.headers['content-type']:
        with lock:
            cur.execute("SELECT id FROM crawldb.page WHERE url=" + "'" + url + "'")
            data = cur.fetchone()
            if not data:

                cur.execute("SELECT hash, id FROM crawldb.page")
                hashesUrls = cur.fetchall()

                if not hashesUrls:
                    hashes = []
                else:
                    hashes = [x[0] for x in hashesUrls]
                    ids = [y[1] for y in hashesUrls]

                hash = hashlib.md5(html_content.encode()).hexdigest()

                if hash in hashes:
                    #Če je duplikat:
                    cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT,%s, %s, %s,%s ,%s ,%s ,CURRENT_TIMESTAMP ) RETURNING id",
                            (id_of_new_site, "DUPLICATE", url, "NULL",  status_code, hash))
                    id_of_new_page = cur.fetchone()[0]

                    cur.execute("INSERT INTO crawldb.link VALUES(%s, %s)",
                        (id_of_new_site, ids[hashes.index(hash)]))

                else:
                    #Če je originalna stran
                    cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT,%s, %s, %s,%s ,%s ,%s ,CURRENT_TIMESTAMP ) RETURNING id",
                        (id_of_new_site, "HTML", url, html_content, status_code, hash))
                    id_of_new_page = cur.fetchone()[0]
            else:
                id_of_new_page = data[0]

    else:
        with lock:
            #Če je Binary naprimer slika, pdf,...
            cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, %s, %s, %s, ,CURRENT_TIMESTAMP ) RETURNING id",
                            (id_of_new_site, 'BINARY', url, "NULL",  status_code, "NULL" ))
            id_of_new_page = cur.fetchone()[0]
            # response = requests.get(url)
            # time.sleep(crawlDelay)
            cur.execute("INSERT INTO crawldb.page_data VALUES(DEFAULT,%s, %s,%s ,%s )",
                        (id_of_new_page,  response.headers['content-type'], "BINARY"))

            cur.close()
    #Dodamo linke
    urls = get_all_website_links(url, id_of_new_page, crawlDelay)
    for curr_url in urls:
        queue.put(curr_url)
    '''
    if(not queue.empty()):
        crawlNext()
    else:
        return
    '''

def get_next_url(my_worker):
    while True:
        with(lock):
            # for worker in workers
            if not my_worker.queue.empty():
                return my_worker.queue.get()
            else:
                my_worker.currentIp = ""
                while not queue.empty():
                    target_url = queue.get(block=True)
                    domain = urlparse(target_url).netloc

                    if domain in ips:
                        ip = ips[domain]
                    else:
                        ip = socket.gethostbyname(domain)
                        ips[domain] = ip

                    print("{} -> {}".format(domain, ip))
                    for worker in workers:
                        if worker.currentIp == ip:
                            worker.queue.put(target_url)
                            break
                    else:
                        return target_url
        time.sleep(5)
        for worker in workers:
            if not worker.currentIp == "":
                break
        else:
            return ""

def crawlNext(my_worker):
    target_url = get_next_url(my_worker)
    if target_url == "":
        return

    print(target_url)
    if target_url not in visited:

        visited.add(target_url)
        #TODO:
        #executor.submit(checkPermissions, target_url)

        checkPermissions(target_url)
    crawlNext(my_worker)
    if (queue.empty()):
        return


def addSiteToDB(base_url, rp, robotsURL):
    #Funkcija doda novo domeno v bazo
    with lock:
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
            #Ce je domenska stran ze notri jo najdemo in vrnemo index
            cur = conn.cursor()
            cur.execute("SELECT id FROM crawldb.site WHERE domain=" + "'" + base_url + "'")

            id_of_new_site = cur.fetchone()[0]

    return id_of_new_site

def checkPermissions(url):
    #Funkcija preveri kaj piše v robot.txt in to upošteva

    #Kreiramo base URL strani
    u = urlparse(url)

    base_url = u.scheme + "://" + u.netloc
    robotsURL = urljoin(base_url, "/robots.txt")

    #Preverimo ali stran ima robots.txt
    r = requests.get(robotsURL)
    time.sleep(5)
    if (r.status_code < 400):

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robotsURL)
        rp.read()

        #Definiramo delay za requesti (da ga ne ddosamo) - TODO bo treba narest še pr threadingu...
        if(rp.crawl_delay("*") == None):

            delay = 5
        else:
            if(rp.crawl_delay("*") > 5):
                delay = rp.crawl_delay("*")
            else:
                delay = 5

        if (rp.can_fetch("*", url)):

            #Robot.txt dovoli crawlanje
            id_of_new_site = addSiteToDB(base_url, rp, robotsURL)
            scraper(url, id_of_new_site, delay)
    else:
        # Robots.txt ne obstaja na strani

        id_of_new_site = addSiteToDB(base_url, "", robotsURL)
        scraper(url, id_of_new_site, 0)
    return

if __name__ == '__main__':

    # Povezava z pgAdmin
    global conn
    conn = psycopg2.connect(host="localhost", user="postgres", password="admin")
    conn.autocommit = True

    #Dodaj seed URLje
    seed_urls = ["http://gov.si", "http://evem.gov.si", "http://e-uprava.gov.si", "http://e-prostor.gov.si"]

    for seed in seed_urls:
        queue.put(seed)
    # crawlNext()
    for i in range(num_workers):
        workers += [Worker(i)]

    for worker in workers:
        worker.join()

    conn.close()
