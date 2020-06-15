import json
import collections
import re
from pprint import pprint

# with open("testdata.edf", 'r') as f:
with open('example.edf', 'r') as f:
    data = f.read()


class Node:

    def __init__(self, x, parent=None):

        self.parent = parent
        self.value = x
        self.children = []

    def __str__(self, level=0):

        result_list = self.treeDiagramBuilder()
        reverse = result_list[::-1]
        output_str = ''
        protect_index = []

        for line in reverse:

            # 生成修正後的 line
            newline = ''
            for i, c in enumerate(line):
                if (i in protect_index):
                    newline += c
                    if c != '|':
                        protect_index.remove(i)
                else:
                    if c == '|':
                        newline += ' '
                    else:
                        newline += c

            output_str = newline+'\n'+output_str

            # update protect index
            # 與 └ 同一欄的 |，不用替換
            for i, c in enumerate(line):
                if c == '└':
                    protect_index.append(i)

        return output_str

    def treeDiagramBuilder(self, level=0):
        sibling = '|   '
        space = '    '
        result_list = [sibling * (level-1 if level > 1 else 0) +
                       '└───' * (1 if level > 0 else 0) +
                       self.value]
        for i, child in enumerate(self.children):
            line_list = child.treeDiagramBuilder(level + 1)
            result_list += line_list

        return result_list

    def appendAndReturn(self, child):
        """
        append a child, return child to move head

        新增兩個同級的方式： 
        pointer.appendAndReturn(newnode1) #會傳回 child，不要接
        pointer.appendAndReturn(newnode2)
        -> 此時指向 newnode2, newnode1, 2 同級 

        依序新增兩個不同及級：
        pointer = pointer.appendAndReturn(newnode1)
        pointer = pointer.appendAndReturn(newnode2)        
        -> 此時指向 newnode2, newnode2, 是 newnode1 的兒子
        """
        self.children.append(child)
        return child


def testTree():

    w = '''outline, group discussion, handout, research, Proofreading, experiment, written work, report writing, experience, reference, textbook, student advisor, teamwork, module, topic, dictionary, laptop, printer, assessment, library, department, computer centre, classroom, attendance, deadline, give a talk, speech, lecture, tutor, main hall, computer laboratory, certificate, diploma, placement test, facilities, college, dining room, specialist, knowledge, international, accommodation, overseas students, full-time, homestay, primary, secondary, intermediate, media room, commencement, dissertation, leaflet,  school reunion,  feedback, tasks, outcomes, advanced, introductory, extra background, resources room, staff,  higher education, guidelines, post-secondary, faculty, pupils, pencil, supervisor, bachelor’s degree, compound, foreign students, schedule, vocabulary, student support services, student retention, publication,  registrar’s office, stationery'''.replace(
        ' ', '').split(',')

    n_child = 0
    nodequeue = []
    root = Node(w[0])
    node = root

    for c in w[1:]:
        newnode = Node(c, node)
        node.children.append(newnode)
        nodequeue.append(newnode)
        n_child += 1
        if n_child >= 3:
            node = nodequeue.pop(0)
            n_child = 0

    print(root)


class Row:
    def __init__(self):
        self.number = 'X'
        self.comp_lib = 'X'
        self.comp_ref = 'X'
        self.comp_lox = 'X'
        self.comp_loy = 'X'
        self.comp_pkg = 'X'
        self.comp_value = 'X'
        self.doc_page = 'X'
        self.doc_number = 'X'
        self.doc_title = 'X'
        self.page_size_x = 'X'
        self.page_size_y = 'X'

        # 寫死
        self.comp_gate = 1
        self.comp_fun = 'X'

    def toOrderedDict(self):
        dic = collections.OrderedDict()
        dic["number"] = self.number
        dic["comp.lib"] = self.comp_lib
        dic["comp.ref"] = self.comp_ref
        dic["comp.lox"] = self.comp_lox
        dic["comp.loy"] = self.comp_loy
        dic["comp.pkg"] = self.comp_pkg
        dic["comp.value"] = self.comp_value
        dic["doc page"] = self.doc_page
        dic["doc number"] = self.doc_number
        dic["doc title"] = self.doc_title
        dic["page size x"] = self.page_size_x
        dic["page size y"] = self.page_size_y
        dic["comp gate"] = self.comp_gate
        dic["comp fun"] = self.comp_fun
        return dic

    def toList(self):
        return list(self.toOrderedDict().values())


def parseAttr(tagline):
    """parse attributes from tag line except child"""
    q = []
    planLock = False
    clean = ''

    for i, c in enumerate(tagline):
        if c == '(':
            q.append(c)
            if len(q) >= 1:
                planLock = True

        elif c == ')':
            if len(q) == 0:
                break
            else:
                q.pop()
                if len(q) == 1:
                    planLock = False
                    # to remove
        else:
            if not planLock:
                clean += c

    # 含有字串符號的內容，其裡面的空格用底線替代，以維持同一屬性
    stringlist = re.findall(r'\".*?\"', clean)
    if stringlist:
        for string in stringlist:
            clean = clean.replace(string, '_'.join(string.split(' ')))

    stringlist = re.findall(r"\'.*?\'", clean)
    if stringlist:
        for string in stringlist:
            clean = clean.replace(string, '_'.join(
                string.split(' ')).replace("\'", "\""))

    cleanlist = [value for value in clean.split(' ') if value != '']

    if len(cleanlist) > 1:
        key = cleanlist[0]
        values = ';'.join(cleanlist[1:])
        attr = '@'.join([key, values])

    else:
        attr = clean
    return attr.strip()


# @jit
def dataToTree(data):

    tag = parseAttr(data[1:])
    root = Node(tag)
    lockediftag = ''
    pointer = root
    nextLevel = False

    q = []
    outcount = 0
    total_len = len(data)
    for i, c in enumerate(data):
        if c == '(':
            q.append(c)

            # append child and point to the next level
            # max_len = total_len
            tag = parseAttr(data[i+1:])
            # tag = data[i+1:i+30].replace('\n', ' ')\
            #                     .replace(')', ' ')\
            #                     .split(' ')[0]
            # skip root
            if ('edif' not in lockediftag) and 'edif' in tag:
                lockediftag = 'edif'
                continue
            # print('%d appending tag %s' % (i, tag))

            newnode = Node(tag, pointer)
            pointer = pointer.appendAndReturn(newnode)

        elif c == ')':

            if len(q) < 1:
                print('unbalance')
                exit()
            q.pop()

            pointer = pointer.parent

    return root
    # node_pattern = r'\([a-zA-Z0-9]+'

    # startrecord = False
    # nodeinfo = ''
    # for c in data:
    #     if c == '(':
    #         startrecord = True
    #     elif c == ')':
    #         pass
    # return

    # for t in l2tag:
    #     print(t)
    # print('\n'+'*'*30+'Unique tags'+'*'*30)
    # tagset = set()
    # for t in l2tag:
    #     if t not in tagset:
    #         print(t)
    #         tagset.add(t)


def treeToDict(root):
    target = {}

    pointer = root
    dictpointer = target

    target[pointer.value] = {}

    for child in pointer.children:

        pass


def dictifyNode(node):
    """每個 node 的結構
        {key:{
            "value": attr... ,  
            "child1's key": [
                    "value": attr...,
                    "grandchild's key": ...
                ],
            "child1's key":[
                ...
                ]
            }
        }

        如果 node value 可以切割，取前段為 dict : key
        不可切割，整段為 dict: key

        dict : value 一定是 dict

        left : children = [] 的 node
    """

    k, v = parseNodeValue(node)
    target = {k: {"value": v}}

    if node.children == []:
        return target

    for child in node.children:
        childk, childv = parseNodeValue(child)

        target[k][childk] = childv


def traverse(head):
    # post-order traverse

    mainDict = {}
    # 如果有重複 child key，要變成 list，再加入 dict
    childrenkeys = [parseNodeValue(child)[0]  # get key of child of child
                    for child in head.children]
    uniquekeys = list(set(childrenkeys))
    for key in uniquekeys:
        childrenkeys.remove(key)
    # 重複集合
    childrenkeys = list(set(childrenkeys))
    # key 重複直接
    for key in childrenkeys:
        mainDict[key] = []

    for child in head.children:

        k, v = parseNodeValue(child)

        if child.children != []:
            childDict = traverse(child)
            if v != '':
                childDict['entry'] = v

            # 有自己的屬性，用 entry 當 key
            if k in childrenkeys:
                mainDict[k].append(childDict)
            else:
                mainDict[k] = childDict
        else:
            if v != '':
                if k in childrenkeys:
                    mainDict[k].append(v)
                else:
                    mainDict[k] = v
            else:
                mainDict[k] = None
    return mainDict


def parseNodeValue(node):

    nodevalue = node.value
    if '@' in nodevalue:
        k, v = nodevalue.split('@')
        if ';' in v:
            v = v.split(';')
    else:
        k = nodevalue
        v = ''
    return k.strip(), v


data = data.replace('\n', ' ')
root = dataToTree(data)
with open('testexe.txt', 'w') as f:
    f.write(root.__str__())
# print(root)
# datajson = traverse(root)
# with open('output/treeJsonLid.json', 'w') as f:
#     jsonstring = json.dump(datajson, f)

# pprint(datajson['design']['cellref'], width=1, indent=2)

# iter = re.finditer(r'\".*\"\(displayPINNUMBER', data.replace(' ', ''))
# for i in range(100):
#     print(next(iter))

# r = (traverse(root))

# root.__str__()
# testTree()


# instances = get_instance_record(data)

# for i in range(len(instances)):
#     get_row_from_instance(instances[i])

# instances = ''.join(instances)

# with open("instances_output.txt", 'w') as f:
#     print(f"{len(instances)} instances have been written.")
#     f.write(instances)

# # check command set
# pattern_command = f'\([a-zA-Z]+ '
# commands = re.findall(pattern_command, data)
# commands = [com.replace('(', '') for com in commands if 'property' not in com]
# commands = collections.Counter(commands)
# com_keys = commands.keys()
# com_values = [commands[k] for k in com_keys]
# com = list(zip(com_keys, com_values))
# # print('commands : ', len(commands.keys()))

# # for k, v in sorted(com, key=lambda x: -x[1]):
# #     print('%20s: %d' % (k, v))

# # property type only
# pattern_command = f'\(property [a-zA-Z0-9]+'
# commands = re.findall(pattern_command, data)
# commands = [com.replace('(', '') for com in commands]
# commands = collections.Counter(commands)
# com_keys = commands.keys()
# com_values = [commands[k] for k in com_keys]
# com_pro = list(zip(com_keys, com_values))
# com += com_pro
# print('property types: ', len(commands.keys()))

# for k, v in sorted(com, key=lambda x: -x[1]):
#     print('%35s: %d' % (k, v))

# testTree()
