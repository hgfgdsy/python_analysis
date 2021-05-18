class MessageMiss:
    def __init__(self, repo_name, repo_version, typec, filed):
        self.repo_name = repo_name
        self.repo_version = repo_version
        self.error_type = typec
        self.file_descriptor = filed

    def tackle_error_by_type(self):
        msg = ''
        pz = ['Gopkg.lock', 'glide.lock']
        if self.error_type == 1:  # 拒绝迁移（直接依赖找不到） 直接依赖
            msg = 'cannot find ' + self.repo_name + ' specified in ' + pz[self.file_descriptor]
            msg = msg + '(maybe it has been redirected or deleted)'
        elif self.error_type == 2:  # 提醒用户，该依赖tag版本不存在，尝试使用hash commit 直接依赖
            msg = 'cannot find the specified version for ' + self.repo_name + ' in ' + pz[self.file_descriptor] + ', '
            msg = msg + 'will try the hash commit for ' + self.repo_name
        elif self.error_type == 3:  # 提醒用户，tag版本不存在，并且revision版本也不存在，故而使用了该依赖在github上的最新版本  直接依赖
            msg = 'cannot find the specified revision for ' + self.repo_name + ' in ' + pz[self.file_descriptor] + ', '
            msg = msg + 'use the latest version or hash instead'
        elif self.error_type == 4:  # 提醒用户（依赖版本由go mod tidy默认控制）（可能会拒绝迁移） 直接依赖
            msg = 'cannot find suitable version for ' + self.repo_name + '. '
            msg = msg + 'it will determined by go mod tidy automatically'
        elif self.error_type == -10:  # 分析版本后缀时下载依赖失败，提醒用户 直接依赖
            msg = 'cannot download ' + self.repo_name + ' for some reason, fail to analyse version suffix for it'
        elif self.error_type == 5:  # 递归分析依赖中断 间接依赖
            msg = 'fail to recursively analyse the version of dependencies for ' + self.repo_name + ', '
            msg = msg + 'it may caused by missing of config files in dependencies'
        elif self.error_type == 6:  # 递归分析依赖中断 间接依赖
            msg = 'fail to recursively analyse the version of dependencies for ' + self.repo_name + ', '
            msg = msg + 'it may caused by errors in config files in dependencies'
        elif self.error_type == 7:  # 提醒用户添加版本后缀修改了源文件
            msg = 'go source files containing dependency ' + self.repo_name + ' has been modified to add version suffix'
        elif self.error_type == 8:  # 提醒用户依赖被重定向了
            msg = 'dependency ' + self.repo_name + ' has been redirected, new repo name is ' + self.repo_version
        elif self.error_type == 9:  # 递归分析间接依赖时，由于各种原因失败（比如没有配置文件）
            msg = 'fail to recursively analyze indirect dependencies for ' + self.repo_version
        elif self.error_type == 90:
            msg = 'a good case right?'
        return msg


def tackle_errors(err_list):
    msg = ''
    for err in err_list:
        msg = msg + err.tackle_error_by_type() + '\n'
    return msg
