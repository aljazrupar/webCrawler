import sys
import os
import pathlib
from lxml import html
import json
import re
#TODO pogledat kako bi prkazoval čšž
def xpathOverstock(page):
    titles = page.xpath('/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody//td/a/b/text()')
    contents = page.xpath('/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td[2]/span/text()')

    listPrice = page.xpath('/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/s/text()')
    price = page.xpath('/html/body/table[2]/tbody//tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/span/b/text()')
    savings = page.xpath('/html/body/table[2]/tbody//tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td[1]/table/tbody/tr[3]/td[2]/span/text()')

    for count, i in enumerate(savings):
        dataItem={
            "Article number": str(count),
            "Title": titles[count],
            "Content": contents[count],
            "ListPrice": listPrice[count],
            "Price": price[count],
            "Saving": i.split(" ")[0],
            "SavingPercent": i.split(" ")[1]
        }
        print("Output object:\n%s" % json.dumps(dataItem, indent=7))
def xpathRTV(page):

    title = page.xpath('//h1/text()')
    subtitle = page.xpath('//header/div[2]/text()')
    author = page.xpath('//header/div[3]/div[1]/strong/text()')
    publishedTime = page.xpath('//header/div[3]/div[1]/text()')
    lead = page.xpath('//header/p/text()')
    content = page.xpath('//article/p//text()')
    contentEncoded=""
    for i in content:
        contentEncoded=contentEncoded+i
    dataItem = {
       "Title": title[0],
       "Subtitle": subtitle[0],
       "Author": author[0],
       "Lead": lead[0],
       "PublishedTime": publishedTime[1][2:-6],
       "Content": contentEncoded
    }
    print("Output object:\n%s" % json.dumps(dataItem, indent=6))
def xpathAvto(page):
    name = page.xpath('//*[@id="results"]//div[3]/div[1]/a/span/text()')
    price =page.xpath('//*[@id="results"]//div[4]/div[1]/div[2]/div/text()')
    year =page.xpath('//*[@id="results"]//div[3]/div[1]/ul/li[1]/text()')
    distance =page.xpath('//*[@id="results"]//div[3]/div[1]/ul/li[2]/text()')
    engine =page.xpath('//*[@id="results"]//div[3]/div[1]/ul/li[3]/text()')
    gear =page.xpath('//*[@id="results"]//div[3]/div[1]/ul/li[4]/text()')

    for count, i in enumerate(year):
        dataItem={
            "Car number": str(count),
            "Name": name[count],
            "Price": price[count],
            "Year": year[count][-4:],
            "Distance [km]": distance[count][:-3],
            "Engine": engine[count].split(",")[0],
            "Power": engine[count].split("/")[1],
            "Gear": gear[count]
        }
        print("Output object:\n%s" % json.dumps(dataItem, indent=8))
def xpath(pages):

    for i in pages:
        with open(i, encoding="ISO-8859-1") as file:  # Use file to refer to the file object
            data = file.read()
        tree = html.fromstring(data)

        if("Avto" in i):
            continue
            xpathAvto(tree)
        elif("jewelry" in i):
            continue
            xpathOverstock(tree)
        else:
            xpathRTV(tree)
def regexRTV(pages):

    regex = r"<h1>(.*)</h1>"
    match=re.compile(regex).search(pages)
    title= match.group(1)

    regex = r"<p class=\"lead\">(.*)</p>"
    match = re.compile(regex).search(pages)
    lead = match.group(1)

    regex = r"<div class=\"subtitle\">(.*)</div>"
    match = re.compile(regex).search(pages)
    subtitle = match.group(1)

    regex = r"<div class=\"author-name\">(.*)</div>"
    match = re.compile(regex).search(pages)
    author = match.group(1)

    regex = r"<div class=\"publish-meta\">\s+(.*)<br>"
    match = re.compile(regex).search(pages)
    date = match.group(1)

    #TODO KAJ TUKAJ ŽELI IMET PRI CONTENT
    regex = r"<figure(.*)"
    match = re.compile(regex).search(pages)
    content = match.group(1)

    dataItem = {
       "Title": title,
       "Subtitle": subtitle,
       "Author": author,
       "Lead": lead,
       "PublishedTime": date,
       "Content": content
    }
    print("Output object:\n%s" % json.dumps(dataItem, indent=6))
def regexAvto(pages):

    regex = r"<a class=\"Adlink\"(.*)>\s+<span>(.*)</span>\s+</a>"
    match=re.compile(regex).findall(pages)
    names = []
    for i in match:
        names.append(i[1])

    regex = r"<div class=\"((ResultsAdPriceStaraCena)|(ResultsAdPriceRegular))\">\s*(.*)\s*(.*)\s*</div>"
    match = re.compile(regex).findall(pages)
    prices = []
    for i in match:
        prices.append(i[3][:-7])

    regex = r"<ul>\s*<li>(.*)</li>\s*<li>(.*)</li>\s*<li>(.*)</li>\s*<li>(.*)</li>\s*</ul>"
    match = re.compile(regex).findall(pages)

    for count,i in enumerate(match):

        dataItem={
            "Car number": str(count),
            "Name": names[count],
            "Price": prices[count],
            "Year": i[0][-4:],
            "Distance [km]": i[1][:-3],
            "Engine": i[2].split(",")[0],
            "Power": i[2].split("/")[1],
            "Gear": i[3]
        }
        print("Output object:\n%s" % json.dumps(dataItem, indent=8))
def regexOverstock(pages):

    regex = r"<s>(.*)</s>"
    match=re.compile(regex).findall(pages)
    listPrice = []
    for i in match:
        listPrice.append(i)

    regex = r"<td align=\"left\" nowrap=\"nowrap\">\s*<span class=\"littleorange\">(.*)</span>"
    match = re.compile(regex).findall(pages)
    Saving = []
    SavingPercent=[]

    for i in match:
        SavingPercent.append(i.split(" ")[1])
        Saving.append(i.split(" ")[0])


    regex = r"<b>(.*)</b>\s*</a>\s*<br>"
    match=re.compile(regex).findall(pages)
    Titles = []
    for i in match:
        Titles.append(i)

    regex = r"<span class=\"bigred\">\s*<b>(.*)</b>"
    match = re.compile(regex).findall(pages)
    Price = []
    for i in match:
        Price.append(i)

    regex = r"</td>\s*<td valign=\"top\">\s*<span class=\"normal\">\s*(.*)"

    match = re.compile(regex).findall(pages)
    #TODO POPRAVIT CONTENT
    Content = []
    for i in match:
        Content.append(i)
        print(i)
        print()

    for count, i in enumerate(Titles):
        dataItem={
            "Article number": str(count),
            "Title": Titles[count],
            "Content": Content[count],
            "ListPrice": listPrice[count],
            "Price": Price[count],
            "Saving": Saving[count],
            "SavingPercent": SavingPercent[count]
        }
        print("Output object:\n%s" % json.dumps(dataItem, indent=7))
def regex(pages):
    for i in pages:
        with open(i, encoding="ISO-8859-1") as file:  # Use file to refer to the file object
            data = file.read()
        tree = data

        if("Avto" in i):
            continue
            regexAvto(tree)
        elif("jewelry" in i):
            #continue
            regexOverstock(tree)
        else:
            continue
            regexRTV(tree)
#def auto():

if __name__ == '__main__':
    method = sys.argv[1]

    rootdir = '../WebExtraction/input-extraction'

    parentPath = pathlib.Path().absolute().parent
    path = os.path.join(parentPath, "input-extraction")
    list_subfolders_with_paths = [f.path for f in os.scandir(path) if f.is_dir()]

    paths=[]
    for i in list_subfolders_with_paths:
        for j in os.scandir(i):
            if (not j.is_dir() and os.path.basename(j) != ".DS_Store"):
                paths.append((j.path))

    if(method == "A"):
        regex(paths)
    elif(method == "B"):
        xpath(paths)
    #else:
    #    auto(paths)
