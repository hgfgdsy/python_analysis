from download import DOWNLOAD
from semver import get_major


import os
import re
import shutil


def get_major_in_module(module):
    last = re.findall(r'/v\d+?$', module)
    if not last:
        return -1

    return int(last[0][2:])


def get_local_pkg(path):
    files = os.listdir(path)
    mod_or_not = -1
    m_url = ''
    for file in files:
        if os.path.isfile(os.path.join(path, file)) and file == 'go.mod':
            mod_or_not = 1
            m_url = os.path.join(path, file)
            break

    if mod_or_not == -1:
        return 0

    f = open(m_url)
    go_mod_content = f.read()
    module = re.findall(r"^module\s*(.+?)$", go_mod_content, re.M)
    go_mod_module = ''
    if module:
        go_mod_module = module[0].replace('"', '').strip()
    else:
        go_mod_module = ''
    f.close()

    major_in_module = get_major_in_module(go_mod_module)

    if major_in_module == -1:
        return 1
    else:
        return major_in_module


def get_version_type(name, version):

    major = get_major(version)
    if int(major) < 2:
        return -11

    if version[0] != 'v' and len(version) >= 7:
        version = version[0:7]
    pkg_name = name.replace('/', '=') + '@' + version

    if os.path.isdir('./pkg1/' + pkg_name):
        r_type = get_local_pkg('./pkg1/' + pkg_name)
        if r_type < 2:
            return r_type
        if r_type != 1 and r_type != int(major):
            return -1
        else:
            return r_type

    get_dep = DOWNLOAD([name, version])
    get_dep.down_load_unzip()
    download_result = get_dep.download_result
    cnt = 0
    while download_result == -1:
        shutil.rmtree(get_dep.dst_name)
        get_dep.down_load_unzip()
        download_result = get_dep.download_result
        cnt = cnt + 1
        if cnt > 5:
            break

    if download_result != -1:
        # pkg_name = os.listdir(os.path.join(get_dep.save_name, '1'))[0]
        pkg_name = name.replace('/', '=') + '@' + version
        pkg_path = os.path.join(os.path.join(get_dep.save_name, pkg_name))
        r_type = get_local_pkg(pkg_path)
    else:
        r_type = -10
    # shutil.rmtree(get_dep.dst_name)
    if r_type < 2:
        return r_type
    if r_type != int(major):
        return -1
    else:
        return r_type
