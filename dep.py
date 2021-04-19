from semver import *
from package_ref import *
from suffix import *

import urllib
from ctypes import cdll, c_char_p


def parse_gopkg_lock(file_type_descriptor, data):
    reference = []
    lineno = 0
    lines = data.split("\n")
    list_length = -1
    for line in lines:
        # print(line)
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
            if val != "":
                lib = cdll.LoadLibrary('./dc.o')

                # print(lib.Sum(1, 2))
                lib.DecodeSource.argtype = c_char_p
                lib.DecodeSource.restype = c_char_p

                out = lib.DecodeSource(bytes(val, encoding="utf8"))

                source = out.decode('utf-8')

                # if source != "":
                #     reference[list_length - 1].set_source(source)
        else:
            if key == "version":
                if not isvalid(val) or canonical(val) != val:
                    continue
                else:
                    reference[list_length - 1].set_version(val)
            else:
                reference[list_length - 1].set_revision(val)

    # cnt = 0
    # for r in reference:
    #     if r.Path == "" or (r.Version == "" and r.Revision == ""):
    #         print("wrong reference!")
    #     else:
    #         print("---------" + str(cnt) + "---------")
    #         print(r.Path + " : " + r.Revision + " ( " + r.Version + " )")
    #
    #     cnt = cnt + 1

    return reference
