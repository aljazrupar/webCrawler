import concurrent.futures
import hashlib
import re
import socket
import ssl
import sys
import threading
import time
import urllib
import urllib.robotparser
from multiprocessing import Queue as MultiProcessingQueue
from queue import Queue
from urllib.request import urlparse, urljoin

import psycopg2
import requests
from bs4 import BeautifulSoup
# from .worker import Worker

num_workers = int(sys.argv[1])

TIMEOUT = 5
queue = Queue()
visited = set([])
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
schemes = ["", "www", "http", "https"]
lock            = threading.Lock()
worker_ip_lock  = threading.Lock()
visitedPages = set()
workers = []
domains = {}
stop_and_save = False

class Worker:
    def __init__(self, index):
        self.index = index
        self.currentIp = ""
        self.queue = MultiProcessingQueue()

        self.p = threading.Thread(target=crawl, args=(self,))
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

class Domain:
    def __init__(self, ip, crawl_delay):
        self.ip = ip
        self.last_access = 0
        self.crawl_delay = max(crawl_delay, TIMEOUT)

    def wait(self):
        while self.last_access + TIMEOUT > time.time():
            time.sleep(self.crawl_delay)
        self.last_access = time.time()

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

def get_Javascript_Onclick(soup):

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
    urls = []

    for elm_with_onclick in soup.find_all(attrs={"onclick": True}):
        for url in re.findall('document\s*\.\s*location=\s*[\'"](.*)[\'"]', elm_with_onclick["onclick"]):
            urls += [url]
    return urls

#----------------------------------------

def get_domain(url):
    domain = urlparse(url).netloc
    if domain in domains:
        return domains[domain]
    else:
        print("Pridobivanje IP-ja za {}...".format(domain))
        ip = socket.gethostbyname(domain)
        domain_obj = Domain(ip, TIMEOUT)
        domains[domain] = domain_obj
        return domain_obj


#TA FUNKCIJA GRE PO ENI SPLETNI STRANI IN IŠČE URLJE IN SLIKE
def get_all_website_links(url,id_of_new_page, crawlDelay, response): # najde vse linke na enem URL
    urls = set()

    soup = BeautifulSoup(response.content, "html.parser")

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

    for url in get_Javascript_Onclick(soup):
        urls.add(url)

    #Najde vse like na strani in jih shrani v bazo image
    img_tags = soup.find_all('img')

    ImgUrls = [img['src'] for img in img_tags]

    for imgUrl in ImgUrls:
        # zdruzi url z domeno ce ni ze cel link.
        imgCleanUrl = urljoin(url, imgUrl)
        parsed_img = urlparse(imgCleanUrl)

        # sparsa link
        imgCleanUrl = parsed_img.scheme + "://" + parsed_img.netloc + parsed_img.path
        filename = imgCleanUrl.split("/")[-1]
        content_type = filename.split(".")[-1]

        if parsed_img.scheme in schemes:
            save_image(id_of_new_page, filename, content_type)

    return urls


def save_image(id_of_new_page, filename, content_type):
    with lock:
        cur = conn.cursor()
        cur.execute("INSERT INTO crawldb.image VALUES(DEFAULT,%s, %s, %s,%s ,CURRENT_TIMESTAMP)",
                    (id_of_new_page, filename, content_type, "BINARY"))
        cur.close()


def wait_for_access_to_url(url):
    with lock:
        get_domain(url).wait()


def scraper(url, id_of_new_site, crawlDelay):  # Funkcija za obdelovanje ene strani in dodajenje linkov v queue
    wait_for_access_to_url(url)

    #Dobimo spletno stran
    response = requests.get(url)

    status_code = response.status_code
    html_content = response.text
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
            cur.execute("SELECT id FROM crawldb.page WHERE url=" + "'" + url + "'")
            data = cur.fetchone()
            if not data:
                #Če je Binary naprimer slika, pdf,...
                cur.execute("INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP ) RETURNING id",
                                (id_of_new_site, 'BINARY', url, "NULL",  status_code, "NULL" ))
                id_of_new_page = cur.fetchone()[0]

                content_type = response.headers['content-type']

                cur.execute("SELECT 1 FROM crawldb.data_type WHERE code =" + "'" + content_type + "'")
                data = cur.fetchall()
                if not data:
                    cur.execute("INSERT INTO crawldb.data_type VALUES(%s)",
                                (content_type, ))

                cur.execute("INSERT INTO crawldb.page_data VALUES(DEFAULT, %s, %s, %s)",
                            (id_of_new_page, content_type, "BINARY"))
            else:
                id_of_new_page = data[0]
            cur.close()
    #Dodamo linke
    urls = get_all_website_links(url, id_of_new_page, crawlDelay, response)
    for curr_url in urls:
        enqueue(curr_url)
    '''
    if(not queue.empty()):
        crawlNext()
    else:
        return
    '''

def enqueue(url):
    try:
        with lock:
            queue.put(url)
            cur = conn.cursor()
            cur.execute("INSERT INTO crawldb.queue VALUES(%s)", (url,))
            cur.close()
    except:
        pass


def dequeue():
    url = queue.get()
    cur = conn.cursor()
    cur.execute("DELETE FROM crawldb.queue WHERE url=%s;", (url,))
    cur.close()

    return url

def add_to_visited(url):
    try:
        with lock:
            visited.add(url)
            cur = conn.cursor()
            cur.execute("INSERT INTO crawldb.visited VALUES(%s)", (url,))
            cur.close()
    except:
        pass

def get_next_url(my_worker):
    while not stop_and_save:
        with(lock):
            my_worker.currentIp = ""
            if not queue.empty():
                return dequeue()
            for worker in workers:
                if not worker.currentIp == "":
                    break
            else:
                return ""
    return ""

def crawl(my_worker):
    target_url = get_next_url(my_worker)
    while not target_url == "":
        print(target_url)
        if target_url not in visited:
            try:
                checkPermissions(target_url)
                add_to_visited(target_url)
            except:
                print("Prišlo je do napake. Strani {} ni bilo mogoče obdelati".format(target_url))

        target_url = get_next_url(my_worker)

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

    if robotsURL == "/robots.txt":
        return

    #Preverimo ali stran ima robots.txt
    wait_for_access_to_url(robotsURL)
    r = requests.get(robotsURL)
    time.sleep(TIMEOUT)
    if (r.status_code < 400):

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robotsURL)
        rp.read()

        #Definiramo delay za requesti (da ga ne ddosamo) - TODO bo treba narest še pr threadingu...
        if(rp.crawl_delay("*") == None):

            delay = TIMEOUT
        else:
            get_domain(url).crawl_delay = max(int(rp.crawl_delay("*")), TIMEOUT)

        if (rp.can_fetch("*", url)):

            #Robot.txt dovoli crawlanje
            id_of_new_site = addSiteToDB(base_url, rp, robotsURL)
            scraper(url, id_of_new_site, delay)
    else:
        # Robots.txt ne obstaja na strani

        id_of_new_site = addSiteToDB(base_url, "", robotsURL)
        scraper(url, id_of_new_site, TIMEOUT)
    return

def listen_to_keyboard():
    while True:
        if input() == ":q":
            print("Ustavljanje in shranjevanje...")
            global stop_and_save
            stop_and_save = True
            break

def load_last_state():
    cur = conn.cursor()
    cur.execute("SELECT * FROM crawldb.queue")
    urls = cur.fetchall()
    cur.close()
    for (url,) in urls:
        queue.put(url)

    cur = conn.cursor()
    cur.execute("SELECT * FROM crawldb.visited")
    urls = cur.fetchall()
    cur.close()
    global visited
    visited = set(map(lambda x: x[0], urls))

if __name__ == '__main__':
    # Povezava z pgAdmin
    global conn
    conn = psycopg2.connect(host="localhost", user="postgres", password="admin")
    conn.autocommit = True

    load_last_state()

    if queue.empty():
        #Dodaj seed URLje
        seed_urls = ["http://gov.si", "http://evem.gov.si", "http://e-uprava.gov.si", "http://e-prostor.gov.si"]

        for seed in seed_urls:
            enqueue(seed)

    for i in range(num_workers):
        workers += [Worker(i)]

    threading.Thread(target=listen_to_keyboard).start()

    for worker in workers:
        worker.join()

    conn.close()