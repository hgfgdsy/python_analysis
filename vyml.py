from package_ref import *


def parse_vendor_yml(file_type_descriptor, data):
    references = []
    lines = data.split('\n')
    vendors = False
    path = ""
    for line in lines:
        if line == '':
            continue
        if line.startwith("vendors:"):
            vendors = True
        elif line[0] != '-' and line[0] != ' ' and line[0] != '\t':
            vendors = False

        if not vendors:
            continue

        if line.startwith("- path:"):
            path = line[len("- path:"):].stripe()

        if line.startwith("  rev:"):
            rev = line[len("  rev:"):].stripe()
            r = pkg()
            r.set_path(path)
            r.set_revision(rev)
            references.append(r)

    return references
