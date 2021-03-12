from semver import *


class pkg:
    def __init__(self):
        self.Path = ""
        self.Version = ""
        self.Source = ""
        self.Revision = ""

    def set_path(self, path):
        self.Path = path

    def set_version(self, version):
        self.Version = version

    def set_source(self, source):
        self.Source = source

    def set_revision(self, revision):
        self.Revision = revision


def parse_gopkg_lock(filedescriptor, data):
    reference = []
    datatostr = str(data, encoding="utf-8")
    lineno = 0
    lines = datatostr.split("/n")
    list_length = -1
    for line in lines:
        lineno = lineno + 1

        i = line.find("#")
        if i >= 0:
            line = line[:i]

        line.strip()

        if line == "[[projects]]":
            reference.append(pkg())
            list_length = len(reference)
            continue

        if line.startswith("["):
            list_length = -1
            continue

        if list_length == -1:
            continue

        i = line.find("=")
        if i < 0:
            continue

        key = line[:i].strip()
        val = line[i+1:].strip()

        if len(val) >= 2 and val[0] == '"' and val[len(val) - 1] == '"':
            q = val[1:len(val)-1]
            val = q.strip()

        if key == "name":
            reference[list_length - 1].set_path(val)
        elif key == "source":
            reference[list_length - 1].set_source(val)
        else:
            if key == "version":
                if not isvalid(val) or canonical(val) != val:
                    break
                else:
                    reference[list_length - 1].set_version(val)
            else:
                reference[list_length - 1].set_revision(val)

        cnt = 0
        for r in reference:
            if r.Path == "" or (r.Version == "" and r.Revision == ""):
                print("wrong reference!")
            else:
                print("---------" + str(cnt) + "---------")
                print(r.Path + " : " + r.Revision + " ( " + r.Version + " )")

            cnt = cnt + 1






