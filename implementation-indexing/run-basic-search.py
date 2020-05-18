import itertools
import os
import sys
from collections import defaultdict
import time
import nltk
from bs4 import BeautifulSoup, Comment
import sqlite3
from nltk import word_tokenize
from nltk.corpus import stopwords
import re

nltk.download('punkt')
nltk.download('stopwords')

stop_words_slovene = set(stopwords.words("slovene")).union(set(
    ["ter", "nov", "novo", "nova", "zato", "še", "zaradi", "a", "ali", "april", "avgust", "b", "bi", "bil", "bila",
     "bile", "bili", "bilo", "biti",
     "blizu", "bo", "bodo", "bojo", "bolj", "bom", "bomo", "boste", "bova", "boš", "brez", "c", "cel", "cela",
     "celi", "celo", "d", "da", "daleč", "dan", "danes", "datum", "december", "deset", "deseta", "deseti", "deseto",
     "devet", "deveta", "deveti", "deveto", "do", "dober", "dobra", "dobri", "dobro", "dokler", "dol", "dolg",
     "dolga", "dolgi", "dovolj", "drug", "druga", "drugi", "drugo", "dva", "dve", "e", "eden", "en", "ena", "ene",
     "eni", "enkrat", "eno", "etc.", "f", "februar", "g", "g.", "ga", "ga.", "gor", "gospa", "gospod", "h", "halo",
     "i", "idr.", "ii", "iii", "in", "iv", "ix", "iz", "j", "januar", "jaz", "je", "ji", "jih", "jim", "jo",
     "julij", "junij", "jutri", "k", "kadarkoli", "kaj", "kajti", "kako", "kakor", "kamor", "kamorkoli", "kar",
     "karkoli", "katerikoli", "kdaj", "kdo", "kdorkoli", "ker", "ki", "kje", "kjer", "kjerkoli", "ko", "koder",
     "koderkoli", "koga", "komu", "kot", "kratek", "kratka", "kratke", "kratki", "l", "lahka", "lahke", "lahki",
     "lahko", "le", "lep", "lepa", "lepe", "lepi", "lepo", "leto", "m", "maj", "majhen", "majhna", "majhni",
     "malce", "malo", "manj", "marec", "me", "med", "medtem", "mene", "mesec", "mi", "midva", "midve", "mnogo",
     "moj", "moja", "moje", "mora", "morajo", "moram", "moramo", "morate", "moraš", "morem", "mu", "n", "na", "nad",
     "naj", "najina", "najino", "najmanj", "naju", "največ", "nam", "narobe", "nas", "nato", "nazaj", "naš", "naša",
     "naše", "ne", "nedavno", "nedelja", "nek", "neka", "nekaj", "nekatere", "nekateri", "nekatero", "nekdo",
     "neke", "nekega", "neki", "nekje", "neko", "nekoga", "nekoč", "ni", "nikamor", "nikdar", "nikjer", "nikoli",
     "nič", "nje", "njega", "njegov", "njegova", "njegovo", "njej", "njemu", "njen", "njena", "njeno", "nji",
     "njih", "njihov", "njihova", "njihovo", "njiju", "njim", "njo", "njun", "njuna", "njuno", "no", "nocoj",
     "november", "npr.", "o", "ob", "oba", "obe", "oboje", "od", "odprt", "odprta", "odprti", "okoli", "oktober",
     "on", "onadva", "one", "oni", "onidve", "osem", "osma", "osmi", "osmo", "oz.", "p", "pa", "pet", "peta",
     "petek", "peti", "peto", "po", "pod", "pogosto", "poleg", "poln", "polna", "polni", "polno", "ponavadi",
     "ponedeljek", "ponovno", "potem", "povsod", "pozdravljen", "pozdravljeni", "prav", "prava", "prave", "pravi",
     "pravo", "prazen", "prazna", "prazno", "prbl.", "precej", "pred", "prej", "preko", "pri", "pribl.",
     "približno", "primer", "pripravljen", "pripravljena", "pripravljeni", "proti", "prva", "prvi", "prvo", "r",
     "ravno", "redko", "res", "reč", "s", "saj", "sam", "sama", "same", "sami", "samo", "se", "sebe", "sebi",
     "sedaj", "sedem", "sedma", "sedmi", "sedmo", "sem", "september", "seveda", "si", "sicer", "skoraj", "skozi",
     "slab", "smo", "so", "sobota", "spet", "sreda", "srednja", "srednji", "sta", "ste", "stran", "stvar", "sva",
     "t", "ta", "tak", "taka", "take", "taki", "tako", "takoj", "tam", "te", "tebe", "tebi", "tega", "težak",
     "težka", "težki", "težko", "ti", "tista", "tiste", "tisti", "tisto", "tj.", "tja", "to", "toda", "torek",
     "tretja", "tretje", "tretji", "tri", "tu", "tudi", "tukaj", "tvoj", "tvoja", "tvoje", "u", "v", "vaju", "vam",
     "vas", "vaš", "vaša", "vaše", "ve", "vedno", "velik", "velika", "veliki", "veliko", "vendar", "ves", "več",
     "vi", "vidva", "vii", "viii", "visok", "visoka", "visoke", "visoki", "vsa", "vsaj", "vsak", "vsaka", "vsakdo",
     "vsake", "vsaki", "vsakomur", "vse", "vsega", "vsi", "vso", "včasih", "včeraj", "x", "z", "za", "zadaj",
     "zadnji", "zakaj", "zaprta", "zaprti", "zaprto", "zdaj", "zelo", "zunaj", "č", "če", "često", "četrta",
     "četrtek", "četrti", "četrto", "čez", "čigav", "š", "šest", "šesta", "šesti", "šesto", "štiri", "ž", "že",
     "svoj", "jesti", "imeti", "\u0161e", "iti", "kak", "www", "km", "eur", "pač", "del", "kljub", "šele", "prek",
     "preko", "znova", "morda", "kateri", "katero", "katera", "ampak", "lahek", "lahka", "lahko", "morati", "torej"]))


def process_text(text):
    return list(word for word in word_tokenize(text.lower()) if word not in stop_words_slovene)


def repair_tree(soup):
    for script in soup.find_all("script"):
        script.decompose()
    for style in soup.find_all("style"):
        style.decompose()
    for comments in soup.findAll(text=lambda text: isinstance(text, Comment)):
        comments.extract()
    for iframe in soup.find_all("iframe"):
        iframe.decompose()
    for link in soup.find_all("link"):
        link.decompose()


def get_hmtl_file_names(input_dir_name):
    for dir_name in os.listdir(input_dir_name):
        dir_path = "%s/%s" % (input_dir_name, dir_name)
        for file in os.listdir(dir_path):
            if file.endswith(".html"):
                yield "%s/%s" % (dir_path, file), file


def get_words_indexes(words):
    indexes = defaultdict(list)

    for i, word in enumerate(words):
        indexes[word].append(i)

    return indexes


def print_result(result, words):
    first = True

    for doc in result:

        if first == True:
            dash = '-' * 50
            print(dash)
            print('{:<8s}{:<30s}{:<100s}'.format("Frequency", "Documents", "Snippet"))
            print(dash)
            first = False
        else:
            soup = BeautifulSoup(open(doc[0], encoding="utf-8"), "html.parser")
            repair_tree(soup)

            tokens = []

            for text in soup.findAll(text=True):

                for x in words:

                    if x in process_text(text):

                        if len(tokens) < 140:
                            if (len(tokens) != 0):
                                tokens += [" ... "]
                            if (len(text) > 50):
                                splitText = re.split(x, text.replace("\n", ""), flags=re.IGNORECASE)
                                textLeft = splitText[0].split(" ")
                                textRight = splitText[1].split(" ")
                                tokens += " ".join(textLeft[-3:]) + x + " ".join(textRight[:3])

                            else:
                                tokens += text.replace("\n", "")

            if (len(tokens) > 0):
                print('{:<8s}{:<30s}{:<100s}'.format(str(doc[1]), doc[0].split("/")[-1],
                                                     "".join(tokens).replace("\t", "")))


def query(indexes):
    result = []

    for (file, i) in indexes.items():
        result.append((file, len(i), i))

    result.sort(key=lambda file: file[1], reverse=True)

    return result

#------------------MAIN----------------------

a=time.perf_counter()

argInput = input("Query: ")

process_text(argInput)

result = defaultdict(list)

INPUT_DIR = "../input-index"

for (path, filename) in get_hmtl_file_names(INPUT_DIR):
    soup = BeautifulSoup(open(path, encoding="utf-8"), "html.parser").find_all("body")[0]
    repair_tree(soup)
    tokens = []
    for text in soup.findAll(text=True):
        tokens += process_text(text)

    for (word, indexes) in get_words_indexes(tokens).items():
        if word in argInput:
            result[path] += indexes

b=time.perf_counter()
timeUsed=b-a

print("\tResults for a query: " + argInput + "\n")
print("\tResults found in " + str(timeUsed) + "s.\n")

print_result(query(result), process_text(argInput))
