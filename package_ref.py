class pkg:
    def __init__(self):
        self.Path = ""
        self.Version = ""
        self.Source = ""
        self.Revision = ""
        self.direct = -1

    def set_path(self, path):
        self.Path = path

    def set_version(self, version):
        self.Version = version

    def set_source(self, source):
        self.Source = source

    def set_revision(self, revision):
        self.Revision = revision

    def set_direct(self, direct):
        self.direct = direct
