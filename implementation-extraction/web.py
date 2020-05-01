from bs4 import BeautifulSoup, Comment
import bs4
import os.path


class Object:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value  # pride v postev pri text
        self.children = list()
        self.optional = False
        self.repeating = False
        # self.deleted = False

    def is_equal(self, other):
        if other is None:
            return False
        if self.tag == other.tag:
            if self.tag == "text":
                if self.value == self.value:
                    return True
                else:
                    return False
            else:
                return True
        return False

    def repair_repetitions(self, newObject):
        if not newObject == None:
            for i in range(len(self.children) - 1, -1, -1):
                child = self.children[i]
                if not child.repeating:
                    if child.is_equal(newObject):
                        child.repeating = True
                    else:
                        break

def check_repeating(children):
    repeating_tags = list()
    for child in children:
        if child.repeating:
            repeating_tags.append(child.tag)
    return repeating_tags



def print_wrapper1(wrapper, f, depth=0):
    special = wrapper.repeating or wrapper.optional
    child_tag_cnt = 0
    repeating = False

    children = []

    for child in wrapper.children:
        if child.tag == "text":
            children.append(child.value)
        else:
            if not repeating:
                children.append(child)
            child_tag_cnt += 1
            repeating = child.repeating

    do_new_line = child_tag_cnt > 1
    indent = "\t" * (depth - 1) if child_tag_cnt > 1 else ""

    f.write("%s<%s>" % ("(" if special else "", wrapper.tag))
    for child in children:
        if type(child) is bs4.NavigableString or type(child) is str:
            f.write(child)
        else:
            if do_new_line:
                f.write("\n")
                f.write(indent + "\t")
            print_wrapper1(child, f, depth + 1 if do_new_line else depth)
    f.write("%s</%s>" % ("\n" + indent if child_tag_cnt > 1 else "", wrapper.tag))

    if wrapper.repeating and wrapper.optional:
        f.write(")*")
    elif wrapper.optional:
        f.write(")?")
    elif wrapper.repeating:
        f.write(")+")


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
        elif type(el) is bs4.NavigableString and not el.string.isspace():
            newObject = Object("text", "#Text")
            curr_object.children.append(newObject)


def add_rest_of_el(el1, el2, wrapper):
    for i in range(len(el2.contents) - 1, len(el1.contents)):
        curr_element = el1.contents[i]
        newObject = Object(curr_element.name, None)
        wrapper.children.append(newObject)
        add_all_contents(curr_element, newObject)


def add_new_element(element, wrapper, optional, repeating):
    newObject = None
    if type(element) is bs4.NavigableString and not element.string.isspace():
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
    return newObject


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

            if not element1.string.isspace() or not element2.string.isspace():
                newObject = Object("text", None)
                if element1.string == element2.string:
                    newObject.value = element1.string
                else:
                    # print("#text1 = ", element1.string, "#text2 = ", element2.string)
                    newObject.value = "#Text"
                wrapper.children.append(newObject)

            count1 += 1
            count2 += 1
        # tag and same
        elif type(element1) is bs4.Tag and type(element2) is bs4.Tag and element1.name == element2.name:
            newObject = Object(element1.name, None)
            wrapper.children.append(newObject)
            if len(element1.contents) > 0 and len(element2.contents) > 0:
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
                newObject = add_new_element(el1.contents[i], wrapper, False, True)
                wrapper.repair_repetitions(newObject)

    elif len(el2.contents) > count2:
        for i in range(count2, len(el2.contents)):
            match = find_next(el2.contents[i], el1, 0)
            if match == -1:
                add_new_element(el2.contents[i], wrapper, True, False)
            else:
                newObject = add_new_element(el2.contents[i], wrapper, False, True)
                wrapper.repair_repetitions(newObject)


def main():
    f1_j = open("../input-extraction/overstock.com/jewelry01.html", 'r')
    f2_j = open("../input-extraction/overstock.com/jewelry02.html", 'r')

    f1_r = open("../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html",
                'r')
    f2_r = open("../input-extraction/rtvslo.si/Volvo.html", 'r')

    f1_a = open("../input-extraction/avto.net/www.Avto.net.html", 'r')
    f2_a = open("../input-extraction/avto.net/www.Avto.net_ 2.html", 'r')

    soup1_j = BeautifulSoup(f1_j.read(), features="lxml")
    soup2_j = BeautifulSoup(f2_j.read(), features="lxml")
    repair_tree(soup1_j)
    repair_tree(soup2_j)
    wrapper_j = Object("Wrapper", "start")
    search(soup1_j, soup2_j, wrapper_j)
    f3_j = open("wrapperOut_jewlery.txt", "w")
    print_wrapper1(wrapper_j, f3_j)

    soup1_r = BeautifulSoup(f1_r.read(), features="lxml")
    soup2_r = BeautifulSoup(f2_r.read(), features="lxml")
    repair_tree(soup1_r)
    repair_tree(soup2_r)
    wrapper_r = Object("Wrapper", "start")
    search(soup1_r, soup2_r, wrapper_r)
    f3_r = open("wrapperOut_rtv.txt", "w")
    print_wrapper1(wrapper_r, f3_r)

    soup1_a = BeautifulSoup(f1_a.read(), features="lxml")
    soup2_a = BeautifulSoup(f2_a.read(), features="lxml")
    repair_tree(soup1_a)
    repair_tree(soup2_a)
    wrapper_a = Object("Wrapper", "start")
    search(soup1_a, soup2_a, wrapper_a)
    f3_a = open("wrapperOut_AvtoNet.txt", "w")
    print_wrapper1(wrapper_a, f3_a)


if __name__ == '__main__': main()
