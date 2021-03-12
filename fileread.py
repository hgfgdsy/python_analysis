from dep import parse_gopkg_lock


def read_in_file(pathname, file_type_descriptor):
    if file_type_descriptor == 1:
        f = open(pathname + "/Gopkg.lock")
        data = f.read()
        parse_gopkg_lock(file_type_descriptor, data)
    else:
        f = open(pathname + "/glide.lock")
        data = f.read()