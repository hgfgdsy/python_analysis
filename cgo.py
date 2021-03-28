from pip._vendor.distlib.compat import raw_input


def get_module_path():
    mp = raw_input("Module path is : ")
    return mp


def get_go_version():
    vs = raw_input("Go version is : ")
    return vs


def write_go_mod(requires, replaces, reqlist):

    module_path = get_module_path()

    go_version = get_go_version()

    msg = 'module '
    msg = msg + module_path + '\n' + '\n'
    msg = msg + 'go ' + go_version + '\n' + '\n'
    msg = msg + 'require (' + '\n'
    for r in requires:
        msg = msg + r + '\n'

    msg = msg + ')\n'

    msg = msg + '\n'
    msg = msg + 'replace (' + '\n'
    for r in replaces:
        msg = msg + r[0] + ' ' + r[2] + ' => ' + r[1] + ' ' + r[2] + '\n'
    msg = msg + ')\n'
    print(msg)

    f = open('./pkg/hgfgdsy=migtry@v0.0.0/go.mod', 'w')
    f.write(msg)
    f.close()
