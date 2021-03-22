import random

import requests
import os
import zipfile


class DOWNLOAD:
    def __init__(self, repo_msg):
        # token = get_token()
        # token_str = 'token ' + token
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
        }
        self.repo = repo_msg
        self.download_result = 0
        self.dst_name = ''
        self.save_name = ''

    def down_load_unzip(self):
        cnt = 0

        while os.path.isdir('temp_hm_' + str(cnt)):
            cnt = cnt + 1

        temp = 'temp_hm_' + str(cnt)
        self.dst_name = temp

        os.mkdir(temp)

        path = '.'
        save_name = os.path.join(path, temp)
        self.save_name = save_name
        repo_name = self.repo[0].replace('github.com/', '')
        repo_version = self.repo[1]
        filename = os.path.join(temp, repo_name.replace('/', '=') + '@' + repo_version)  # kiali=kiali@v1.0.0
        # judge dir exit or not
        # check_result = os.path.exists(os.path.join(path, filename))
        check_result = os.path.isdir(os.path.join(path, filename))
        # print(os.path.join(path, filename))
        # print(check_result)
        if not check_result:
            # create url
            url = 'https://github.com/{}/archive/{}.zip'.format(repo_name, repo_version)
            try:
                r = requests.get(url=url, headers=self.headers, stream=True)
                with open(f'{os.path.join(path, filename)}.zip', 'wb') as f:
                    # write into content
                    for chunk in r.iter_content(chunk_size=512):
                        if chunk:
                            f.write(chunk)
                    f.flush()
                    f.close()
                    tip = 'Repo {} download successfully'.format(filename)
                # print(tip)

                # UNZIP
                unzip_name = filename + '.zip'
                # print(os.path.join(path, unzip_name))
                unzip = zipfile.ZipFile(os.path.join(path, unzip_name), 'r')
                unzip.extractall(os.path.join(save_name, '1'))
                unzip.close()
                # print('Unzip successfully')
                # old_name = os.listdir(os.path.join(save_name, '1'))[0]
                # os.remove(os.path.join(path, unzip_name))  # delete the zip
                # os.rename(os.path.join(os.path.join(save_name, '1'), old_name), os.path.join(path, filename))
                self.download_result = 1
            except Exception as exp:
                self.download_result = -1
                print("download", filename, "failed:", exp, '---------------------------------------------------------')