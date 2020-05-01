from bs4 import BeautifulSoup, Comment
import bs4


class Object:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value # pride v postev pri text
        self.children = list()
        self.optional = False
        self.repeating = False
        # self.deleted = False

# def compare_object(object1, object2):
#     if object1.tag == "text" and object2.tag == "text":
#         if object1.value == object2.value:
#             return True
#         else:
#             return False
#
#     elif object1.tag == object2.tag:
#         if len(object1.children) == len(object2.children):
#             for ch1, ch2 in zip(object1.children, object2.children):
#                 if not compare_object(ch1, ch2):
#                     return False
#             return True
#         else:
#             return False
#     else:
#         return False

# def square_matching(wrapper):
#     if len(wrapper.children) > 1:
#         # print(wrapper.children)
#         for i in range(1, len(wrapper.children)):
#             if compare_object(wrapper.children[0], wrapper.children[i]):
#                 wrapper.children[0].repeating = True
#                 wrapper.children[i].deleted = True
#             else:
#                 square_matching(wrapper.children[i])
#     elif len(wrapper.children) == 1:
#         square_matching(wrapper.children[0])
#     else:
#         return
#
#
# def check_repeating(children):
#     repeating_tags = list()
#     for child in children:
#         if child.repeating:
#             repeating_tags.append(child.tag)
#     return repeating_tags
#
#
# def print_children(children, f):
#     already_printed = list()
#     if len(children) > 0:
#         repeating_tags = check_repeating(children)
#         for child in children:
#             if child.tag in repeating_tags and child.tag not in already_printed:
#                 already_printed.append(child.tag)
#                 f.write("( " + "\n")
#                 print_wrapper1(child, f)
#                 f.write(")+" + "\n")
#             elif child.tag not in repeating_tags:
#                 print_wrapper1(child, f)
#
#
# def print_wrapper1(wrapper, f):
#     if wrapper.tag == "text":
#         f.write(wrapper.value + "\n")
#     else:
#         already_printed = list()
#         if len(wrapper.children) > 0:
#             repeating_tags = check_repeating(wrapper.children)
#             for child in wrapper.children:
#                 if child.tag in repeating_tags and child.tag not in already_printed:
#                     already_printed.append(child.tag)
#                     f.write("( " + "\n")
#                     print_wrapper1(child, f)
#                     f.write(")+" + "\n")
#                 elif child.tag not in repeating_tags:
#                     print_wrapper1(child, f)
#         elif wrapper.optional:
#             f.write("( <" + wrapper.tag + ">" + "\n")
#             for child in wrapper.children:
#                 print_wrapper1(child, f)
#             f.write("</" + wrapper.tag + "> )?" + "\n")
#         else:
#             f.write("<" + wrapper.tag + ">" + "\n")
#             for child in wrapper.children:
#                 print_wrapper1(child, f)
#             f.write("</" + wrapper.tag + ">" + "\n")


def print_wrapper(wrapper):
    print("tag-> ", wrapper.tag, ", Value-> ", wrapper.value, " rep->", wrapper.repeating)
    if len(wrapper.children) > 0:
        for el in wrapper.children:
            print_wrapper(el)


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

    for el in soup.recursiveChildGenerator():
        if type(el) is bs4.element.Tag:
            el.attrs = {}


def add_all_contents(element, curr_object):  # add all contents of an element
    for el in element.contents:
        if type(el) is bs4.Tag:
            newObject = Object(el.name, None)
            curr_object.children.append(newObject)
            if len(el.contents) > 0:
                newObject.value = "Contents"
                add_all_contents(el, newObject)
        elif type(el) is bs4.NavigableString:
            newObject = Object("text", "#Text")
            curr_object.children.append(newObject)
        else:
            print("Error--> different type")


def add_rest_of_el(el1, el2, wrapper):
    for i in range(len(el2.contents) - 1, len(el1.contents)):
        curr_element = el1.contents[i]
        newObject = Object(curr_element.name, None)
        wrapper.children.append(newObject)
        add_all_contents(curr_element, newObject)


def add_new_element(element, wrapper, optional, repeating):
    if type(element) is bs4.NavigableString:
        newObject = Object("text", None)
        newObject.value = "#Text"
        newObject.optional = optional
        newObject.repeating = repeating
        wrapper.children.append(newObject)
    elif type(element) is bs4.Tag:
        newObject = Object(element.name, None)
        newObject.optional = optional
        newObject.repeating = repeating
        wrapper.children.append(newObject)
        add_all_contents(element, newObject)


def find_next(element1, el2, count2):
    for index2 in range(count2, len(el2.contents)):
        element2 = el2.contents[index2]
        if type(element1) is bs4.NavigableString and type(element2) is bs4.NavigableString:
            if element1.string == element2.string:
                return index2
        if type(element1) is bs4.Tag and type(element2) is bs4.Tag:
            if element1.name == element2.name:
                return index2
    return -1


def search(el1, el2, wrapper):
    count1 = 0
    count2 = 0
    while count1 < len(el1.contents) and count2 < len(el2.contents):
        element1 = el1.contents[count1]
        element2 = el2.contents[count2]
        # print("count1 -> ", count1, " count 2 -> ", count2)

        # elements are just texts
        if type(element1) is bs4.NavigableString and type(element2) is bs4.NavigableString:
            if str(element1.string) == '\n' and str(element2.string) == '\n':
                count1 += 1
                count2 += 1
                continue
            if str(element1.string) == '\n':
                count1 += 1
                continue
            if str(element2.string) == '\n':
                count2 += 1
                continue

            newObject = Object("text", None)
            if element1.string == element2.string:
                newObject.value = element1.string
                # print("Same string--> ", element1.string)
            else:
                print("#text1 = ", element1.string, "#text2 = ", element2.string)
                newObject.value = "#Text"
                # print("bumbem -----------------> ", element1.string)
                # print("#Text", element1.string)
            wrapper.children.append(newObject)

            count1 += 1
            count2 += 1
        # tag and same
        elif type(element1) is bs4.Tag and type(element2) is bs4.Tag and element1.name == element2.name:
            newObject = Object(element1.name, None)
            wrapper.children.append(newObject)
            if len(element1.contents) > 0 and len(element2.contents) > 0:
                # print(element1.contents)
                # print("resursive, both len > 0")
                search(element1, element2, newObject)
            elif len(element1.contents) != 0 and len(element2.contents) == 0:
                newObject.value = "#Contents"
                add_all_contents(element1, newObject)
            elif len(element1.contents) == 0 and len(element2.contents) != 0:
                newObject.value = "#Contents"
                add_all_contents(element2, newObject)

            count1 += 1
            count2 += 1

        # miss match
        else:
            match_element1 = find_next(element1, el2, count2)  # index on el2 match
            match_element2 = find_next(element2, el1, count1)  # index on el1 match
            if match_element1 == -1:
                add_new_element(element1, wrapper, True, False)
                count1 += 1
            if match_element2 == -1:
                add_new_element(element2, wrapper, True, False)
                count2 += 1

            if match_element1 != -1 and match_element2 != -1:
                skipped_count_1 = match_element2 - count1  # count skipped na el1
                skipped_count_2 = match_element1 - count2  # count skipped na el2

                # recursive with the least skipped count

                if skipped_count_1 < skipped_count_2:
                    # add all skipped elements as optional.
                    for i in range(count1, match_element2):
                        add_new_element(el1.contents[i], wrapper, True, False)
                    count1 = match_element2
                else:
                    for i in range(count2, match_element1):
                        add_new_element(el2.contents[i], wrapper, True, False)
                    count2 = match_element1

    # add the rest
    # check if iterator
    # if yes mark as repeating
    # if not add new optional
    if len(el1.contents) > count1:
        for i in range(count1, len(el1.contents)):
            match = find_next(el1.contents[i], el2, 0)
            if match == -1:
                add_new_element(el1.contents[i], wrapper, True, False)
            else:
                add_new_element(el1.contents[i], wrapper, False, True)

    elif len(el2.contents) > count2:
        for i in range(count2, len(el2.contents)):
            match = find_next(el2.contents[i], el1, 0)
            if match == -1:
                add_new_element(el2.contents[i], wrapper, True, False)
            else:
                add_new_element(el2.contents[i], wrapper, False, True)


def main():
    # f1 = open("jewelry01.html", 'r')
    # f2 = open("jewelry02.html", 'r')
    # f1 = open("Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html", 'r')
    # f2 = open("Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html", 'r')
    f1 = open("test1.html", 'r')
    f2 = open("test2.html", 'r')
    soup1 = BeautifulSoup(f1.read(), features="lxml")
    soup2 = BeautifulSoup(f2.read(), features="lxml")
    repair_tree(soup1)
    #print(soup1)
    repair_tree(soup2)
    wrapper = Object("Wrapper", "start")
    search(soup1, soup2, wrapper)
    #square_matching(wrapper)

    f3 = open("wrapperOut.txt", "w")
    #print_wrapper1(wrapper, f3)
    print(print_wrapper(wrapper))
    #TODO -> Ce sta 2 elementa ista na istem nivoju(childrens) oznaci kot repeating in izpisi samo enega.
    # ((< ...> ) ? pomeni opcijski element
    # (<....> ) + pomeni repeating element
    # #Text pomeni isti element v obeh html z razlicnim textom.
    # text: object.tag = "text", object.value = #Text, ce razlicna. in npr Abraham ce isti string.
    # tag: object.tag = neki druzga kot text. object.childrens = njegovi sinovi.

if __name__ == '__main__': main()
