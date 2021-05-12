import os

from fileread import read_in_file
from dep import parse_gopkg_lock
from glide import parse_glide_lock


def str_compare(filename):
    if filename == "Gopkg.lock":
        return 1
    if filename == "glide.lock":
        return 2
    return 0


def choose_file(pathname, module_path):
    files = os.listdir(pathname)
    target_file_count = 0
    file_type_descriptor = 0
    for file in files:
        if not os.path.isdir(file):
            if str_compare(file) != 0:
                file_type_descriptor = str_compare(file)
                target_file_count = target_file_count + 1
    tlp = []
    if target_file_count != 1:
        if target_file_count == 0:
            print("No Configfile found: In " + pathname + " !\n")
        elif target_file_count > 1:
            print("too many possible Configfile found: In " + pathname + " !\n")
    else:
        if file_type_descriptor == 1:
            path = os.path.join(pathname, 'Gopkg.lock')
            f = open(path)
            data = f.read()
            f.close()
            reference = parse_gopkg_lock(file_type_descriptor, data)
            tlp = read_in_file(pathname, file_type_descriptor, reference, module_path)
        elif file_type_descriptor == 2:
            path = os.path.join(pathname, 'glide.lock')
            f = open(path)
            data = f.read()
            f.close()
            reference = parse_glide_lock(file_type_descriptor, data)
            tlp = read_in_file(pathname, file_type_descriptor, reference, module_path)
    return [file_type_descriptor, tlp]