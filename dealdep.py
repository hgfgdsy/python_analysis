import os
import re

import chardet

def get_tool_name_list():
    tool_name_list = ['Godeps.json', 'vendor.conf', 'vendor.json', 'glide.yaml', 'glide.toml', 'Gopkg.toml', 'Godep.json']
    return tool_name_list


def get_tool_name_list_2():
    tool_name_list = ['glide.lock', 'Gopkg.lock']
    return tool_name_list


def deal_dep_version(dep_version):
    dep_version = dep_version.replace('// indirect', '').replace('+incompatible', '').strip()
    not_semantic = re.findall(r"^v\d+?\.\d+?\.\d+?-*[^-]*?-[0-9.]+?-([A-Za-z0-9]+?)$", dep_version)
    not_semantic_2 = re.findall(r"^v\d+?\.\d+?\.\d+?-.+?-([A-Za-z0-9]+?)$", dep_version)
    # bug_main_version = ''
    if not_semantic:
        repo_version = not_semantic[0][0:7]
    else:
        if not_semantic_2:
            repo_version = not_semantic_2[0][0:7]
        else:
            repo_version = dep_version
    return repo_version


def get_mod_require(mod_url, requires_list, replaces_list):
    f = open(mod_url)
    go_mod_content = f.read()
    require_part = go_mod_content.replace('"', '')
    f.close()
    # get all require
    mod_requires = re.findall(r"require\s*\(\n*(.+?)\n*\)", require_part, re.S)  # 括号括起来的requires
    if mod_requires:
        require_l = mod_requires[0].split('\n')
        for require_r in require_l:
            require_r = require_r.strip().replace('+incompatible', '')
            # (not re.findall(r"^[0-9a-zA-Z]+?/[0-9a-zA-Z]+?$", require_r))
            #                 and (not re.findall(r"^[0-9a-zA-Z]+?$", require_r)) and
            if require_r and (not re.findall(r"^//.+?", require_r)) and (require_r not in requires_list):
                requires_list.append(require_r)
                # print(require_r)
    mod_requires = re.findall(r"^require\s+([^(]+?)$", require_part, re.M)  # 不是括号括起来的requires
    for require_r in mod_requires:
        require_r = require_r.strip().replace('+incompatible', '')
        if require_r and (require_r not in requires_list):
            requires_list.append(require_r)
            # print(require_r)
    # get all replace
    mod_replaces = re.findall(r"replace\s*\(\n*(.+?)\n*\)", require_part, re.S)  # 同上理
    if mod_replaces:
        replace_l = mod_replaces[0].split('\n')
        for replace_p in replace_l:
            replace_p = replace_p.strip().replace('+incompatible', '')
            if replace_p and (not re.findall(r"^//.+?", replace_p)):
                replace_rl = re.findall(r"^(.+?)\s", replace_p)
                replace_rr = re.findall(r"=>\s(.+?)$", replace_p)
                if replace_rl and replace_rr and ([replace_rl[0], replace_rr[0]] not in replaces_list):
                    replaces_list.append([replace_rl[0], replace_rr[0]])
                    for r in requires_list:
                        if re.findall(r"^" + replace_rl[0] + r"\s", r):
                            requires_list.remove(r)
                            replace_rr_ind = replace_rr[0] + ' +replace'
                            if (replace_rr[0] not in requires_list) and (replace_rr_ind not in requires_list):
                                requires_list.append(replace_rr_ind)  # +replace
                                # print(replace_rr_ind)
    mod_replaces = re.findall(r"^replace\s+([^(]+?)$", require_part, re.M)
    for replace_r in mod_replaces:
        replace_r = replace_r.strip()
        if replace_r:
            replace_rl = re.findall(r"^(.+?)\s", replace_r)
            replace_rr = re.findall(r"=>\s(.+?)$", replace_r)
            if replace_rl and replace_rr and ([replace_rl[0], replace_rr[0]] not in replaces_list):
                replaces_list.append([replace_rl[0], replace_rr[0]])
                for r in requires_list:
                    if re.findall(r"^" + replace_rl[0] + r"\s", r):
                        requires_list.remove(r)
                        replace_rr_ind = replace_rr[0] + ' +replace'
                        if (replace_rr[0] not in requires_list) and (replace_rr_ind not in requires_list):
                            requires_list.append(replace_rr_ind)  # +replace
                            # print(replace_rr_ind)
    return requires_list, replaces_list


def l_deal_mod(mod_list, repo_url, repo_name):
    mod_dep_list = []
    mod_req_list = []  # require
    mod_rep_list = []  # replace
    mod_cu = ''
    for p in mod_list:
        if re.findall(r"/v\d+?/$", p):  # 在找子目录法迁移后的vN目录，对于windows是不是没考虑，斜杠  uncertain
            path_v = re.findall(r"/v(\d+?)/$", p)[0]
            if int(path_v) >= 2:
                mod_cu = p  # have v_dir
                break
    if not mod_cu:  # 没有subdirectory的话就默认根目录的go.mod
        mod_cu = mod_list[0]
    m_url = repo_url + mod_cu + 'go.mod'
    go_mod_module = ''
    if os.path.isfile(m_url):
        f = open(m_url)
        go_mod_content = f.read()
        module = re.findall(r"^module\s*(.+?)$", go_mod_content, re.M)
        if module:
            go_mod_module = module[0].replace('"', '').strip()
        else:
            go_mod_module = ''
        f.close()
    if not go_mod_module and repo_name:
        go_mod_module = 'github.com/' + repo_name

    for m_url in mod_list:
        url = repo_url + m_url + 'go.mod'

        if os.path.isfile(url):
            (mod_req_list, mod_rep_list) = get_mod_require(url, mod_req_list, mod_rep_list)

    for m in mod_req_list:
        dep = m.replace('+replace', '').replace('// indirect', '').strip().split(' ')
        if len(dep) > 1:
            dep_version = deal_dep_version(dep[1])
            if re.findall(r"\+replace", m) and dep:
                mod_dep_list.append([dep[0], dep_version, 3])  # replace
            elif re.findall(r"// indirect", m) and dep:
                mod_dep_list.append([dep[0], dep_version, 2])  # dep from old repo
            elif dep:
                mod_dep_list.append([dep[0], dep_version, 1])  # normal
    return mod_dep_list, mod_rep_list, go_mod_module


def deal_local_repo(root_url, local_url, go_list, mod_list, tool_list):
    local_list = os.listdir(local_url)
    tool_name_list = get_tool_name_list()
    tool_name_list_2 = get_tool_name_list_2()

    dir_list = []

    for f in local_list:
        n_path = os.path.join(local_url, f)
        n_r_path = n_path.replace(root_url, '')
        if os.path.isdir(n_path) and f != 'vendor':
            dir_list.append(n_path)
        elif os.path.isfile(n_path):
            if re.findall(r"\.go$", f):
                if n_r_path not in go_list:
                    go_list.append(n_r_path)
            elif f == 'go.mod':
                mod_path = n_r_path.replace('go.mod', '').strip()
                if mod_path not in mod_list:
                    mod_list.append(mod_path)
            elif f in tool_name_list:  # tool
                # print(n_r_path)
                if n_r_path not in tool_list:
                    tool_list.append(n_r_path)
            elif f in tool_name_list_2:  # tool 2
                # print(n_r_path)
                if n_r_path not in tool_list:
                    tool_list.append(n_r_path)

    for p in dir_list:
        (go_list, mod_list, tool_list) = deal_local_repo(root_url, p, go_list, mod_list, tool_list)

    return go_list, mod_list, tool_list


def l_deal_tool(repo_tool, repo_url, repo_name):
    return []


def get_requires_from_file(file_url, import_list):
    f = open(file_url, 'rb')
    f_content = f.read()
    f_charInfo = chardet.detect(f_content)
    # print(f_charInfo)

    if not f_charInfo['encoding']:
        file_content = f_content.decode('utf-8', 'ignore')
    elif f_charInfo['encoding'] == 'EUC-TW':
        file_content = f_content.decode('utf-8', 'ignore')
    else:
        file_content = f_content.decode(f_charInfo['encoding'], errors='ignore')
    file_import = re.findall(r"import\s*\(\n(.+?)\n\)", file_content, re.S)
    # print(file_import)
    f.close()
    if file_import:
        i_list = file_import[0].split('\n')
        for imp in i_list:
            imp = imp.strip()
            # 排除库函数
            if (not re.findall(r"^//.+?", imp)) and (not re.findall(r"\"[0-9a-zA-Z]+?/[0-9a-zA-Z]+?\"", imp)) and \
                    (not re.findall(r"\"[0-9a-zA-Z]+?\"", imp)):
                if re.findall(r"\"(.+?)\"", imp):
                    import_path = re.findall(r"\"(.+?)\"", imp)[0].strip()
                    # print(import_path)
                    if import_path not in import_list:
                        import_list.append(import_path)
                        # print(import_path)
    return import_list


def deal_go_files(go_list, repo_url, go_mod_module):
    import_list = []
    for f_url in go_list:
        file_url = repo_url + f_url
        import_list = get_requires_from_file(file_url, import_list)
    delete_list = []
    for i in import_list:
        # if go_mod_module:
        #     delete_list.append(go_mod_module)
        if go_mod_module and re.findall(r"^" + go_mod_module, i):
            delete_list.append(i)
    self_ref = len(delete_list)
    for d in delete_list:
        import_list.remove(d)
    return import_list, self_ref


def get_all_direct_depmod(import_list, mod_dep_list):
    search_e = 0

    direct_dep_list = []


def deal_local_repo_dir(repo_id, repo_name, repo_version):
    go_list = []
    mod_list = []
    tool_list = []

    nd_path = os.path.join('.', 'pkg')
    repo_url = os.path.join(nd_path, repo_id)

    (go_list, mod_list, tool_list) = deal_local_repo(repo_url, repo_url, go_list, mod_list, tool_list)

    mod_num = len(mod_list)
    tool_num = len(tool_list)

    mod_dep_list = []
    tool_dep_list = []
    mod_rep_list = []
    go_mod_module = ''

    if mod_list:
        (mod_dep_list, mod_rep_list, go_mod_module) = l_deal_mod(mod_list, repo_url, repo_name)

    if tool_list:
        repo_tool = tool_list[0]
        tool_dep_list = l_deal_tool(repo_tool, repo_url, repo_name)

    (import_list, self_ref) = deal_go_files(go_list, repo_url, go_mod_module)

    if mod_dep_list and (mod_list[0] == '/' or mod_list == 0):  # '/'就说明是根目录的go.mod文件
        direct_repo_list = get_all_direct_depmod(import_list, mod_dep_list)
    else:
        direct_repo_list = get_all_direct_dep(import_list, tool_dep_list)


def deal_local_repo_dir_fork():
    go_list = []
    mod_list = []
    tool_list = []
    vendor_list = []
    deal_repo_path = './repos/deps/2'
    if not os.path.exists(deal_repo_path):
        os.makedirs(deal_repo_path)
        os.makedirs(mod_dir_name)
        os.makedirs(tool_dir_name)

    # 该调用第二个参数是否不对 bug？
    (go_list, mod_list, tool_list, vendor_list) = deal_local_repo(repo_url, repo_url, go_list, mod_list, tool_list,
                                                                  vendor_list)
    mod_num = len(mod_list)  # $mod_num=2$
    tool_num = len(tool_list)  # $tool_num=3$
    if mod_num > 0:
        mod_list.sort(key=lambda m: len(m), reverse=False)
    if tool_num > 0:
        tool_list.sort(key=lambda t: len(t), reverse=False)
    repo_name = ''
    if re.findall(r"/([^/]+?)@+?$", repo_url):  # 是否应该是/([^/]+?)@.+?$ bug?
        repo_name = re.findall(r"/([^/]+?)@+?$", repo_url)[0].replace('=', '/')
    elif re.findall(r"\\([^\\]+?)@.+?$", repo_url):
        repo_name = re.findall(r"\\([^\\]+?)@.+?$", repo_url)[0].replace('=', '/')
    go_mod_module = ''
    mod_dep_list = []
    l_mod_list = []
    l_tool_list = []
    if mod_list:
        (mod_dep_list, l_mod_list, go_mod_module) = l_deal_mod(mod_list, repo_url, mod_dir_name, repo_name)
    if tool_list:
        l_tool_list = l_deal_tool(tool_list, repo_url, tool_dir_name)

    if not go_mod_module and repo_name:
        go_mod_module = 'github.com/' + repo_name
    (import_list, self_ref) = deal_go_files(go_list, repo_url, go_mod_module)

    if mod_dep_list and (mod_list[0] == '/' or mod_list == 0):  # '/'就说明是根目录的go.mod文件
        direct_repo_list = get_all_direct_depmod(import_list, mod_dep_list)
    else:
        direct_repo_list = get_all_direct_dep(import_list)
    delete_list = []
    this_repo_name = repo_id.split('@')[0].replace('=', '/')
    for dep in direct_repo_list:
        if dep[0] == this_repo_name:
            self_ref = self_ref + 1
            delete_list.append(dep)

    for d in delete_list:
        direct_repo_list.remove(d)
    # 写入文件：
    # $mod_num=2$   $tool_num=3$
    # vendor_list
    # l_mod_list  l_tool_list
    # self_ref
    # go_mod_module
    # direct_repo_list
    if not mod_list:
        go_mod_module = ''
    file_str = '$mod_num=' + str(mod_num) + '$tool_num=' + str(tool_num) + '$self_ref=' + str(self_ref) + '$'
    if go_mod_module:
        file_str = file_str + '*go_mod_module=' + go_mod_module + '*'
    vendor_str = '$vendor:'
    for v in vendor_list:
        vendor_str = vendor_str + v + ';'
    file_str = file_str + vendor_str + '$'
    mod_str = '$go.mod:'
    for lm in l_mod_list:
        mod_str = mod_str + lm + ';'
    file_str = file_str + mod_str + '$'
    tool_str = '$tool:'
    for lt in l_tool_list:
        tool_str = tool_str + lt + ';'
    file_str = file_str + tool_str + '$'
    direct_dep_str = '$direct_dep:'
    for d in direct_repo_list:
        d_str = '['
        for d_s in d:
            if isinstance(d_s, int):
                d_str = d_str + str(d_s) + ','
            else:
                d_str = d_str + d_s + ','
        d_str = d_str.strip(',') + ']'
        direct_dep_str = direct_dep_str + d_str + ';'
    file_str = file_str + direct_dep_str + '$'

    file = open(file_name, 'w')
    file.write(file_str)  # msg也就是下面的Hello world!
    file.close()
    # nd_path = deal_path
    nd_path_2 = os.path.join(nd_path, '@').strip('@')
    if re.findall(r"^" + nd_path + "$", repo_url) \
            or re.findall(r"^" + nd_path_2, repo_url):
        print('+++++++++++++++++++++++++++++++cannot delete: ', repo_url)
    else:
        shutil.rmtree(repo_url)