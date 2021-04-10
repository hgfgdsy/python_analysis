from dep import parse_gopkg_lock
from cgo import write_go_mod
import re
from suffix import get_version_type, get_major

import requests
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import json
import random
import pymysql

from dealdep import deal_local_repo_dir, get_db_search, get_db_insert

from missing import *
import os

import subprocess

from dealdep import get_mod_require, deal_dep_version, get_repo_name
from download import *
import hashlib


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    return result


def get_token():  # download 重复
    # token 0a6cca72aa3cc98993950500c87831bfef7e5707 [meng] Y
    # token ad418c5441a67ad8b2c95188e131876c6a1187fe [end] x
    # token abdd967d350662632381f130cd62268ed2f961a1 [end] x
    # token ff4e63b2dba8febac0aeb59aa3b8829a05de97e7 [hu] x
    # token a41ca9587818fc355b015376e814df47223fc136 [me] x

    # token a8ad3ffb79d2ef67a1f19da8245ff361e624dc20 [ql] x
    # token 6f8454c973d4f7f07a57c2982db79d2ce543403d [zs] x
    # token 3e87d1e3a489815cdf597a10b426ad1e2a7426db [zs]
    # token 24748c727dfbcbfa18c3478f495c2b8b6ed1703e [ql]

    # token_list = ['0a6cca72aa3cc98993950500c87831bfef7e5707', '24748c727dfbcbfa18c3478f495c2b8b6ed1703e',
    #               '3e87d1e3a489815cdf597a10b426ad1e2a7426db']
    # index_num = random.randint(0, 2)
    # return token_list[index_num]

    return '2dcf8df8093697b00207ec01051847f269987e33'


def get_headers():
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
    #            'Content-Type': 'application/json', 'Accept': 'application/json'}
    token = get_token()
    token_str = 'token ' + token
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json', 'Accept': 'application/json',
               'Authorization': token_str}
    # headers_2 = {'User-Agent': 'Mozilla/5.0',
    #              'Content-Type': 'application/json', 'Accept': 'application/json',
    #              'Authorization': 'token a8ad3ffb79d2ef67a1f19da8245ff361e624dc20'}
    # headers_3 = {'User-Agent': 'Mozilla/5.0',
    #              'Content-Type': 'application/json', 'Accept': 'application/json',
    #              'Authorization': 'token 0a6cca72aa3cc98993950500c87831bfef7e5707'}
    return headers


def get_last_version(fullname):
    headers = get_headers()
    repo_name_list = fullname.split('/')
    repo_name = repo_name_list[0] + '/' + repo_name_list[1]
    subdir_name = ''
    c = 0
    for n in repo_name_list:
        c = c + 1
        if c > 2:
            subdir_name = subdir_name + '/' + n
    if subdir_name:
        # print('1.:', repo_name, subdir_name, '************************************get_releases_url*******')
        d_url = 'https://api.github.com/repos/' + repo_name
    else:
        d_url = 'https://api.github.com/repos/' + fullname
    try:
        one_page_results = get_results(d_url, headers)
        releases_url = one_page_results['releases_url']
        (v_name, semantic) = get_version(releases_url)
    except Exception as exp:
        print("************** get search releases_url error", exp, '*******************************************')
        v_name = 'master'
        semantic = False
    return v_name, semantic


def get_version(releases_url):
    headers = get_headers()
    v_url = releases_url.replace('{/id}', '')
    version_result = get_results(v_url, headers)
    # v_id = ''
    v_name = ''
    semantic = True
    if version_result:
        v_url = releases_url.replace('{/id}', '/latest')
        try:
            result = get_results(v_url, headers)
        except Exception as exp:
            result = version_result[0]
            print("When find version: get search error", exp, '-------------------------------------------------------')
        v_name = result['tag_name']
    else:
        semantic = False
    return v_name, semantic


def get_last_hash(repo_name):
    repo_name_list = repo_name.split('/')
    fullname = repo_name_list[0] + '/' + repo_name_list[1]
    # https://api.github.com/repos/robfig/cron/commits
    url = 'https://api.github.com/repos/' + fullname + '/commits'
    headers = get_headers()
    try:
        commts = get_results(url, headers)
        last_commt = commts[0]["sha"][0:7]
        # print('%%%%get the last commit hash is:', last_commt, fullname)
    except Exception as exp:
        last_commt = ''
        print("************** get search releases_url error", exp, '*******************************************')
    return last_commt


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
        div_msg = str(soup.find('a', class_='f6 link-gray text-mono ml-2 d-none d-lg-inline'))
        div_msg = div_msg.strip('').replace('\n', '')
        # print(div_msg)
        hash_str = re.findall(r">([0-9a-zA-Z]+?)</a>", div_msg)
        # print(hash_str)
        if hash_str:
            v_hash = hash_str[0]
    except Exception as exp:
        search_e = search_e + 1
        print("get hash error:", exp, "**************************************************")
    return v_hash, search_e


def get_last_version_or_hashi(repo_name, search_e):
    v_name = ''
    v_hashi = ''
    (v_name, semantic) = get_last_version(repo_name)
    if not semantic:
        v_hashi = get_last_hash(repo_name)
    else:
        url = "https://github.com/" + repo_name + '/tree/' + v_name
        (v_hash, search_e) = get_hash(url, search_e)
    return v_name, v_hashi, search_e


def check_repo_exist_web(repo_name):
    url = 'https://github.com/' + repo_name.replace('github.com/', '').strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "lxml")
        str_all = str(soup)
        # f6 link-gray text-mono ml-2 d-none d-lg-inline
        # main = str(soup.find('body'))
        div_msg = str_all.strip('').replace('\n', '')
        # print(div_msg)
        error_str = re.findall(r"https://github.githubassets.com/_error.js", div_msg)
        notfound_str = re.findall(r"Not Found", div_msg)
        # print(hash_str)
        if error_str or notfound_str:
            repo_exit = -1
        else:
            repo_exit = 1
    except Exception as exp:
        repo_exit = 0
        print("get repo error:", exp, "**************************************************")
    return repo_exit


def check_version_exist(repo_name, repo_version):
    url = 'https://github.com/' + repo_name.replace('github.com/', '').strip() + '/tree/' + repo_version.strip()
    # print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "lxml")
        # f6 link-gray text-mono ml-2 d-none d-lg-inline
        # main = str(soup.find('body'))
        main = str(soup)
        div_msg = main.strip('').replace('\n', '')
        # print(div_msg)
        hash_str = re.findall(r"https://github.githubassets.com/_error.js", div_msg)
        notfound_str = re.findall(r"Not Found", div_msg)
        # print(hash_str)
        if hash_str or notfound_str:
            repo_exit = -1
        else:
            repo_exit = check_repo_exist_web(repo_name)
            if repo_exit == 1:
                repo_exit = -2
            elif repo_exit == -1:
                repo_exit = -1
    except Exception as exp:
        repo_exit = 0
        print("get repo error:", exp, "**************************************************")
    return repo_exit


def check_repo_exist(repo_name):
    # print('check_repo_exit', repo_name, type(repo_name))
    repo_name = repo_name.replace('github.com/', '')
    repo_name = repo_name.strip()
    repo_exit = check_repo_exist_web(repo_name)
    if repo_exit == 0:
        repo_url = 'https://api.github.com/repos/' + repo_name
        headers = get_headers()
        try:
            repo_exit = 1
            page_detail = get_results(repo_url, headers)
            if 'message' in page_detail:
                if page_detail['message'] == 'Not Found':
                    repo_exit = -1
        except Exception as exp:
            repo_exit = -1
            print("The repo name is not correct: ", exp, '**************************************************')
    return repo_exit


def check_repo_valid(in_repo_name, in_version):
    insert_error = 0
    in_repo_name = in_repo_name.replace('github.com/', '')
    repo_exit = check_version_exist(in_repo_name, in_version)
    # print('check_repo_version_exit_web: ', repo_exit)
    if repo_exit == 0 or repo_exit < 0:
        repo_url = 'https://api.github.com/repos/' + in_repo_name + '/contents?ref=' + in_version
        # print(repo_url)
        headers = get_headers()
        # print(headers)
        try:
            insert_error = 0
            page_detail = get_results(repo_url, headers)
        except Exception as exp:

            print("Maybe cannot find version: ", exp, '**************************************************')
            repo_url = 'https://api.github.com/repos/' + in_repo_name
            try:
                page_detail = get_results(repo_url, headers)
                insert_error = 2
                print(in_repo_name, insert_error, 'The repo version name is not correct!')
            except Exception as exp:
                insert_error = 1
                print(in_repo_name, insert_error, 'The repo name is not correct:', exp, '*************************')
    else:
        insert_error = 0
    # print('check_insert_mes', insert_error)
    return insert_error


def check_repo_db_v_name(repo_name, repo_version):
    check_db_name = 'repo'
    (host, user, password, db_name) = get_db_insert()
    # sql = "SELECT * FROM " + check_db_name + " LIMIT 5"
    # sql = "SHOW FULL COLUMNS FROM " + check_db_name
    sql = "SELECT * FROM " + check_db_name + " WHERE repo_name = '%s' AND v_name = '%s'" % (repo_name, repo_version)
    db_check = pymysql.connect(host=host, user=user, password=password, database=db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return check_result
        else:
            return
    except Exception as exp:
        print(check_db_name, " error",
              exp, '%%%%%%%%%%%%%')
        return


def check_repo_db_v_hash(repo_name, repo_hash):
    check_db_name = 'repo'
    (host, user, password, db_name) = get_db_insert()
    # sql = "SELECT * FROM " + check_db_name + " LIMIT 5"
    # sql = "SHOW FULL COLUMNS FROM " + check_db_name
    sql = "SELECT * FROM " + check_db_name + " WHERE repo_name = '%s' AND v_hash = '%s'" % (repo_name, repo_hash)
    db_check = pymysql.connect(host=host, user=user, password=password, database=db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return check_result
        else:
            return
    except Exception as exp:
        print(check_db_name, " error",
              exp, '%%%%%%%%%%%%%')
        return


def check_repo_db_for_valid(repo_name, repo_version, repo_hash):
    if repo_version == "":
        r = check_repo_db_v_name(repo_name, repo_version)
    else:
        r = check_repo_db_v_hash(repo_name, repo_hash)

    if r:
        return 0
    else:
        return -1


def get_redirect_repo(old_repo):
    # repo_name_update
    check_db_name = 'repo_name_update'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT now_repo_name FROM " + check_db_name + " WHERE now_repo_name!='0' and old_repo_name='%s'" % old_repo
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
              exp, '%%%%%%%%%%%%%')
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


def get_diffs(reqlist, all_direct_r, all_direct_dep):
    requires = []
    replaces = []
    mod_dep_list = []
    diffs = []
    (requires, replaces) = get_mod_require('./pkg/hgfgdsy=migtry@v0.0.0/go.mod', requires, replaces)

    for m in requires:
        dep = m.replace('+replace', '').replace('// indirect', '').strip().split(' ')
        if len(dep) > 1:
            dep_version = deal_dep_version(dep[1])
            if re.findall(r"\+replace", m) and dep:
                mod_dep_list.append([dep[0], dep_version, 3])  # replace
            elif re.findall(r"// indirect", m) and dep:
                mod_dep_list.append([dep[0], dep_version, 2])  # dep from old repo
            elif dep:
                mod_dep_list.append([dep[0], dep_version, 1])  # normal

    for d in mod_dep_list:
        repo = d[0]
        ver = d[1]
        rec = None
        recver = ''
        for r in reqlist:
            vr = r[1]
            if vr[0] != 'v':
                vr = vr[0:7]
            if r[0] == repo:
                rec = r
                if vr == ver:
                    recver = vr

        if rec is None:  # a new dependency
            diffs.append([d, 1])
        else:
            if recver == '':
                diffs.append([d, 2])

    return diffs


def out_to_list(a, b):
    lines = b.split('\n')
    lines = lines[2:]
    chain = []
    for line in lines:
        if line != '':
            chain.append(line)
    return chain


def download_a_repo(repo, version):
    if not re.findall(r'^github.com/', repo):
        (repo_name, siv_path) = get_repo_name(repo)
    else:
        repo_name = repo.replace('github.com/', '')

    if repo_name == '':
        return [1, '']

    pkg_name = repo_name.replace('/', '=') + '@' + version
    if os.path.isdir('./pkg/' + pkg_name):
        return [0, pkg_name]
    get_dep = DOWNLOAD([repo_name, version])
    get_dep.down_load_unzip()
    download_result = get_dep.download_result
    if download_result == -1:
        return [-1, '']
    return [0, pkg_name]


def write_modify_to_mod(modifies):
    repos = []
    dic = {}
    for m in modifies:
        repos.append(m[0])
        dic[m[0]] = m[1]
    f = open('./pkg/hgfgdsy=migtry@v0.0.0/go.mod', 'r')

    go_mod_content = f.read()
    require_part = go_mod_content.replace('"', '')
    f.close()
    requires_list = []
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


    ansr = []
    for r in requires_list:
        temp = r.split()
        if temp[0] in repos:
            msg = temp[0] + ' ' + dic[temp[0]]
            ansr.append(msg)
        else:
            ansr.append(r)


    tag = 0
    msg = ''
    lines = go_mod_content.split('\n')
    for line in lines:

        if re.findall(r'^require\s*', line):
            tag = 1

        if tag == 0:
            msg = msg + line + '\n'

        if tag == 1:
            if re.findall(r"^replace", line):
                tag = 2
                msg = msg + 'require' + ' (' + '\n'
                for r in ansr:
                    msg = msg + r + '\n'
                msg = msg + ')\n'
            else:
                continue
        if tag == 2:
            msg = msg + line + '\n'
    f = open('./pkg/hgfgdsy=migtry@v0.0.0/go.mod', 'w')
    f.write(msg)
    f.close()

    # get all require
    # mod_requires = re.findall(r"require\s*\(\n*(.+?)\n*\)", require_part, re.S)  # 括号括起来的requires
    # if mod_requires:
    #     require_l = mod_requires[0].split('\n')
    #     for require_r in require_l:
    #         require_r = require_r.strip().replace('+incompatible', '')
    #
    #         # (not re.findall(r"^[0-9a-zA-Z]+?/[0-9a-zA-Z]+?$", require_r))
    #         #                 and (not re.findall(r"^[0-9a-zA-Z]+?$", require_r)) and
    #         if require_r and (not re.findall(r"^//.+?", require_r)):
    #             rp = require_r[0]
    #             if rp in repos:
    #
    #             # print(require_r)
    # mod_requires = re.findall(r"^require\s+([^(]+?)$", require_part, re.M)  # 不是括号括起来的requires
    # for require_r in mod_requires:
    #     require_r = require_r.strip().replace('+incompatible', '')
    #     if require_r and (require_r not in requires_list):
    #         requires_list.append(require_r)


def hash_name(repo):
    sha1 = hashlib.sha1()
    sha1.update(repo)
    return sha1.hexdigest()


def read_in_file(pathname, file_type_descriptor):
    dic_rec_ver = {}
    errors = []
    replaces = []
    if file_type_descriptor == 1:
        path = os.path.join(pathname, 'Gopkg.lock')
        f = open(path)
        data = f.read()
        reference = parse_gopkg_lock(file_type_descriptor, data)
        repo_id = re.findall(r'/([^/]+?)$', pathname)[0]

        requires = []
        reqlist = []
        upgrade_list = []

        (all_direct_r, all_direct_dep) = deal_local_repo_dir(repo_id, 1, reference)
        count = 0
        for d in all_direct_dep:
            r = all_direct_r[count]
            count = count + 1
            origin_repo_name = d[2]
            github_repo_name = d[0]
            if r.Version != '':
                if d[4] != '':
                    github_repo_name = d[4]
                    replaces.append((origin_repo_name, r.Source, r.Version))
                    requires.append(origin_repo_name + ' ' + r.Version)
                    reqlist.append([origin_repo_name, r.Version])
                    continue

                path = 'github.com/' + github_repo_name

                if github_repo_name != '':
                    valid = check_repo_db_for_valid(github_repo_name, r.Version, "")
                    if valid == -1:
                        valid = check_repo_valid(path, r.Version)

                    new_path = ''
                    if valid == 1:
                        new_path = get_redirect_repo(github_repo_name)
                        if new_path == '':
                            new_path = get_new_url(path)
                        else:
                            replaces.append((origin_repo_name, 'github.com/' + new_path, r.Version))
                            valid = 0

                        if new_path == '':
                            err = MessageMiss(origin_repo_name, r.Version, 1, file_type_descriptor)
                            errors.append(err)
                            continue

                        elif valid != 0:
                            replaces.append((origin_repo_name, new_path, r.Version))
                            valid = 0

                    if valid == 2:
                        err = MessageMiss(origin_repo_name, r.Version, 2, file_type_descriptor)
                        errors.append(err)

                    if valid != 0:
                        valid = check_repo_db_for_valid(origin_repo_name, "", r.Revision)

                        if valid == -1:
                            valid = check_repo_valid(path, r.Revision)

                        new_path = ''
                        if valid == 1:
                            new_path = get_redirect_repo(github_repo_name)
                            if new_path == '':
                                new_path = get_new_url(path)
                            else:
                                replaces.append((origin_repo_name, 'github.com/' + new_path, r.Revision))
                                valid = 0

                            if new_path == '':
                                err = MessageMiss(origin_repo_name, r.Revision, 1, file_type_descriptor)
                                errors.append(err)
                            elif valid != 0:
                                replaces.append((origin_repo_name, new_path, r.Revision))
                                valid = 0

                        if valid == 2:  # TODO get last version here
                            (v_name, v_hash, search_e) = get_last_version_or_hashi(github_repo_name, 0)
                            if v_name != '':
                                requires.append(origin_repo_name + ' ' + v_name)
                                reqlist.append([origin_repo_name, v_name])
                                err = MessageMiss(origin_repo_name, v_name, 3, file_type_descriptor)
                                errors.append(err)
                                continue
                            elif v_hash != '':
                                requires.append(origin_repo_name + ' ' + v_hash)
                                reqlist.append([origin_repo_name, v_hash])
                                err = MessageMiss(origin_repo_name, v_hash, 3, file_type_descriptor)
                                errors.append(err)
                                continue

                        if valid == 0:
                            requires.append(origin_repo_name + ' ' + r.Revision)
                            reqlist.append([origin_repo_name, r.Revision])
                            continue
                        else:
                            err = MessageMiss(origin_repo_name, r.Revision, 4, file_type_descriptor)
                            errors.append(err)
                            continue

                    use_version = get_version_type(github_repo_name, r.Version)
                    if use_version == -11:
                        requires.append(origin_repo_name + ' ' + r.Version)
                        reqlist.append([origin_repo_name, r.Version])

                    if use_version == -10:
                        err = MessageMiss(origin_repo_name, r.Version, -10, file_type_descriptor)
                        errors.append(err)
                        requires.append(origin_repo_name + ' ' + r.Revision)
                        reqlist.append([origin_repo_name, r.Revision])

                    if use_version == -1:
                        print("It should not occur!(where major version doesn't equal to version in module path)")

                    if use_version == 0:  # no go.mod in dst pkg
                        requires.append(origin_repo_name + ' ' + r.Version + '+incompatible')
                        reqlist.append([origin_repo_name, r.Version])

                    if use_version == 1:  # has go.mod but in module path no version suffix
                        i = re.findall(r'gopkg.in/', origin_repo_name)
                        if not i:
                            requires.append(origin_repo_name + ' ' + r.Revision)
                            reqlist.append([origin_repo_name, r.Revision])
                        else:
                            requires.append(origin_repo_name + ' ' + r.Version)
                            reqlist.append([origin_repo_name, r.Version])

                    if use_version >= 2:
                        requires.append(origin_repo_name + '/' + 'v' + str(use_version) + ' ' + r.Version)
                        reqlist.append([origin_repo_name, r.Version])
                else:
                    requires.append(origin_repo_name + ' ' + r.Version)
                    reqlist.append([origin_repo_name, r.Version])
            else:
                if d[4] != '':
                    github_repo_name = d[4]
                    replaces.append((origin_repo_name, r.Source, r.Revision))
                    requires.append(origin_repo_name + ' ' + r.Revision)
                    reqlist.append([origin_repo_name, r.Revision])
                    continue

                path = 'github.com/' + github_repo_name

                if github_repo_name != '':
                    valid = check_repo_db_for_valid(github_repo_name, "", r.Revision)

                    if valid == -1:
                        valid = check_repo_valid(path, r.Revision)

                    new_path = ''
                    if valid == 1:
                        new_path = get_redirect_repo(github_repo_name)
                        if new_path == '':
                            new_path = get_new_url(path)
                        else:
                            replaces.append((origin_repo_name, 'github.com/' + new_path, r.Revision))
                            valid = 0

                        if new_path == '':
                            err = MessageMiss(origin_repo_name, r.Revision, 1, file_type_descriptor)
                            errors.append(err)
                        elif valid != 0:
                            replaces.append((origin_repo_name, new_path, r.Revision))
                            valid = 0

                    if valid == 2:  # TODO get latest version or hash here
                        (v_name, v_hash, search_e) = get_last_version_or_hashi(github_repo_name, 0)
                        if v_name != '':
                            requires.append(origin_repo_name + ' ' + v_name)
                            reqlist.append([origin_repo_name, v_name])
                            err = MessageMiss(origin_repo_name, v_name, 3, file_type_descriptor)
                            errors.append(err)
                            continue
                        elif v_hash != '':
                            requires.append(origin_repo_name + ' ' + v_hash)
                            reqlist.append([origin_repo_name, v_hash])
                            err = MessageMiss(origin_repo_name, v_hash, 3, file_type_descriptor)
                            errors.append(err)
                            continue

                    if valid != 0:
                        err = MessageMiss(origin_repo_name, r.Revision, 4, file_type_descriptor)
                        errors.append(err)
                        continue
                    requires.append(origin_repo_name + ' ' + r.Revision)
                    reqlist.append([origin_repo_name, r.Revision])
                else:
                    requires.append(origin_repo_name + ' ' + r.Revision)
                    reqlist.append([origin_repo_name, r.Revision])

        for r in reference:
            if r not in all_direct_r:
                if r.Source != '':
                    path = r.Path
                    if r.Version != '':
                        replaces.append((r.Path, r.Source, r.Version))
                    else:
                        replaces.append((r.Path, r.Source, r.Revision))
                else:
                    path = r.Path

                if r.Version != '':
                    major = get_major(r.Version)
                    if int(major) >= 2:
                        if re.findall(r'$github\.com/', r.Source):
                            use_version = get_version_type(r.Source, r.Version)
                            if use_version < 2:
                                requires.append(path + ' ' + r.Version)
                                reqlist.append([path, r.Version])
                    else:
                        requires.append(path + ' ' + r.Version)
                        reqlist.append([path, r.Version])
                elif r.Revision != '':
                    requires.append(path + ' ' + r.Revision)
                    reqlist.append([path, r.Revision])

        # TODO write a initial go.mod
        write_go_mod(requires, replaces, reqlist)

        (a, b) = subprocess.getstatusoutput('cd pkg/hgfgdsy=migtry@v0.0.0 && go mod tidy')

        print(b)

        diffs = get_diffs(reqlist, all_direct_r, all_direct_dep)

        modifies = []

        for dif in diffs:  # 可以优化
            after = dif[0]
            diff_type = dif[1]
            print(after[0])
            (a, b) = subprocess.getstatusoutput('cd pkg/hgfgdsy=migtry@v0.0.0 && go mod why ' + after[0])
            print(a, b)
            chain = out_to_list(a, b)  # chain is start with the project itself
            length = len(chain)

            now_dep_list = []

            for d in all_direct_dep:
                now_dep_list.append([d[2], d[1]])
            if diff_type == 1:
                rec_name = ''
                rec_version = ''
                cnt = 0
                for repo in chain:
                    ver = ''
                    for d in now_dep_list:
                        if d[0] == repo:
                            ver = d[1]
                            break
                    if ver == '':
                        err = MessageMiss(repo, chain[0], 5, file_type_descriptor)
                        errors.append(err)
                        break
                    else:
                        cnt = cnt + 1
                        rec_name = repo
                        rec_version = ver
                        if cnt >= length:
                            break
                        hname = str(hash_name(repo))
                        if hname in dic_rec_ver.keys():
                            now_dep_list = dic_rec_ver[hname]
                        else:
                            ret = download_a_repo(repo, ver)
                            if ret[0] != 0:
                                err = MessageMiss(repo, chain[0], 6, file_type_descriptor)
                                errors.append(err)
                                break

                            all_deps = deal_local_repo_dir(ret[1], 2, [])
                            dic_rec_ver[hname] = all_deps
                            now_dep_list = all_deps

                if rec_name != '' and rec_version != '':
                    if rec_version != after[1]:
                        print(rec_name)
                        modifies.append([rec_name, rec_version])
            else:
                rec_name = ''
                rec_version = ''
                cnt = 0
                for repo in chain:
                    ver = ''
                    for d in now_dep_list:
                        if d[0] == repo:
                            ver = d[1]
                            break
                    if ver == '':
                        err = MessageMiss(repo, chain[0], 5, file_type_descriptor)
                        errors.append(err)
                        break
                    else:
                        cnt = cnt + 1
                        rec_name = repo
                        rec_version = ver
                        if cnt >= length:
                            break
                        hname = str(hash_name(repo))
                        if hname in dic_rec_ver.keys():
                            now_dep_list = dic_rec_ver[hname]
                        else:
                            ret = download_a_repo(repo, ver)
                            if ret[0] != 0:
                                err = MessageMiss(repo, chain[0], 6, file_type_descriptor)
                                errors.append(err)
                                break

                            all_deps = deal_local_repo_dir(ret[1], 2, [])
                            dic_rec_ver[hname] = all_deps
                            now_dep_list = all_deps

                if rec_name != '' and rec_version != '':
                    if rec_version != after[1]:
                        print(rec_name)
                        err = MessageMiss(rec_name, rec_version, 7, file_type_descriptor)
                        errors.append(err)
                        modifies.append([rec_name, rec_version])

                write_modify_to_mod(modifies)
                # version = after[1]
                # for repo in chain:
                #     ret = download_a_repo(repo, version)
                #     if ret[0] != 0:
                #         err = MessageMiss(repo, version, 3)
                #         errors.append(err)
                #         break
                #
                #     all_deps = deal_local_repo_dir(ret[1], 2, [])
                #     ver = ''
                #     for r in all_deps:
                #         if r[0] == repo:
                #             if r[1] != '':
                #                 ver = r[1]










        #
        # requires = []
        # for r in reference:
        #     if r.Path == "" or (r.Version == "" and r.Revision == ""):
        #         print("wrong reference!")
        #     else:
        #         if r.Source != "":  # source should be replace
        #             path = r.Source
        #             if r.Version == "":
        #                 replaces.append((r.Path, r.Source, r.Revision))
        #             else:
        #                 replaces.append((r.Path, r.Source, r.Version))
        #         else:
        #             path = r.Path
        #
        #         all_direct_dep = deal_local_repo_dir()
        #         if not re.findall(r'^github.com/', path):  # TODO(download/check pkgs from other sources)
        #             if r.Version != "":
        #                 requires.append(path + ' ' + r.Version)
        #             else:
        #                 requires.append(path + ' ' + r.Revision)
        #         else:
        #             if r.Version != "":
        #                 valid = check_repo_db_for_valid(path.replace('github.com/', ''), r.Version, "")
        #                 if valid == -1:
        #                     valid = check_repo_valid(path, r.Version)
        #
        #                 new_path = ''
        #                 if valid == 1:
        #                     new_path = get_redirect_repo(path.replace('github.com/', ''))
        #                     if new_path == '':
        #                         new_path = get_new_url(path)
        #                     else:
        #                         replaces.append((path, 'github.com/' + new_path, r.Version))
        #                         valid = 0
        #
        #                     if new_path == '':
        #                         err = MessageMiss(path, r.Version, 1)
        #                         errors.append(err)
        #                     elif valid != 0:
        #                         replaces.append((path, new_path, r.Version))
        #                         valid = 0
        #
        #                 if valid == 2:
        #                     err = MessageMiss(path, r.Version, 2)
        #                     errors.append(err)
        #
        #                 if valid != 0:
        #                     valid = check_repo_db_for_valid(path, "", r.Revision)
        #
        #                     if valid == -1:
        #                         valid = check_repo_valid(path, r.Revision)
        #
        #                     new_path = ''
        #                     if valid == 1:
        #                         new_path = get_redirect_repo(path.replace('github.com/', ''))
        #                         if new_path == '':
        #                             new_path = get_new_url(path)
        #                         else:
        #                             replaces.append((path, 'github.com/' + new_path, r.Revision))
        #                             valid = 0
        #
        #                         if new_path == '':
        #                             err = MessageMiss(path, r.Revision, 1)
        #                             errors.append(err)
        #                         elif valid != 0:
        #                             replaces.append((path, new_path, r.Revision))
        #                             valid = 0
        #
        #                     if valid == 2:
        #                         err = MessageMiss(path, r.Revision, 2)
        #                         errors.append(err)
        #
        #                     if valid == 0:
        #                         requires.append(path + ' ' + r.Revision)
        #                         continue
        #                     else:
        #                         continue
        #
        #                 use_version = get_version_type(path, r.Version)
        #                 if use_version == -11:
        #                     requires.append(path + ' ' + r.Version)
        #
        #                 if use_version == -10:
        #                     err = MessageMiss(path, r.Version, 10)
        #                     requires.append(path + ' ' + r.Revision)
        #
        #                 if use_version == -1:
        #                     print("It should not occur!(where major version doesn't equal to version in module path)")
        #
        #                 if use_version == 0:  # no go.mod in dst pkg
        #                     requires.append(path + ' ' + r.Version + '+incompatible')
        #
        #                 if use_version == 1:  # has go.mod but in module path no version suffix
        #                     requires.append(path + ' ' + r.Revision)
        #
        #                 if use_version >= 2:
        #                     requires.append(path + '/' + 'v' + str(use_version) + ' ' + r.Version)
        #             else:
        #                 valid = check_repo_db_for_valid(path.replace('github.com/', ''), "", r.Revision)
        #
        #                 if path == 'github.com/caicloud/cyclone':
        #                     print(valid)
        #                 if valid == -1:
        #                     valid = check_repo_valid(path, r.Revision)
        #
        #                 if path == 'github.com/caicloud/cyclone':
        #                     print(valid)
        #
        #                 new_path = ''
        #                 if valid == 1:
        #                     new_path = get_redirect_repo(path.replace('github.com/', ''))
        #                     if new_path == '':
        #                         new_path = get_new_url(path)
        #                     else:
        #                         replaces.append((path, 'github.com/' + new_path, r.Revision))
        #                         valid = 0
        #
        #                     if new_path == '':
        #                         err = MessageMiss(path, r.Revision, 1)
        #                         errors.append(err)
        #                     elif valid != 0:
        #                         replaces.append((path, new_path, r.Revision))
        #                         valid = 0
        #
        #                 if valid == 2:
        #                     err = MessageMiss(path, r.Revision, 2)
        #                     errors.append(err)
        #
        #                 if valid != 0:
        #                     continue
        #                 requires.append(path + ' ' + r.Revision)
        # for r in requires:
        #     print(r)
        #
        # for r in replaces:
        #     print(r)

    else:
        f = open(pathname + "/glide.lock")
        data = f.read()