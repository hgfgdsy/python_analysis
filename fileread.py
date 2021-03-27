from dep import parse_gopkg_lock
from cgo import write_go_mod
import re
from suffix import get_version_type

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
    (requires, replaces) = get_mod_require('./pkg/hgfgdsy=migtry@v0.0.0/.go.mod', requires, replaces)

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


def read_in_file(pathname, file_type_descriptor):
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
                            err = MessageMiss(origin_repo_name, r.Version, 1)
                            errors.append(err)
                        elif valid != 0:
                            replaces.append((origin_repo_name, new_path, r.Version))
                            valid = 0

                    if valid == 2:  # TODO get last version here
                        err = MessageMiss(origin_repo_name, r.Version, 2)
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
                                err = MessageMiss(origin_repo_name, r.Revision, 1)
                                errors.append(err)
                            elif valid != 0:
                                replaces.append((origin_repo_name, new_path, r.Revision))
                                valid = 0

                        if valid == 2:
                            err = MessageMiss(path, r.Revision, 2)
                            errors.append(err)

                        if valid == 0:
                            requires.append(origin_repo_name + ' ' + r.Revision)
                            reqlist.append([origin_repo_name, r.Revision])
                            continue
                        else:
                            continue

                    use_version = get_version_type(github_repo_name, r.Version)
                    if use_version == -11:
                        requires.append(origin_repo_name + ' ' + r.Version)
                        reqlist.append([origin_repo_name, r.Version])

                    if use_version == -10:
                        err = MessageMiss(origin_repo_name, r.Version, 10)
                        requires.append(origin_repo_name + ' ' + r.Revision)
                        reqlist.append([origin_repo_name, r.Revision])

                    if use_version == -1:
                        print("It should not occur!(where major version doesn't equal to version in module path)")

                    if use_version == 0:  # no go.mod in dst pkg
                        requires.append(origin_repo_name + ' ' + r.Version + '+incompatible')
                        reqlist.append([origin_repo_name, r.Version])

                    if use_version == 1:  # has go.mod but in module path no version suffix
                        i = re.findall(r'gopkg.in/')
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
                            err = MessageMiss(origin_repo_name, r.Revision, 1)
                            errors.append(err)
                        elif valid != 0:
                            replaces.append((origin_repo_name, new_path, r.Revision))
                            valid = 0

                    if valid == 2:  # TODO get latest version or hash here
                        err = MessageMiss(origin_repo_name, r.Revision, 2)
                        errors.append(err)

                    if valid != 0:
                        continue
                    requires.append(origin_repo_name + ' ' + r.Revision)
                    reqlist.append([origin_repo_name, r.Revision])
                else:
                    requires.append(origin_repo_name + ' ' + r.Revision)
                    reqlist.append([origin_repo_name, r.Revision])

        for r in reference:
            if r not in all_direct_r:
                if r.Source != '':
                    path = r.Source
                    if r.Version != '':
                        replaces.append((r.Path, r.Source, r.Version))
                    else:
                        replaces.append((r.Path, r.Source, r.Revision))
                else:
                    path = r.Path

                if r.Version != '':
                    requires.append(path + ' ' + r.Version)
                    reqlist.append([path, r.Version])
                elif r.Revision != '':
                    requires.append(path + ' ' + r.Revision)
                    reqlist.append([path, r.Revision])

        # TODO write a initial go.mod
        write_go_mod(requires, replaces, reqlist)

        (a, b) = subprocess.getstatusoutput('cd pkg/hgfgdsy=migrationcase@v0.0.0 && go mod tidy')

        diffs = get_diffs(reqlist, all_direct_r, all_direct_dep)

        for dif in diffs:
            after = dif[0]
            diff_type = dif[1]
            (a, b) = subprocess.getstatusoutput('cd pkg/hgfgdsy=migrationcase@v0.0.0 && go mod why ' + after[0])
            chain = out_to_list(a, b)  # chain is start with the project itself
            length = len(chain)

            if diff_type == 1:
                version = after[1]
                for repo in chain:
                    ret = download_a_repo(repo, version)
                    if ret[0] != 0:
                        err = MessageMiss(repo, version, 3)
                        errors.append(err)
                        break

                    all_deps = deal_local_repo_dir(ret[1], 2, [])
                    ver = ''
                    for r in all_deps:
                        if r[0] == repo:
                            if r[1] != '':
                                ver = r[1]
                    








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