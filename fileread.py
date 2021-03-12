from dep import parse_gopkg_lock


def read_in_file(pathname, file_descriptor):
    if file_descriptor == 1:
        f = open(pathname + "/" + "Gopkg.lock", 'r')
        data = f.read()
        parse_gopkg_lock(file_descriptor, data)
    else:
        f = open(pathname + "/" + "glide.lock", 'r')
        data = f.read()