#! /usr/bin/env python3

import os
import json
import copy
import readline
import glob
import re
from snakemake import load_configfile
from collections import defaultdict
import argparse
from NextSnakes.Logger import *
from functools import reduce
import operator
import datetime
import _version

parser = argparse.ArgumentParser(
    description="Helper to create or manipulate initial config file used for workflow processing with NextSnakes"
)
parser.add_argument(
    "-t",
    "--test",
    action="store_true",
    default=False,
    help="runnign in test-mode for showing interim results to copy",
)
args = parser.parse_args()


class NestedDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(NestedDefaultDict, self).__init__(NestedDefaultDict, *args, **kwargs)


class PROJECT:
    def __init__(self):
        self.name = ""
        self.subname = ""
        self.path = ""
        self.cores = 1
        self.baseDict = NestedDefaultDict()
        self.commentsDict = NestedDefaultDict()
        self.conditionDict = NestedDefaultDict()
        self.samplesDict = NestedDefaultDict()
        self.workflowsDict = NestedDefaultDict()
        self.settingsDict = NestedDefaultDict()
        self.settingsList = []


class GUIDE:
    def __init__(self):
        self.mode = ""
        self.answer = ""
        self.toclear = 0
        self.testing = False

    def clear(self, number=None):
        if not number:
            number = self.toclear
        CURSOR_UP_ONE = "\x1b[1A"
        ERASE_LINE = "\x1b[2K"
        for i in range(number):
            print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE)
        self.toclear = 0

    def display(self, options=None, question=None, proof=None, spec=None):
        if options:
            space = 0
            for k, v in options.items():
                if len(str(k)) >= space:
                    space = len(str(k))
            for k, v in options.items():
                prYellow(f"   {k}{' '*(space+2-len(str(k)))}>  {v}")
                guide.toclear += 1
        if question:
            print("\n" + bold_color.BOLD + question + bold_color.END)
            guide.toclear += 1
        self.proof_input(proof, spec)

    def proof_input(self, proof=None, spec=None):
        unallowed_characters = ["{", "}"]
        while True:
            if spec:
                a = rlinput(">>> ", spec)
            else:
                a = input(">>> ").strip()

            if any(x in unallowed_characters for x in a):
                safe = self.toclear
                self.clear(2)
                self.toclear = safe
                prRed("You used unallowed letters, try again")
                continue

            if proof == None:
                self.answer = a
                break
            elif proof == "only_numbers":
                try:
                    [float(x) for x in a.split(",")]
                    self.answer = a
                    break
                except:
                    self.clear(2)
                    prRed("please enter integer or float")
                    continue
            elif "end_exist_" in proof:
                if not a:
                    self.answer = a
                    break
                ending = proof.replace("end_exist_", "") + "$"
                if not re.findall(ending, a):
                    self.clear(2)
                    prRed(f"Nope, file has to end with '{ending.replace('$','')}'")
                    continue
                elif not os.path.isfile(a):
                    self.clear(2)
                    prRed(f"Nope, '{a}' doesn't exist")
                    continue
                else:
                    self.answer = a
                    break
            else:
                if any(x not in proof for x in a.split(",")):
                    safe = self.toclear
                    self.clear(2)
                    self.toclear = safe
                    prRed(f"available are: {proof}")
                    continue
                else:
                    self.answer = a
                break


class bold_color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


## PRINTERS
def prRed(skk):
    print("\033[91m{}\033[00m".format(skk))


def prGreen(skk):
    print("\033[92m{}\033[00m".format(skk))


def prYellow(skk):
    print("\033[93m{}\033[00m".format(skk))


def prLightPurple(skk):
    print("\033[94m{}\033[00m".format(skk))


def prPurple(skk):
    print("\033[95m{}\033[00m".format(skk))


def prCyan(skk):
    print("\033[96m{}\033[00m".format(skk))


def prLightGray(skk):
    print("\033[97m{}\033[00m".format(skk))


def print_dict(dict, indent=6, col=None, gap=""):
    if col == "Cyan":
        for line in json.dumps(dict, indent=indent).split("\n"):
            guide.toclear += 1
            prCyan(gap + line)
    else:
        for line in json.dumps(dict, indent=indent).split("\n"):
            guide.toclear += 1
            print(gap + line)


## DICT MANIPULATORS
def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    if isinstance(get_by_path(root, items[:-1])[items[-1]], list):
        gp = get_by_path(root, items[:-1])[items[-1]]
        gp.append(value)
    else:
        get_by_path(root, items[:-1])[items[-1]] = value


def del_by_path(root, items):
    """Delete a key-value in a nested object in root by item sequence."""
    if isinstance(get_by_path(root, items[:-1])[items[-1]], str):
        get_by_path(root, items[:-1])[items[-1]] = ""
    else:
        del get_by_path(root, items[:-1])[items[-1]]


def setInDict(dataDict, maplist, value):
    first, rest = maplist[0], maplist[1:]
    if rest:
        try:
            if not isinstance(dataDict[first], dict):
                dataDict[first] = {}
        except KeyError:
            dataDict[first] = {}
        setInDict(dataDict[first], rest, value)
    else:
        try:
            if isinstance(dataDict[first], list):
                dataDict[first].append(value)
            else:
                dataDict[first] = value
        except:
            dataDict[first] = value


def get_conditions_from_dict(root, keylist=[]):
    for k, v in root.items():
        keylist.append(
            k,
        )
        if not v:
            yield ":".join(keylist)
        else:
            yield from get_conditions_from_dict(v, keylist)
        keylist.pop()


def getPathesFromDict(d, value=None):
    def yield_func(d):
        q = [(d, [])]
        while q:
            n, p = q.pop(0)
            yield p
            if isinstance(n, dict):
                for k, v in n.items():
                    q.append((v, p + [k]))
            elif isinstance(n, list):
                for i, v in enumerate(n):
                    q.append((v, p + [i]))

    ret = [p for p in yield_func(d)]
    if value:
        sel = []
        for path in ret:
            if value in path:
                sel.append(path)
        return sel
    return ret


def decouple(d):
    string = json.dumps(d)
    return json.loads(string)


def print_dict_pointer(dict, path, copy, indent=6):
    text = json.dumps(dict, indent=indent)
    route = ["step"] + path.copy()
    out = f"\n{'='*60}\n\n"
    stepper = 1
    for line in text.split("\n"):
        level = int(((len(line) - len(line.lstrip(" "))) - indent) / indent)
        key = (
            line.replace('"', "")
            .replace("{", "")
            .replace("}", "")
            .replace(":", "")
            .replace(",", "")
            .strip()
        )
        if level + 1 >= len(route):
            out += line + "\n"
        elif not key:
            out += line + "\n"
        elif route[level + 1] == key and route[level] == "step":
            route[stepper] = "step"
            stepper += 1
            if len(route) == level + 2:
                if route[level - 1] == "step":
                    if copy and copy != [""]:
                        out += f"{line}    <-\n"
                        option = f"enter ID's on condition level comma separated \n\nor copy {copy} with 'cp'"
                        guide.toclear += 2
                    else:
                        out += f"{line}    <-\n"
                        option = "enter ID's on conditions comma separated "
                else:
                    out += f"{line}    <-\n"
                    option = "enter ID's on conditions comma separated "
            else:
                out += line + "\n"
        else:
            out += line + "\n"
    out += f"\n{'='*60}\n\n"
    return out, option


def rec_tree_builder(subtree, leafes, path=[], tree=None):
    if tree == None:
        tree = subtree
    if not leafes[0]:
        path.pop()
        return
    for leaf in leafes:
        if not leaf in subtree.keys():
            subtree[leaf] = NestedDefaultDict()
    copy = []
    for k, v in subtree.items():
        path.append(k)
        text, opt = print_dict_pointer(tree, path, copy)
        for line in text.split("\n"):
            if "<-" in line:
                prYellow("  " + line)
            else:
                prRed("  " + line)
        guide.toclear += len(text.split("\n")) + 2
        guide.display(question=opt)
        guide.clear()
        if guide.answer != "":
            guide.answer = guide.answer.rstrip(",")
            leafes = [x for x in guide.answer.split(",")]
        elif guide.answer == "" and isinstance(v, dict) and v != {}:
            leafes = list(v.keys())
        else:
            leafes = [""]
        if leafes == ["cp"]:
            leafes = copy
        rec_tree_builder(subtree[k], leafes, path, tree)
        copy = leafes
        leafes = [""]
    if len(path) > 0:
        path.pop()
    return


def depth(d):
    if isinstance(d, dict):
        return 1 + (max(map(depth, d.values())) if d else 0)
    return 0


def select_id_to_set(cdict, i, indent=6):
    text = json.dumps(cdict, indent=indent)
    project.settingsList = []
    d = depth(cdict)
    path = []
    reminder = ""
    counter = 0
    prRed(f"\n{'='*60}\n")
    for line in text.split("\n"):
        level = int(((len(line) - len(line.lstrip(" "))) - indent) / indent)
        key = (
            line.replace('"', "")
            .replace("{", "")
            .replace("}", "")
            .replace(":", "")
            .replace(",", "")
            .strip()
        )
        if key:
            if len(path) > level:
                path = path[: -(len(path) - level)]
            path.append(key)
        if level == i and ":" in line:
            if reminder != key:
                counter += 1
                reminder = key
                project.settingsList.append([])
        elif level < i and "{}" in line:
            counter += 1
            project.settingsList.append([])
        if "{}" in line:
            if "," in line:
                out = f"{line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}"
                if counter % 2:
                    prPurple("  " + out)
                else:
                    prLightPurple("  " + out)
            else:
                out = f"{line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}"
                if counter % 2:
                    prPurple("  " + out)
                else:
                    prLightPurple("  " + out)
            project.settingsList[-1].append(path)
        else:
            prRed("  " + line)
        guide.toclear += 1
    prRed(f"\n{'='*60}\n")
    guide.toclear += 6


def location(dictionary, setting, indent=6):
    prRed(f"\n{'='*60}\n")
    spots = copy.deepcopy(setting)
    d = depth(dictionary)
    text = json.dumps(dictionary, indent=indent)
    for line in text.split("\n"):
        switch = True
        level = int(((len(line) - len(line.lstrip(" "))) - indent) / indent)
        key = (
            line.replace('"', "")
            .replace("{", "")
            .replace("}", "")
            .replace(":", "")
            .replace(",", "")
            .strip()
        )
        if key:
            for path in spots:
                if not path:
                    continue
                if path[0] == key:
                    path.pop(0)
                    if not path:
                        if "," in line:
                            prYellow(
                                f"  {line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-"
                            )
                        else:
                            prYellow(
                                f"  {line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-"
                            )
                        switch = False
        if switch:
            prRed("  " + line)
        guide.toclear += 1
    prRed(f"\n{'='*60}\n")
    guide.toclear += 4


def show_settings():
    if guide.testing == False:
        return
    provars = NestedDefaultDict()
    provars["guide.mode"] = guide.mode
    provars["project.name"] = project.name
    provars["project.path"] = project.path
    provars["project.cores"] = project.cores
    provars["project.baseDict"] = project.baseDict
    provars["project.conditionDict"] = project.conditionDict
    provars["project.samplesDict"] = project.samplesDict
    provars["project.settingsDict"] = project.settingsDict
    provars["project.settingsList"] = project.settingsList
    provars["project.workflowsDict"] = project.workflowsDict
    provars["project.commentsDict"] = project.commentsDict
    print(f"============COPYME:\n")
    for name, var in provars.items():
        if isinstance(var, str):
            var = f"'{var}'"
        if isinstance(var, dict):
            var = json.dumps(var, indent=4)
        try:
            print(f"{name} = {var}")
        except:
            print(f"{name} = NestedDefaultDict()")
    print(f"\n============")


def rlinput(prompt, prefill=""):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def complete(text, state):
    return (glob.glob(text + "*") + [None])[state]


readline.set_completer_delims(" \t\n;")
readline.parse_and_bind("tab: menu-complete")
readline.set_completer(complete)

project = PROJECT()
guide = GUIDE()


################################################################################################################
####                                            CONVERSATION                                                ####
################################################################################################################


def prepare_project(template):
    # add template dict to project object
    project.baseDict = template
    # add comments to commentsdict and remove them from baseDict
    comment_pathes = getPathesFromDict(project.baseDict, "comment")
    for path in comment_pathes:
        if path[-1] != "comment":
            continue
        opt = get_by_path(project.baseDict, path)
        set_by_path(project.commentsDict, path, opt)
        del_by_path(project.baseDict, path)
    show_settings()
    return intro()


def intro():
    print("NSW: " + __version__)
    print("RTD: https://nextsnakes.readthedocs.io/en/latest/index.html\n")
    print(
        bold_color.BOLD
        + "N E X T S N A K E S   C O N F I G U R A T O R"
        + bold_color.END
        + "\n"
    )
    opts = {
        "1": "create new project",
        "2": "modify existing config-file",
        "3": "add config-file to existing project",
    }
    guide.display(
        question="choose an option",
        options=opts,
        proof=opts.keys(),
    )
    guide.clear(3)
    if guide.answer == "1":
        guide.mode = "new"
        return new()
    if guide.answer == "2":
        guide.mode = "modify"
        return modify()
    if guide.answer == "3":
        guide.mode = "new"
        return new(existing=True)


def new(existing=False):
    if existing:
        prGreen("\nCREATE NEW CONFIG")
    else:
        prGreen("\nCREATE NEW PROJECT")
    print("\n   Directory:")
    er = 0
    while True:
        if er == 0:
            if existing:
                ques = "Enter the absolute of your project-folder"
            else:
                ques = "Enter the absolute path where your project-folder should be created"
        if er == 1:
            ques = "couldn't find this directory"
        if er == 2:
            ques = "WARNING: The directory you entered already exist."
        guide.display(question=ques, spec=os.getcwd())
        project.name = os.path.basename(guide.answer)
        project.path = guide.answer
        if os.path.isdir(project.path) and not existing:
            guide.clear(3)
            er = 2
            continue
        if os.path.isdir(project.path) and existing:
            guide.clear(4)
            prCyan(f"  Directory: {project.path}")
            print("\n  Subname: ")
            guide.display(question=f"enter subname to differ from {project.name}")
            project.subname = guide.answer
            guide.clear(4)
            prCyan(f"  Subname: {project.subname}")
            break
        if os.path.isdir(os.path.dirname(project.path)):
            guide.clear(4)
            prCyan(f"   Directory: {project.path}")
            break
        else:
            guide.clear(3)
            er = 1
    show_settings()
    return add_workflows()


def add_workflows(existing_workflows=None):
    prGreen("\nADD WORKFLOWS\n")
    possible_workflows = list(project.baseDict.keys())
    for e in none_workflow_keys:
        possible_workflows.remove(e)
    if existing_workflows:
        for e in existing_workflows:
            possible_workflows.remove(e)
    posWorkDict = NestedDefaultDict()
    counter = 1
    for w in possible_workflows:
        posWorkDict[counter] = w
        counter += 1
    guide.display(
        question="choose WORKFLOWS comma separated",
        options=posWorkDict,
        proof=list(str(i) for i in posWorkDict.keys()),
    )
    addedW = []
    for number in guide.answer.split(","):
        wf = posWorkDict[int(number)]
        addedW.append(wf)
        project.workflowsDict[wf]
    guide.clear(3)
    prCyan(f"\n   Added Workflows: {', '.join(addedW)}")
    show_settings()
    if guide.mode == "modify":
        return select_conditioning()
    if guide.mode == "new":
        return create_condition_tree()


def create_condition_tree():
    prGreen("\nCREATE CONDITION-TREE:")
    while True:
        rec_tree_builder(project.conditionDict, [project.name])
        print("")
        print_dict(project.conditionDict, gap="   ")
        guide.display(
            question="press enter to continue or type 'no' to create it again",
            proof=["", "no"],
        )
        if guide.answer == "no":
            guide.toclear += 2
            guide.clear()
            project.conditionDict = NestedDefaultDict()
        else:
            guide.toclear += 2
            guide.clear()
            # prCyan("   Condition-Tree:\n")
            print_dict(project.conditionDict, col="Cyan", gap="         ")
            project.settingsDict = decouple(project.conditionDict)
            break
    show_settings()
    return add_sample_dirs()


def add_sample_dirs():
    print("\n  FASTQ files:")
    path_to_samples_dict = NestedDefaultDict()
    er = 0
    while True:

        if er == 0:
            ques = "Enter an absolute path where samples are stored"
            sp = os.getcwd()
        if er == 3:
            ques = "Add another path or press enter to continue"
            sp = ""
        if er == 1:
            ques = f"Sorry, couldn't find '{dir}'. Enter an absolute path where samples are stored"
            sp = dir
        if er == 2:
            ques = f"Samples must be specified to continue. Enter an absolute path where samples are stored"
            sp = os.getcwd()
        guide.display(
            question=ques,
            # options = path_to_samples_dict,
            spec=sp,
        )
        dir = guide.answer
        if guide.answer == "" and len(project.samplesDict) == 0:
            er = 2
            guide.clear(3)
            continue
        if guide.answer == "" and len(project.samplesDict) != 0:
            guide.clear(3)
            break
        if not os.path.isdir(dir):
            er = 1
            guide.clear(3)
            continue
        if "dirpath" not in locals():
            guide.clear(4)
            prCyan("  FASTQ files:\n")
        else:
            guide.clear(3)
        print(f"         {dir}\n")
        opts = {"1": "single", "2": "paired"}
        # print('\n')
        guide.display(
            question="Specify sequencing method", options=opts, proof=opts.keys()
        )
        seq = opts[guide.answer]
        print("")

        opts = {"1": "unstranded", "2": "rf", "3": "fr"}
        guide.display(question="Specify strandedness", options=opts, proof=opts.keys())
        stranded = opts[guide.answer]

        if os.path.isdir(dir):
            counter = 0
            for dirpath, dirnames, filenames in os.walk(dir):
                for filename in [f for f in filenames if f.endswith(".fastq.gz")]:
                    counter += 1
                    name = filename.replace(".fastq.gz", "")
                    if seq == "paired":
                        if "_R1" in filename:
                            name = name.replace("_R1", "")
                        elif "_R2" in filename:
                            name = name.replace("_R2", "")
                        else:
                            continue
                    project.samplesDict[name] = {
                        "file": filename,
                        "dir": dirpath,
                        "seq": seq,
                        "strand": stranded,
                        "cond": "",
                    }

            path_to_samples_dict[dir] = f"{counter} {seq} files found"
            guide.clear(14)
            prCyan(f"         {dir}  >  {counter} {seq} files found")
            # print_dict(project.samplesDict)
            er = 3
            continue

    counter = 1
    show_settings()
    return assign_samples()


def assign_samples():
    prCyan("\n  Sample Assignment:\n")
    conditions = [
        pattern for pattern in get_conditions_from_dict(project.conditionDict)
    ]
    if guide.mode == "modify":
        safety_dict = decouple(project.settingsDict)
    elif guide.mode == "new":
        safety_dict = decouple(project.conditionDict)
        project.settingsDict = decouple(project.conditionDict)
    else:
        print("WARNING: NO MODE!!")
        exit()
    er = 0
    guide.toclear = 0
    while True:
        opts = NestedDefaultDict()
        number = 1
        space = 0
        for k in project.samplesDict.keys():
            if len(k) >= space:
                space = len(k)
        if er == 0:
            for k in project.samplesDict.keys():
                opts[
                    number
                ] = f"{k}{' '*(space+2-len(k))} in  {project.samplesDict[k]['dir']}"
                number += 1
        # samplesInList = []
        for condition in conditions:
            # for s in samplesInList:
            #     toDelete = []
            #     for k, v in opts.items():
            #         if s in v:
            #             toDelete.append(k)
            # for d in toDelete:
            #     del opts[d]
            if (
                "SAMPLES"
                in get_by_path(project.settingsDict, condition.split(":")).keys()
            ):
                continue
            if er == 0:
                ques = f"enter all sample-numbers according to the displayed condition comma separated"
            if er == 1:
                guide.clear(guide.toclear + 4)
                ques = f"ERROR: Its not possible to merge single-end and paired-end samples, try again"

            cond_as_list = [x for x in condition.split(":")]
            location(project.settingsDict, [cond_as_list])

            guide.display(
                question=ques, options=opts, proof=[str(i) for i in opts.keys()]
            )

            check_seq = set()
            for num in guide.answer.split(","):
                check_seq.add(project.samplesDict[opts[int(num)].split(" ")[0]]["seq"])
            if len(check_seq) > 1:
                er = 1
                break
            else:
                er = 0
            samplesInList = []
            for num in guide.answer.split(","):
                project.samplesDict[opts[int(num)].split(" ")[0]]["cond"] = condition
                samplesInList.append(opts[int(num)].split(" ")[0])
            set_by_path(
                project.settingsDict,
                cond_as_list,
                {"SAMPLES": samplesInList},
            )
            guide.clear(guide.toclear + 4)
        if er == 1:
            continue
        print_dict(project.settingsDict, gap="   ")
        guide.display(
            question="press enter to continue or type 'no' to assign samples again"
        )
        if guide.answer == "no":
            guide.toclear += 2
            project.settingsDict = decouple(safety_dict)
        else:
            guide.toclear += 2
            guide.clear()
            print_dict(project.settingsDict, col="Cyan", gap="         ")
            break
    show_settings()
    return set_settings()


def set_settings():
    prGreen("\nGENERAL SETTINGS")
    print("(blank entry possible)")
    guide.toclear = 0
    safety_dict = decouple(project.settingsDict)
    conditions_list = [
        pattern.split(":")
        for pattern in get_conditions_from_dict(project.conditionDict)
    ]
    while True:
        previous_maplist = []
        for maplist in conditions_list:
            if "SEQUENCING" in get_by_path(project.settingsDict, maplist).keys():
                continue
            prRed(f"\n   Condition:   {' : '.join(maplist)} \n")
            seq = ""
            for k in project.samplesDict.keys():
                try:
                    if project.samplesDict[k]["cond"] == ":".join(maplist):
                        seq = project.samplesDict[k]["seq"]
                except:
                    continue
            setInDict(project.settingsDict, maplist + ["SEQUENCING"], seq)
            settings_to_make = ["REFERENCE", "GTF", "GFF"]
            if list(set(project.workflowsDict.keys()) & set(IP_workflows)):
                settings_to_make = settings_to_make + ["IP"]
            if list(
                set(project.workflowsDict.keys())
                & set(comparable_workflows + ["PEAKS"])
            ):
                settings_to_make = settings_to_make + ["GROUPS", "TYPES", "BATCHES"]
            if list(set(project.workflowsDict.keys()) & set(index_prefix_workflows)):
                settings_to_make = settings_to_make + ["INDEX", "PREFIX"]
            last_answer = os.getcwd()
            for key in settings_to_make:
                print(f"   {key}:")
                if key in ["REFERENCE", "GTF", "GFF", "IP"]:
                    if previous_maplist:
                        if key in ["GTF", "GFF"]:
                            s = get_by_path(
                                project.settingsDict,
                                previous_maplist + ["ANNOTATION", key],
                            )
                        else:
                            s = get_by_path(
                                project.settingsDict, previous_maplist + [key]
                            )
                    else:
                        s = last_answer
                    if key in ["GTF", "GFF"]:
                        p = f"end_exist_.{key.lower()}.*.gz"
                    elif kez == "IP":
                        p = None
                    else:
                        p = "end_exist_.gz"
                else:
                    p = None
                    s = None
                guide.display(
                    question=f"{project.commentsDict['SETTINGS']['comment'][key]}",
                    spec=s,
                    proof=p,
                )
                guide.clear(4)
                last_answer = guide.answer
                prCyan(f"   {key}: {guide.answer}")
                if key in ["GTF", "GFF"]:
                    setInDict(
                        project.settingsDict,
                        maplist + ["ANNOTATION", key],
                        guide.answer,
                    )
                else:
                    setInDict(project.settingsDict, maplist + [key], guide.answer)
            previous_maplist = maplist
        guide.toclear = 0
        print("\n\n   SETTINGS Key:\n")
        print_dict(project.settingsDict, gap="   ")
        guide.display(
            question="\npress enter to continue or type 'no' to make settings again",
            proof=["", "no"],
        )
        if guide.answer == "":
            guide.toclear += 7
            guide.clear()
            prCyan("\n\n   SETTINGS Key:\n")
            print_dict(project.settingsDict, col="Cyan", gap="         ")
            show_settings()
            if guide.mode == "new":
                return select_conditioning()
            if guide.mode == "modify":
                return fillup_workflows()
        if guide.answer == "no":
            project.settingsDict = decouple(safety_dict)
            continue


def set_comparison_settings():
    last_sample = ""
    for sample in get_by_path(project.settingsDict, maplist + ["SAMPLES"]):

        prPurple(f"\n      Sample: {sample}\n")
        for key in ["GROUPS", "TYPES", "BATCHES"]:
            if last_sample and key == "GROUPS":
                ques = f"enter 'cp' to copy entries from sample before"
            else:
                ques = f"{project.commentsDict['SETTINGS']['comment'][key]}"
            print(f"         {key}:")
            guide.display(question=ques)
            if guide.answer == "cp" and last_sample:
                guide.clear(4)
                for key in ["GROUPS", "TYPES", "BATCHES"]:
                    to_add = get_by_path(project.settingsDict, maplist + [key])[-1]
                    prCyan(f"         {key}: {to_add}")
                    get_by_path(project.settingsDict, maplist + [key]).append(to_add)
                break
            else:
                last_sample = sample
                guide.clear(4)
                prCyan(f"         {key}: {guide.answer}")
                try:
                    get_by_path(project.settingsDict, maplist + [key]).append(
                        guide.answer
                    )
                except:
                    setInDict(project.settingsDict, maplist + [key], [])
                    get_by_path(project.settingsDict, maplist + [key]).append(
                        guide.answer
                    )


def modify():
    prGreen("\nMODIFY PROJECT")
    er = 0
    while True:
        if er == 0:
            ques = "Enter the absolut path of the config file to be modified"
        if er == 1:
            ques = "couldn't find the file"
        if er == 2:
            ques = (
                "can't read the file, check if it's the right file or if it's corrupted"
            )
        guide.display(question=ques, spec=os.getcwd())
        if not os.path.isfile(guide.answer):
            guide.clear(3)
            er = 1
            continue
        try:
            modify_config = load_configfile(guide.answer)
            project.path = os.path.dirname(guide.answer)
            project.name = list(modify_config["SETTINGS"].keys())[0]
            project.cores = modify_config["MAXTHREADS"]
            project.settingsDict = modify_config["SETTINGS"]
            project.conditionDict = NestedDefaultDict()
            guide.clear(2)
            prCyan(f"   {guide.answer}")
        except:
            er = 2

        condition_pathes = getPathesFromDict(modify_config, "SAMPLES")
        for path in condition_pathes:
            if path[-1] == "SAMPLES":
                path = path[1:-1]
                setInDict(project.conditionDict, path, {})

        active_workflows = modify_config["WORKFLOWS"].split(",")
        inactive_workflows = list(modify_config.keys())
        for e in none_workflow_keys:
            inactive_workflows.remove(e)
        for wf in inactive_workflows:
            project.workflowsDict[wf] = decouple(modify_config[wf])
        for e in modify_config["WORKFLOWS"].split(","):
            inactive_workflows.remove(e)
        prRed("\n   Following configuration was found :\n")
        prRed("   Condition-Tree:\n")
        print_dict(project.conditionDict, gap="      ")
        prRed("\n   active WORKFLOWS:\n")
        if active_workflows:
            print("      " + ", ".join(active_workflows))
        else:
            print("      -")
        prRed("\n   inactive WORKFLOWS:\n")
        if inactive_workflows:
            print("      " + ", ".join(inactive_workflows))
        else:
            print("      -")

        print("\nWhat do you want to do...\n")
        opts = NestedDefaultDict()
        opts["1"] = "add workflows"
        opts["2"] = "remove workflows"
        opts["3"] = "add conditions"
        opts["4"] = "remove conditions"
        opts["5"] = "choose another file"
        guide.display(question="choose an option", options=opts, proof=opts.keys())
        guide.clear(3)
        if guide.answer == "1":
            return add_workflows(inactive_workflows + active_workflows)
        if guide.answer == "2":
            return remove_workflows(active_workflows, inactive_workflows)
        if guide.answer == "3":
            return add_conditions()
        if guide.answer == "4":
            return remove_conditions()
        if guide.answer == "5":
            project.settingsDict = NestedDefaultDict()
            project.conditionDict = NestedDefaultDict()
            project.workflowsDict = NestedDefaultDict()
            continue


def add_conditions():
    prGreen("\n\nADD CONDIIONS")
    while True:
        new_conditions = decouple(project.conditionDict)
        rec_tree_builder(new_conditions, [project.name])
        print("\n   New Condition-Tree:\n")
        print_dict(new_conditions, gap="   ")
        guide.display(
            question="press enter to apply changes or type 'no' to make changes again",
            proof=["", "no"],
        )
        if guide.answer == "no":
            guide.toclear += 3
            guide.clear()
            continue
        else:
            project.conditionDict = new_conditions
            guide.toclear += 4
            guide.clear()
            prCyan("   New Condition-Tree:\n")
            print_dict(project.conditionDict, col="Cyan", gap="         ")
            # project.settingsDict = decouple(project.conditionDict)
            break

    conditions = [
        pattern.split(":")
        for pattern in get_conditions_from_dict(project.conditionDict)
    ]
    for condition in conditions:
        try:
            get_by_path(project.settingsDict, condition)
        except:
            setInDict(project.settingsDict, condition, NestedDefaultDict())
        for wf in project.workflowsDict.keys():
            try:
                get_by_path(project.workflowsDict, [wf] + condition)
            except:
                setInDict(project.workflowsDict, [wf] + condition, NestedDefaultDict())
    show_settings()
    return add_sample_dirs()


def remove_workflows(actives, inactives):
    prGreen("\n\nREMOVE WORKFLOWS")
    workflows = project.workflowsDict.keys()
    opts = NestedDefaultDict()
    number = 1
    for wf in workflows:
        opts[str(number)] = wf
        number += 1
    while True:
        print("\nfollowing workflows exist:\n")
        guide.display(
            question="enter numbers of workflows to be removed comma separated",
            options=opts,
            proof=opts.keys(),
        )
        new_workflows = decouple(project.workflowsDict)
        new_actives = copy.deepcopy(actives)
        new_inactives = copy.deepcopy(inactives)
        for key, value in opts.items():
            if key in guide.answer.split(","):
                new_workflows.pop(value)
                if value in new_actives:
                    new_actives.remove(value)
                if value in new_inactives:
                    new_inactives.remove(value)
        prRed("\n   active WORKFLOWS:\n")
        if new_actives:
            print("      " + ", ".join(new_actives))
        else:
            print("      -")
        prRed("\n   inactive WORKFLOWS:\n")
        if new_inactives:
            print("      " + ", ".join(new_inactives))
        else:
            print("      -")
        guide.display(
            question="press enter to apply changes or type 'no' to make changes again",
            proof=["", "no"],
        )
        if guide.answer == "":
            project.workflowsDict = new_workflows
            return finalize()
        if guide.answer == "no":
            continue


def remove_conditions():
    prGreen("\n\nREMOVE CONDITIONS")
    conditions = get_conditions_from_dict(project.conditionDict)
    opts = NestedDefaultDict()
    number = 1
    for c in conditions:
        opts[str(number)] = c
        number += 1
    while True:
        new_settings = decouple(project.settingsDict)
        new_workflows = decouple(project.workflowsDict)
        new_conditions = decouple(project.conditionDict)
        print("\nfollowing conditions exist:\n")
        guide.display(
            question="enter numbers of conditions to be removed comma separated",
            options=opts,
            proof=opts.keys(),
        )
        numbers = guide.answer.split(",")
        for number in numbers:
            path_to_remove = opts[number].split(":")
            del_by_path(new_settings, path_to_remove)
            del_by_path(new_conditions, path_to_remove)
            for key in new_workflows.keys():
                del_by_path(new_workflows, [key] + path_to_remove)
        print_dict(new_settings)
        input()
        print_dict(new_conditions)
        input()
        print_dict(new_workflows)
        input()
        prRed("\nNew condition-Tree:")
        print_dict(new_conditions)
        guide.display(
            question="press enter to apply changes or type 'no' to make changes again",
            proof=["", "no"],
        )
        if guide.answer == "":
            project.settingsDict = new_settings
            project.workflowsDict = new_workflows
            project.conditionDict = new_conditions
            return finalize()
        if guide.answer == "no":
            continue


def select_conditioning():
    prGreen("\n\nSELECT CONDITIONS")
    guide.toclear = 0
    while True:
        d = depth(project.conditionDict)
        for i in range(d - 1):
            select_id_to_set(project.conditionDict, i)
            print(
                "In the following steps you will make different settings for each condition.\nTo avoid repetitions, specify which conditions should get the same settings\nYou will set all conditions with the same number at once afterwards"
            )
            guide.display(
                question="To loop through the possible selections press enter\nFinally enter 'ok' to make the settings",
                proof=["ok", ""],
            )
            guide.toclear += 6
            if guide.answer == "ok":
                guide.clear(8)
                show_settings()
                return set_workflows()
            else:
                guide.clear()


def fillup_workflows():
    conditions = [
        pattern.split(":")
        for pattern in get_conditions_from_dict(project.conditionDict)
    ]
    fillupDict = NestedDefaultDict()
    for wf in project.workflowsDict.keys():
        fillupDict[wf]["on"] = []
        fillupDict[wf]["off"] = []
        for condition in conditions:
            if not get_by_path(project.workflowsDict, [wf] + condition):
                fillupDict[wf]["off"].append(condition)
            if get_by_path(project.workflowsDict, [wf] + condition):
                fillupDict[wf]["on"].append(condition)

    for wf in project.workflowsDict.keys():
        for off_con in fillupDict[wf]["off"]:
            location(project.workflowsDict[wf], [off_con])
            prGreen(f"FILLUP WORKFLOW-SETTINGS FOR {wf}\n")
            opts = NestedDefaultDict()
            number = 1
            for on_con in fillupDict[wf]["on"]:
                opts[str(number)] = f"copy from {':'.join(on_con)}"
                number += 1
            opts[str(number)] = "make new settings"
            guide.display(question="enter option", options=opts, proof=opts.keys())
            if opts[guide.answer] == "make new settings":
                project.settingsList = [[off_con]]
                set_workflows(wf)
            else:
                copy_con = opts[guide.answer].split(" ")[-1].split(":")
                toadd = get_by_path(project.workflowsDict, [wf] + copy_con)
                setInDict(project.workflowsDict, [wf] + off_con, toadd)
    return finalize()


def set_workflows(wf=None):
    if wf:
        workflows = [wf]
    else:
        workflows = project.workflowsDict.keys()
    for workflow in workflows:
        if not project.workflowsDict[workflow] or wf:
            prGreen(f"\nMAKE SETTINGS FOR {workflow}\n")
            opt_dict = NestedDefaultDict()
            tools_to_use = NestedDefaultDict()
            if "TOOLS" in project.baseDict[workflow].keys():
                number = 1
                for k in project.baseDict[workflow]["TOOLS"].keys():
                    opt_dict[number] = k
                    number += 1
                if number > 2:
                    print(f"   Tools:\n")
                    guide.display(
                        question="Select from these available Tools comma separated:",
                        options=opt_dict,
                        proof=[str(i) for i in opt_dict.keys()],
                    )
                    guide.clear(len(opt_dict) + 5)
                    for number in guide.answer.split(","):
                        tools_to_use[opt_dict[int(number)]] = project.baseDict[
                            workflow
                        ]["TOOLS"][opt_dict[int(number)]]
                    prCyan(f"   Tools: {', '.join(tools_to_use.keys())}")
                else:
                    tools_to_use[opt_dict[int(1)]] = project.baseDict[workflow][
                        "TOOLS"
                    ][opt_dict[int(1)]]
                    prCyan(f"   Tool: {', '.join(tools_to_use.keys())}")

            if (
                workflow == "PEAKS"
                and "macs" in ", ".join(tools_to_use.keys())
                or workflow in comparable_workflows
            ):
                prRed(f"\n   Settings for differential Analyses:\n")

            if "CUTOFFS" in project.baseDict[workflow].keys() and not wf:

                project.workflowsDict[workflow].update({"CUTOFFS": {}})
                project.workflowsDict[workflow]["CUTOFFS"].update(
                    project.baseDict[workflow]["CUTOFFS"]
                )

                for key, value in project.baseDict[workflow]["CUTOFFS"].items():
                    print(f"      {key}:")
                    guide.display(
                        question=f"set cutoff", proof="only_numbers", spec=value
                    )
                    guide.clear(4)
                    prCyan(f"      {key}: {guide.answer}")
                    set_by_path(
                        project.workflowsDict,
                        [workflow, "CUTOFFS", key],
                        str(guide.answer),
                    )

            if (
                workflow == "PEAKS"
                and "macs" in ", ".join(tools_to_use.keys())
                or workflow in comparable_workflows
            ):
                project.workflowsDict[workflow]["COMPARABLE"]
                project.workflowsDict[workflow]["EXCLUDE"] = []
                prCyan(f"      Comparables:\n")
                groups = set()
                conditions = get_conditions_from_dict(project.conditionDict)
                for condition in conditions:
                    for g in get_by_path(
                        project.settingsDict, condition.split(":") + ["GROUPS"]
                    ):
                        groups.add(g)
                if len(groups) < 2:
                    guide.clear(2)
                    prCyan(f"      Comparables: No Groups found\n")
                    comp_name = "empty"
                    contrast = [[], []]
                    project.workflowsDict[workflow]["COMPARABLE"][comp_name] = contrast
                else:
                    while True:
                        guide.display(
                            question="Press enter to add a differential contrast or type 'ok'",
                            proof=["", "ok"],
                        )
                        if guide.answer == "ok":
                            guide.clear(2)
                            break

                        number = 1
                        guide.clear(2)
                        opt_dict = NestedDefaultDict()
                        for g in sorted(groups):
                            opt_dict[str(number)] = g
                            number += 1
                        contrast = [[], []]
                        guide.display(
                            question="select base-condition",
                            options=opt_dict,
                            proof=opt_dict.keys(),
                        )
                        guide.toclear += 2
                        contrast[0].append(opt_dict[guide.answer])
                        del opt_dict[guide.answer]
                        print("")
                        guide.display(
                            question="select contrast-condition",
                            options=opt_dict,
                            proof=opt_dict.keys(),
                        )
                        guide.toclear += 2
                        contrast[1].append(opt_dict[guide.answer])

                        guide.toclear += 2
                        guide.clear()
                        comp_name = "-VS-".join(x[0] for x in contrast)
                        prCyan(f"         {comp_name}")
                        project.workflowsDict[workflow]["COMPARABLE"][
                            comp_name
                        ] = contrast
                guide.clear(1)

            for setting in project.settingsList:
                prRed(
                    f"\n   Selected Conditions:   {' / '.join([':'.join(c) for c in setting])}"
                )
                for tool, bin in tools_to_use.items():
                    project.workflowsDict[workflow]["TOOLS"][tool] = bin
                    for maplist in setting:
                        setInDict(
                            project.workflowsDict,
                            [workflow] + maplist + [tool, "OPTIONS"],
                            {},
                        )
                    prPurple(f"\n      Set OPTIONS for tool:  {tool}\n")
                    for option in project.baseDict[workflow][tool]["OPTIONS"]:
                        print(f"      Option: '{option}'")
                        call = project.baseDict[workflow][tool]["OPTIONS"][option]
                        guide.toclear = 0
                        guide.display(
                            question=f"{project.commentsDict[workflow][tool]['comment'][option]}",
                            spec=call,
                        )
                        optsDict = guide.answer
                        for maplist in setting:
                            setInDict(
                                project.workflowsDict,
                                [workflow] + maplist + [tool, "OPTIONS", option],
                                optsDict,
                            )
                        guide.clear(4)
                        prCyan(f"      {option}:  {guide.answer}")
    show_settings()
    if guide.mode == "new" or guide.mode == "":
        return set_cores()
    if guide.mode == "modify":
        return finalize()


def set_cores():
    prGreen("\nSET THREADS\n")
    print("   MAXTHREADS:")
    guide.display(
        question="set the maximum number of cores that can be used",
        proof="only_numbers",
    )
    guide.clear(5)
    prCyan(f"\n   MAXTHREADS: {guide.answer}")
    project.cores = str(guide.answer)
    show_settings()
    return finalize()


def finalize():
    final_dict = NestedDefaultDict()

    final_dict["WORKFLOWS"] = ",".join(project.workflowsDict.keys())
    final_dict["BINS"] = project.baseDict["BINS"]
    final_dict["MAXTHREADS"] = project.cores
    final_dict["VERSION"] = __version__[1:]
    final_dict["SETTINGS"] = project.settingsDict
    final_dict.update(project.workflowsDict)

    if project.subname:
        configfile = f"config_{'_'.join([project.name,project.subname])}.json"
    else:
        configfile = f"config_{project.name}.json"
    print("\n")
    prGreen("FINAL CONFIGURATION:\n")
    print_dict(final_dict)
    print("\n")

    if guide.mode == "new":
        space = len(configfile)
        print(
            "Above is your final configuration of NextSnakes. The Guide will create this directory as new project:\n"
        )
        prGreen(f"  {os.path.dirname(project.path)}")
        prGreen(f"  └─{os.path.basename(project.path)}")
        prGreen(f"     ├─NextSnakes{' '*(space-10)}   >  symlink to {os.getcwd()}")
        prGreen(
            f"     ├─FASTQ{' '*(space-5)}   >  contains symlinks of your samplefiles"
        )
        prGreen(
            f"     ├─GENOMES{' '*(space-7)}   >  contains symlinks of your reference files"
        )
        prGreen(f"     └─{configfile}   >  your brand new configuration file")

        guide.display(
            question="\npress enter to create your project or type 'abort' before it gets serious",
            proof=["", "abort"],
        )
    if guide.mode == "modify":
        print("Above is your updated configuration of NextSnakes\n")
        print(
            "The old config-file will be preserved (it will have a timestamp in it's name)\n"
        )
        guide.display(
            question=f"\npress enter to update {configfile} or type 'abort' before it gets serious",
            proof=["", "abort"],
        )

    if guide.answer == "abort":
        quit()
    else:
        guide.clear(3)
        return create_project(final_dict)


def create_project(final_dict):
    if guide.mode == "new":

        # create Project Folder
        cwd = os.getcwd()
        if not os.path.exists(project.path):
            os.mkdir(project.path)
        fastq = os.path.join(project.path, "FASTQ")
        gen = os.path.join(project.path, "GENOMES")
        ns = os.path.join(project.path, "NextSnakes")
        if not os.path.exists(fastq):
            os.mkdir(fastq)
        if not os.path.exists(gen):
            os.mkdir(gen)
        if not os.path.exists(ns):
            os.symlink(cwd, ns)

        # LINK samples into FASTQ and insert samplenames in dict
        for k in project.samplesDict.keys():
            if project.samplesDict[k]["cond"]:
                condition = project.samplesDict[k]["cond"]
                cond_as_list = [x for x in condition.split(":")[1:]]
                os.chdir(fastq)
                for dir in cond_as_list:
                    if not os.path.exists(os.path.join(dir)):
                        os.mkdir(os.path.join(dir))
                    os.chdir(os.path.join(dir))
                path = "/".join(cond_as_list)
                cond_dir = os.path.join(fastq, path)
                dst = os.path.join(cond_dir, project.samplesDict[k]["file"])
                src = os.path.join(
                    project.samplesDict[k]["dir"], project.samplesDict[k]["file"]
                )
                if not os.path.exists(dst):
                    os.symlink(src, dst)

        # link reference and annotation
        for setting in project.settingsList:
            for condition in setting:
                ref = get_by_path(project.settingsDict, condition + ["REFERENCE"])
                if os.path.isfile(ref):
                    if not os.path.exists(os.path.join(gen, os.path.basename(ref))):
                        os.symlink(
                            os.path.realpath(ref),
                            os.path.join(gen, os.path.basename(ref)),
                        )
                    f = os.path.join(gen, os.path.basename(ref))
                    rel = os.path.os.path.relpath(f, start=project.path)
                    setInDict(project.settingsDict, condition + ["REFERENCE"], rel)
                else:
                    prRed(
                        f"WARNING: reference path at {condition} is not correct, could not symlink, please do by hand"
                    )
                    setInDict(project.settingsDict, condition + ["REFERENCE"], "")

                gtf = get_by_path(
                    project.settingsDict, condition + ["ANNOTATION", "GTF"]
                )
                if os.path.isfile(gtf):
                    if not os.path.exists(os.path.join(gen, os.path.basename(gtf))):
                        os.symlink(
                            os.path.realpath(gtf),
                            os.path.join(gen, os.path.basename(gtf)),
                        )
                    f = os.path.join(gen, os.path.basename(gtf))
                    rel = os.path.os.path.relpath(f, start=project.path)
                    setInDict(
                        project.settingsDict, condition + ["ANNOTATION", "GTF"], rel
                    )
                else:
                    prRed(
                        f"WARNING: GTF path at {condition} is not correct, could not symlink, please do by hand"
                    )
                    setInDict(
                        project.settingsDict, condition + ["ANNOTATION", "GTF"], ""
                    )

                gff = get_by_path(
                    project.settingsDict, condition + ["ANNOTATION", "GFF"]
                )
                if os.path.isfile(gff):
                    if not os.path.exists(os.path.join(gen, os.path.basename(gff))):
                        os.symlink(
                            os.path.realpath(gff),
                            os.path.join(gen, os.path.basename(gff)),
                        )
                    f = os.path.join(gen, os.path.basename(gff))
                    rel = os.path.os.path.relpath(f, start=project.path)
                    setInDict(
                        project.settingsDict, condition + ["ANNOTATION", "GFF"], rel
                    )
                else:
                    prRed(
                        f"WARNING: GFF path at {condition} is not correct, could not symlink, please do by hand"
                    )
                    setInDict(
                        project.settingsDict, condition + ["ANNOTATION", "GFF"], ""
                    )

    if guide.mode == "modify":
        file = os.path.join(project.path, f"config_{project.name}.json")
        bakfile = os.path.join(
            project.path,
            f"config_{project.name}_{datetime.datetime.now().strftime('%Y%m%d_%H_%M_%S')}.json",
        )
        os.system(f"cp {file} {bakfile}")

    if project.subname:
        configfile = f"config_{'_'.join([project.name,project.subname])}.json"
    else:
        configfile = f"config_{project.name}.json"
    with open(os.path.join(project.path, configfile), "w") as jsonout:
        print(json.dumps(final_dict, indent=4), file=jsonout)

    print(f"\nStart RunSnakemake with\n")
    prGreen(f"   cd {project.path}\n")
    prGreen(
        f"   python3 NextSnakes/NextSnakes.py -c {configfile} --directory ${{PWD}}\n\n"
    )


#############################
####    TEST VAR SPACE   ####
#############################

####################
####    MAIN    ####
####################

os.chdir(os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":

    template = load_configfile("../configs/template_base_commented.json")
    __version__ = _version.get_versions()["version"]
    none_workflow_keys = ["WORKFLOWS", "BINS", "MAXTHREADS", "SETTINGS", "VERSION"]
    comparable_workflows = ["DE", "DEU", "DAS", "DTU"]
    IP_workflows = ["PEAKS"]
    index_prefix_workflows = ["MAPPING"]

    if args.test:
        guide.testing = True

    prepare_project(template)
