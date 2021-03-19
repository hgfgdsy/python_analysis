from package_ref import *


def parse_glide_lock(file_type_descriptor, data):
    reference = []
    lineno = 0
    lines = data.split("\n")
    list_length = -1

    imports = False
    name = ""

    for line in lines:
        if line == "":
            continue

        if line.startwith("imports:"):
            imports = True
        elif line[0] != '-' and line[0] != ' ' and line[0] != '\t':
            imports = False

        if not imports:
            continue

        if line.startwith("- name:"):
            name = line[len("- name:"):].strip()

        if line.startwith("  version:"):
            version = line[len("  version:"):].strip()
            if name != "" and version != "":
                another = pkg()
                another.set_path(name)
                another.set_revision(version)
                reference.append(another)

    return reference



