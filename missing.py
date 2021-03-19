class MessageMiss:
    def __init__(self, repo_name, repo_version, typec):
        self.repo_name = repo_name
        self.repo_version = repo_version
        self.error_type = typec

    def tackle_error_type_1(self):
        print(self.repo_name, self.repo_version)
        return 1
