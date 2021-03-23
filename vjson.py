from package_ref import *
from ctypes import cdll, c_char_p


def parse_vendor_json(file_type_descriptor, data):
    references = []
    lib = cdll.LoadLibrary('./dc.o')

    lib.Vjsonsup.argtype = c_char_p
    lib.Vjsonsup.restype = c_char_p

    out = lib.Vjsonsup(bytes(data, encoding="utf8"))
    ss = out.decode("utf-8").split('\n')
    for rr in ss:
        f = rr.split()
        r = pkg()
        r.set_path(f[0])
        r.set_revision(f[1])
        references.append(r)

    return references
