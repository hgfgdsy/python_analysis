from package_ref import *


def parse_vendor_conf(file_type_descriptor, data):
    references = []
    lines = data.split('\n')

    for line in lines:
        i = -1
        i = line.find('#')
        if i > 0:
            line = line[:i]

        f = line.split()
        if len(f) >= 2:
            r = pkg()
            i = f[1].find('.')
            if i > 0:
                r.set_version(f[1])
            else:
                r.set_revision(f[1])

            references.append(r)

    return references