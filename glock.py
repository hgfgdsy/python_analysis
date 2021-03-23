from package_ref import *


def parse_glockfile(file_type_descriptor, data):
    references = []
    lines = data.split('\n')

    for line in lines:
        f = line.split()
        if len(f) >= 2 and f[0] != 'cmd':
            r = pkg()
            r.set_path(f[0])
            if f[1][0] != 'v':
                r.set_revision(f[1])
            else:
                r.set_version(f[1])

            references.append(r)

    return references
