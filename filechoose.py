import os

from fileread import read_in_file


def str_compare(filename):
    if filename == "Gopkg.lock":
        return 1
    if filename == "glide.lock":
        return 2
    return 0


def choose_file(pathname):
    files = os.listdir(pathname)
    target_file_count = 0
    file_type_descriptor = 0
    for file in files:
        if not os.path.isdir(file):
            if str_compare(file) != 0:
                file_type_descriptor = str_compare(file)
                target_file_count = target_file_count + 1
    if target_file_count != 1:
        if target_file_count == 0:
            print("No Configfile found: In " + pathname + " !\n")
        elif target_file_count > 1:
            print("too many possible Configfile found: In " + pathname + " !\n")
    else:
        read_in_file(pathname, file_type_descriptor)