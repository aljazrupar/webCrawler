# Crawley

Crawley is a web crawler designed to crawl Slovenian govermental websites, which include gov.si in the domain. Crawley is designed in a way to gather basic site information in the most 
effective way possible. To achieve that we have used asynchronous page processing. The project also follows the basic rules of ethnics and as such does not DDoS the pages.

## Installation

The project has been developed in Python 3.8.1

To be able to run the project you will first need to install the following Python packages:
argparse
concurrent.futures
datetime
sys
threading
urllib
queue 
urllib
time
psycopg2
requests
fBeautifulSoup

Secondly since we are using pgAdmin 4, you should install the software on your computer locally and create database using template crawldb.sql found in the project folder.
Credentials should be initialised to:
user: postgres
password: admin

To run the project open command prompt on Windows and run (Note: arg1 is the numbe of threads, you wish to open for asynchronous processing):

python */Webcrawler/crawler/crawler.py arg1

Note: The poject has only been tested on Windows 10.