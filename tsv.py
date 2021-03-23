from package_ref import *


def parse_dependencies_tsv(file_type_descriptor, data):
    references = []
    lines = data.split('\n')
    for line in lines:
        f = line.split('\t')
        r = pkg()
        r.set_path(f[0])
        r.set_revision(f[2])
        references.append(r)

    return references
