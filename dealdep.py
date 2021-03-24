import os
import re

import chardet
import pymysql

from fileread import get_db_search, get_db_insert

from dep import parse_gopkg_lock
from glide import parse_glide_lock
from godeps import parse_godeps_json
from glock import parse_glockfile
from tsv import parse_dependencies_tsv
from vconf import parse_vendor_conf
from vyml import parse_vendor_yml
from vjson import parse_vendor_json
from vmanifest import parse_vendor_manifest


def get_tool_dic(tool_list):
    dic = {1: '', 2: '', 3: '', 4: '', 5: '', 6: '', 7: '', 8: '', 9: ''}
    for t in tool_list:
        t = t[1:]
        if t == 'Gopkg.lock':
            dic[1] = t

        if t == 'glide.lock':
            dic[2] = t

        if t == 'Godeps/Godeps.json':
            dic[3] = t

        if t == 'GLOCKFILE':
            dic[4] = t

        if t == 'dependencies.tsv':
            dic[5] = t

        if t == 'vendor.conf':
            dic[6] = t

        if t == 'vendor.yml':
            dic[7] = t

        if t == 'vendor/vendor.json':
            dic[8] = t

        if t == 'vendor/vendor.manifest':
            dic[9] = t

    return dic


def get_tool_name_list():
    tool_name_list = ['Godeps.json', 'vendor.conf', 'vendor.json', 'GLOCKFILE', 'dependencies.tsv', 'vendor.manifest', 'vendor.yml']
    return tool_name_list


def get_tool_name_list_2():
    tool_name_list = ['glide.lock', 'Gopkg.lock']
    return tool_name_list


def check_repo_red_del(old_repo):
    # repo_name_update
    check_db_name = 'repo_name_update'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT now_repo_name FROM " + check_db_name + " WHERE old_repo_name='%s'" % old_repo
    db_check = pymysql.connect(host, user, password, db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print("get redirected repo name from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%')
        print(sql)
        return ''


def get_new_url(old_url):
    # new_web_name
    check_db_name = 'new_web_name'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT now_url FROM " + check_db_name + " WHERE old_url='%s' or " \
                                                   "old_url='%s'" % (old_url, 'github.com/' + old_url)
    db_check = pymysql.connect(host, user, password, db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print("2. get new url from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%')
        print(sql)
        return ''


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
        if os.path.isdir(n_path):
            if f == 'vendor':
                vlist = os.listdir(n_path)  # vendor/vendor.json vendor/vendor.manifest
                for item in vlist:
                    if os.path.isfile(item):
                        if item in tool_name_list:
                            n_rr_path = os.path.join(n_r_path, item)
                            if n_rr_path not in tool_list:
                                tool_list.append(n_rr_path)
            elif f == 'Godeps':
                glist = os.listdir(n_path)  # vendor/vendor.json vendor/vendor.manifest
                for item in glist:
                    if os.path.isfile(item):
                        if item in tool_name_list:
                            n_rr_path = os.path.join(n_r_path, item)
                            if n_rr_path not in tool_list:
                                tool_list.append(n_rr_path)
            else:
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


def l_deal_tool(tool_list, repo_url, repo_name):
    references = []
    rpaths = []
    for tool in tool_list:
        tool = tool[1:]
        path = os.path.join(repo_url, tool)
        f = open(path)
        data = f.read()
        refs = []
        if tool == 'Gopkg.lock':
            refs = parse_gopkg_lock(-1, data)

        if tool == 'glide.lock':
            refs = parse_glide_lock(-1, data)

        if tool == 'Godeps/Godeps.json':
            refs = parse_godeps_json(-1, data)

        if tool == 'GLOCKFILE':
            refs = parse_glockfile(-1, data)

        if tool == 'dependencies.tsv':
            refs = parse_dependencies_tsv(-1, data)

        if tool == 'vendor.conf':
            refs = parse_vendor_conf(-1, data)

        if tool == 'vendor.yml':
            refs = parse_vendor_yml(-1, data)

        if tool == 'vendor/vendor.json':
            refs = parse_vendor_json(-1, data)

        if tool == 'vendor/vendor.manifest':
            refs = parse_vendor_manifest(-1, data)

        if not references:
            for r in refs:
                if r.Path != '':
                    rpaths.append(r.Path)
                    references.append(r)
        else:
            for r in refs:
                if r.Path != '' and r.Path not in rpaths:
                    rpaths.append(r.Path)
                    references.append(r)

    tool_dep_list = []
    for r in references:
        if r.Version != '':
            tool_dep_list.append([r.Path, r.Version])
        else:
            tool_dep_list.append([r.Path, r.Revision])
    return tool_dep_list


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


def get_github_name_db(spec_name):
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT old_url FROM new_web_name WHERE now_url='%s'" % spec_name
    db_check = pymysql.connect(host, user, password, db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # print('This special url have related github url：', check_result[0][0])
            return 1, check_result[0][0]
        else:
            return 0, ''
    except Exception as exp:
        print("1. check new_web_name error:", exp, '-------------------------------------------------------------')
        print(sql)
        return -1, ''


def get_github_name(dep_name):
    siv_path = ''
    git_mod_name = ''
    repo_name = ''
    if re.findall(r"^(gopkg.in/.+?)\.v\d", dep_name):
        # gopkg.in/cheggaaa/pb.v1
        repo_name = re.findall(r"^(gopkg.in/.+?)\.v\d", dep_name)[0]
    siv_path = get_imp_siv_path(dep_name)
    nosiv_path = dep_name.replace(siv_path, '')
    if repo_name:
        (r, git_name) = get_github_name_db(repo_name)
        if git_name:
            git_mod_name = git_name
    else:
        if re.findall(r"^([^/]+?/[^/]+?)$", nosiv_path):
            repo_name = re.findall(r"^([^/]+?/[^/]+?)$", nosiv_path)[0]
        elif re.findall(r"^([^/]+?/[^/]+?)/", nosiv_path):
            repo_name = re.findall(r"^([^/]+?/[^/]+?)/", nosiv_path)[0]
        else:
            repo_name = nosiv_path
        (r, git_name) = get_github_name_db(repo_name)

        if git_name:
            git_mod_name = git_name
    return git_mod_name


def return_repo_name(dep_name):
    dep_name = 'github.com' + dep_name.replace('github.com/', '')
    repo_name = get_git_repo_name(dep_name)
    return repo_name


def get_git_repo_name(dep):
    repo_name = ''
    if re.findall(r"^github.com/([^/]+?/[^/]+?)$", dep):
        repo_name = re.findall(r"^github.com/([^/]+?/[^/]+?)$", dep)[0]
    elif re.findall(r"^github.com/([^/]+?/[^/]+?)/", dep):
        repo_name = re.findall(r"^github.com/([^/]+?/[^/]+?)/", dep)[0]
    return repo_name


def get_imp_siv_path(dep_name):
    siv_path = ''
    if re.findall(r"(/v\d+?)$", dep_name):
        siv_path = re.findall(r"(/v\d+?)$", dep_name)[0]
    elif re.findall(r"(\.v\d+?)$", dep_name):
        siv_path = re.findall(r"(\.v\d+?)$", dep_name)[0]
    elif re.findall(r"(/v\d+?)/", dep_name):
        siv_path = re.findall(r"(/v\d+?)/", dep_name)[0]
    elif re.findall(r"(\.v\d+?)/", dep_name):
        siv_path = re.findall(r"(\.v\d+?)/", dep_name)[0]
    return siv_path


def get_repo_name(dep_name):
    repo_name = ''
    siv_path = get_imp_siv_path(dep_name)
    if re.findall(r"^github.com/", dep_name):
        repo_name = get_git_repo_name(dep_name)
    elif re.findall(r"^go.etcd.io/", dep_name):
        repo_name = dep_name.replace('go.etcd.io/', 'etcd-io/')
        if repo_name != dep_name:
            repo_name = return_repo_name(repo_name)
        else:
            git_name = get_github_name(dep_name)
            # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
            if git_name:
                repo_name = git_name
    elif re.findall(r"^golang.org/x/", dep_name):
        repo_name = dep_name.replace('golang.org/x/', 'golang/')
        if repo_name != dep_name:
            repo_name = return_repo_name(repo_name)
        else:
            git_name = get_github_name(dep_name)
            # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
            if git_name:
                repo_name = git_name
    elif re.findall(r"^gopkg\.in/", dep_name):
        if re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.v\d", dep_name):
            repo_name = re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.v\d", dep_name)[0]
        else:
            if re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.", dep_name):
                repo_name = re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.", dep_name)[0]
            else:
                if re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)/", dep_name):
                    repo_name = re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)/", dep_name)[0]
                else:
                    git_name = get_github_name(dep_name)
                    # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
                    if git_name:
                        repo_name = git_name
    else:
        git_name = get_github_name(dep_name)
        # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
        if git_name:
            repo_name = git_name

    repo_name = repo_name.replace('github.com/', '')
    return repo_name, siv_path


def get_all_direct_dep(import_list, tool_dep_list):
    search_e = 0
    repo_list = []
    # dep_list = []
    direct_repo_list = []
    # siv_path = ''
    # for imp in import_list:
    #     (repo_name, siv_path) = get_repo_name(imp)
    #     if repo_name:
    #         if not re.findall(r"^github.com/", imp):
    #             web_name = get_new_url('github.com/' + repo_name)
    #             if [repo_name, web_name, siv_path, 0] not in repo_list:
    #                 repo_list.append([repo_name, web_name, siv_path, 0])
    #             # if web_name:
    #             #     if web_name not in dep_list:
    #             #         dep_list.append(web_name)
    #             # else:
    #             #     dep_list.append(repo_name)
    #         else:
    #             now_name = check_repo_red_del(repo_name)
    #             if not now_name and now_name != '0':
    #                 if [repo_name, '', siv_path, 0] not in repo_list:
    #                     repo_list.append([repo_name, '', siv_path, 0])
    #                     # print('get_all_direct_dep方法:', [repo_name, ''])
    #             else:
    #                 if [now_name, repo_name, siv_path, 1] not in repo_list:
    #                     repo_list.append([now_name, repo_name, siv_path, 1])

    direct_dep_list = []
    for imp in import_list:
        (repo_name, siv_path) = get_repo_name(imp)
        ver = ''
        for r in tool_dep_list:
            if r.Path == imp:
                if r.Version != '':
                    ver = r.Version
                else:
                    ver = r.Revision

        if ver != '':
            direct_dep_list.append([repo_name, ver, imp, siv_path])

    return direct_dep_list


def deal_local_repo_dir(repo_id, tag, references):
    go_list = []
    mod_list = []
    tool_list = []

    nd_path = os.path.join('.', 'pkg')
    repo_url = os.path.join(nd_path, repo_id)

    (go_list, mod_list, tool_list) = deal_local_repo(repo_url, repo_url, go_list, mod_list, tool_list)

    mod_num = len(mod_list)
    tool_num = len(tool_list)

    repo_name = ''
    if re.findall(r"/([^/]+?)@+?$", repo_url):  # 是否应该是/([^/]+?)@.+?$ bug?
        repo_name = re.findall(r"/([^/]+?)@+?$", repo_url)[0].replace('=', '/')
    elif re.findall(r"\\([^\\]+?)@.+?$", repo_url):
        repo_name = re.findall(r"\\([^\\]+?)@.+?$", repo_url)[0].replace('=', '/')

    mod_dep_list = []
    tool_dep_list = []
    mod_rep_list = []
    go_mod_module = ''

    if tag == 1:
        (import_list, self_ref) = deal_go_files(go_list, repo_url, go_mod_module)
        direct_repo_list = get_all_direct_dep(import_list, references)
        return direct_repo_list
    else:
        if mod_list:
            (mod_dep_list, mod_rep_list, go_mod_module) = l_deal_mod(mod_list, repo_url, repo_name)

        if tool_list:
            tool_dep_list = l_deal_tool(tool_list, repo_url, repo_name)
