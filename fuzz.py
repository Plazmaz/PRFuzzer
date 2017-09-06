import requests
import json
import re
FAKE_STRINGS = [u'\u202e', u'\u0000', "A\n" * 5000, u'\u202e' * 5000] # Long strings break stuff
NULL_STRINGS = [u"null", u"\"null\"", u"\"false\"", u"false", u"\"\""]
FUZZ_IDX = 0
SRC_BRANCH = "src-branch"
DST_BRANCH = "master"
USER = ""
PASS = ""
REPO = ""
CONTENT_TYPE = "plain"
ENDPOINT = ""
with open("config.txt") as f:
    lines = f.readlines()
    for line in lines:
        line = line.replace("\n", "")
        if(line.startswith("USERNAME=")):
            USER = line[len("USERNAME="):]
        elif(line.startswith("PASSWORD=")):
            PASS = line[len("PASSWORD="):]
        if(line.startswith("REPOSITORY=")):
            REPO = line[len("REPOSITORY="):]
print("http://api.bitbucket.org/rest/api/1.0/projects/~" + USER + "/repos/" + REPO + "/pull-requests")

def fuzz_string(offset, nullable=False):
    global FUZZ_IDX
    str_array = []
    if(nullable):
        str_array = FAKE_STRINGS + NULL_STRINGS
    else:
        str_array = FAKE_STRINGS
    res = str_array[(FUZZ_IDX + offset) % len(str_array)]    
    FUZZ_IDX += 1
    return res
 
 #Can be changed to any file
with open('bitbucket-pr.json') as f:
    data = f.readlines()
    payloads = []
    i = 0
    for j in range(10):
        newLines = []
        for line in data:
            if "$$SRCBRANCH" in line:
                line = line.replace("$$SRCBRANCH", SRC_BRANCH)
            if "$$DSTBRANCH" in line:
                line = line.replace("$$DSTBRANCH", DST_BRANCH)
            if "$$USER" in line:
               line = line.replace("$$USER", USER)
            if "$$REPO" in line:
               line = line.replace("$$REPO", REPO)
            if "${NSTR}" in line:
                line = line.replace("${NSTR}", fuzz_string(0, True))
            if "${STR}" in line:
               line = line.replace("${STR}", fuzz_string(0, False))
            if "${BOOL}" in line:
                line = line.replace("${BOOL}", "true" if FUZZ_IDX % 2 == 0 else "false")
            if "${NVAL:" in line:
                options = re.compile("\$\{NVAL:(.*?)\}").search(line).group(1)
                options = options.split(",")
                print(options[(FUZZ_IDX + i) % len(options)])
                line = re.sub("\$\{NVAL:(.*?)\}", "\"" + options[(FUZZ_IDX + i) % len(options)] + "\"", line)
            # Config is lines 1 and 2.
            if i <= 1:
                print("LINE: " +line)
                if line.startswith("ENDPOINT="):
                    line = line.replace("\n", "")
                    ENDPOINT = line[len("ENDPOINT="):]
                    continue
                elif line.startswith("TYPE="):
                    line = line.replace("\n", "")
                    CONTENT_TYPE = line[len("TYPE="):]
                    continue
            newLines.append(line.encode('utf-8'))
            i += 1
        print("".join(newLines))
        if CONTENT_TYPE == "json":
            json_data = json.loads("".join(newLines))
            r = requests.post(ENDPOINT, auth=(USER, PASS), json=json_data)
            print(r.status_code, r.reason)
            print(r.text[:300] + '...')
        else:
            print("ENDPOINT " + ENDPOINT)
            r = requests.post(ENDPOINT, auth=(USER, PASS), data="".join(newLines))
            print(r.status_code, r.reason)
            print(r.text[:300] + '...')