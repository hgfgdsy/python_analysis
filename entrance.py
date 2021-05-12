from filechoose import choose_file
from fileread import check_repo_valid
from download import *
import shutil
import zipfile


def writeAllFileToZip(absdir, zip_file):
    for f in os.listdir(absdir):
        absfile = os.path.join(absdir, f)  # 子文件的绝对路径
        if os.path.isdir(absfile):  # 判断是文件夹，继续深度读取。
            relfile = absfile[len(os.getcwd()) + 1:]  # 改成相对路径，否则解压zip是/User/xxx开头的文件。
            zip_file.write(relfile)  # 在zip文件中创建文件夹
            writeAllFileToZip(absfile, zip_file)  # 递归操作
        else:  # 判断是普通文件，直接写到zip文件中。
            relfile = absfile[len(os.getcwd()) + 1:]  # 改成相对路径
            zip_file.write(relfile)
    return


def get_in_repo(repo_name, repo_version):
    if os.path.isdir('./pkg/hgfgdsy=migtry@v0.0.0'):
        shutil.rmtree('./pkg/hgfgdsy=migtry@v0.0.0')
    get_init = DOWNLOAD([repo_name, repo_version])
    get_init.down_load_init()

    return get_init.download_result


def way_one(repo_name, repo_version, repo_path, go_version):

    insert_error = check_repo_valid(repo_name, repo_version)

    if insert_error == 1:
        return []

    if insert_error == 2:
        return []

    get_in_repo(repo_name, repo_version)

    result = choose_file("./pkg/hgfgdsy=migtry@v0.0.0", repo_path)

    if os.path.isdir('./answers'):
        shutil.rmtree('./answers')

    os.mkdir('answers')
    zip_file_path = './answers/ret.zip'

    zip_file = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)

    writeAllFileToZip("/root/Myproject/migrate/front/pkg/hgfgdsy=migtry@v0.0.0", zip_file)
    return result[1]
