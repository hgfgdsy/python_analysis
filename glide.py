from package_ref import *
from semver import *
import re
import requests
from bs4 import BeautifulSoup


# get hash through version, 获取一个版本对应的哈希值，需要补充一个通过哈希值获取版本的方法 ~~~
def get_hash(url, search_e):
    v_hash = ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "lxml")
        # f6 link-gray text-mono ml-2 d-none d-lg-inline
        div_msg = str(soup.find('a', class_='f6 Link--secondary text-mono ml-2 d-none d-lg-inline'))
        hash_str = re.findall(r"<a href=\"(.+?)\"", div_msg)
        # print(hash_str)
        if hash_str:
            v_hash = hash_str[0]
    except Exception as exp:
        search_e = search_e + 1
        print("get hash error:", exp, "**************************************************")
    return v_hash, search_e


def parse_glide_lock(file_type_descriptor, data):
    reference = []
    lineno = 0
    lines = data.split("\n")
    list_length = -1

    imports = False
    name = ""
    source = ""

    for line in lines:
        if line == "":
            continue

        if line.startswith("imports:"):
            imports = True
        elif line[0] != '-' and line[0] != ' ' and line[0] != '\t':
            imports = False

        if not imports:
            continue

        if line.startswith("- name:"):
            name = line[len("- name:"):].strip()

        if line.startswith("  repo:"):
            tempname = line[len("  repo:"):].strip()
            if re.findall(r'^https://', tempname):
                source = tempname.replace('https://', '').strip()

        if line.startswith("  version:"):
            version = line[len("  version:"):].strip()
            if name != "" and version != "":
                another = pkg()
                another.set_path(name)
                using = name
                if source != "":
                    another.set_source(source)
                    using = source
                    source = ''
                if len(version) != 40:
                    repo_url = "https://github.com/" + name + '/tree/' + version
                    search_e = 0
                    (v_hash, search_e) = get_hash(repo_url, search_e)
                    v_hashi = v_hash.replace('/' + using + '/commit/', '')
                    if not isvalid(version) or canonical(version) != version:
                        if v_hashi != '':
                            another.set_revision(v_hashi)
                        else:
                            another.set_version(version)
                    else:
                        another.set_version(version)
                        if v_hashi != '':
                            another.set_revision(v_hashi)
                else:
                    another.set_revision(version)
                reference.append(another)
    return reference



