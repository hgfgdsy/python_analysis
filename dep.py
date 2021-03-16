from semver import *
from package_ref import *
from suffix import *

import re


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
            reference[list_length - 1].set_source(val)
        else:
            if key == "version":
                if not isvalid(val) or canonical(val) != val:
                    continue
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

    # use_versions = []
    # for r in reference:
    #     if r.Path == "" or (r.Version == "" and r.Revision == ""):
    #         print("wrong reference!")
    #     else:
    #         use_version = -3
    #         if r.Version != "":
    #             if not re.findall(r'github.com', r.Path):
    #                 use_version = -2
    #             else:
    #                 use_version = get_version_type(r.Path, r.Version)
    #
    #         use_versions.append(use_version)
    #         if r.Version != "":
    #             if use_version == -2:  # TODO(download pkgs from other sources)
    #                 versions.append(r.Revision)
    #
    #             if use_version == -1:
    #                 versions.append(r.Revision)
    #                 print("It should not occur!(where major version doesn't equal to version in module path)")
    #
    #             if use_version == 0:  # no go.mod in dst pkg
    #                 versions.append(r.Version + '+incompatible')
    #
    #             if use_version == 1: # has go.mod but in module path no version suffix
    #                 versions.append(r.Revision)
    #
    #             if use_version >= 2:
    #                 versions

    requires = []
    for r in reference:
        if r.Path == "" or (r.Version == "" and r.Revision == ""):
            print("wrong reference!")
        else:
            if r.Source != "None":
                path = r.Source
            else:
                path = r.Path
            if not re.findall(r'^github.com/', path):  # TODO(download pkgs from other sources)
                if r.Version != "":
                    requires.append(path + ' ' + r.Version)
                else:
                    requires.append(path + ' ' + r.Revision)
            else:
                if r.Version != "":
                    use_version = get_version_type(path, r.Version)
                    if use_version == -1:
                        print("It should not occur!(where major version doesn't equal to version in module path)")

                    if use_version == 0:  # no go.mod in dst pkg
                        requires.append(path + ' ' + r.Version + '+incompatible')

                    if use_version == 1:  # has go.mod but in module path no version suffix
                        requires.append(path + ' ' + r.Revision)

                    if use_version >= 2:
                        requires.append(path + '/' + str(use_version) + ' ' + r.Version)
                else:
                    requires.append(path + ' ' + r.Revision)

    



















