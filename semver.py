class Parsed:
    def __init__(self):
        self.major = ""
        self.minor = ""
        self.patch = ""
        self.build = ""
        self.short = ""
        self.prerelease = ""
        self.err = ""


def is_ident_char(c):
    return  'A' <= c <= 'Z' or 'a' <= c <= 'z' or '0' <= c <= '9' or c == '-'


def is_bad_num(v):
    i = 0
    while i < len(v) and '0' <= v[i] <= '9':
        i = i + 1

    return i == len(v) and i > 1 and v[0] == '0'


def parse_prerelease(v):
    if v == "" or v[0] != '-':
        return "", "", False

    i = 1
    start = 1

    while i < len(v) and v[i] != '+':
        if (not is_ident_char(v[i])) and v[i] != '.':
            return "", "", False
        if v[i] == '.':
            if start == i or is_bad_num(v[start:i]):
                return "", "", False

            start = start + i
        i = i + 1
    if start == i or is_bad_num(v[start:i]):
        return "", "", False

    return v[:i], v[i:], True


def parse_build(v):
    if v == "" or v[0] != '+':
        return "", "", False

    i = 1
    start = 1

    while i < len(v):
        if (not is_ident_char(v[i])) and v[i] != '.':
            return "", "", False

        if v[i] == '.':
            if start == i:
                return "", "", False

            start = i + 1
        i = i + 1

    if start == i:
        return "", "", False

    return v[:i], v[i:], True


def parse_int(v):
    if v == "":
        return "", "", False

    if v[0] < '0' or v[0] > '9':
        return "", "", False

    i = 1

    while i < len(v) and '0' <= v[i] <= '9':
        i = i + 1

    if v[0] == '0' and i != 1:
        return "", "", False

    return v[:i], v[i:], True


def parse(v):
    p = Parsed()
    if v == "" or v[0] != 'v':
        p.err = "missing v prefix"
        return p, False

    p.major, v, ok = parse_int(v[1:])

    if not ok:
        p.err = "bad major version"
        return p, ok

    if v == "":
        p.minor = "0"
        p.patch = "0"
        p.short = ".0.0"
        return p, ok

    if v[0] != '.':
        p.err = "bad minor prefix"
        ok = False
        return p, ok

    p.minor, v, ok = parse_int(v[1:])

    if not ok:
        p.err = "bad minor version"
        return p, ok

    if v == "":
        p.patch = "0"
        p.short = ".0"
        return p, ok

    if v[0] != '.':
        p.err = "bad patch prefix"
        ok = False
        return p, ok

    p.patch, v, ok = parse_int(v[1:])

    if not ok:
        p.err = "bad patch version"
        return p, ok

    if len(v) > 0 and v[0] == '-':
        p.prerelease, v, ok = parse_prerelease(v)
        if not ok:
            p.err = "bad prerelease"
            return p, ok

    if len(v) > 0 and v[0] == '+':
        p.build, v, ok = parse_build(v)
        if not ok:
            p.err = "bad build"
            return p, ok

    if v != "":
        p.err = "junk on end"
        ok = False
        return p, ok

    ok = True
    return p, ok


def isvalid(v):
    (p, ok) = parse(v)
    return ok


def canonical(v):
    p, ok = parse(v)
    if not ok:
        return ""
    if p.build != "":
        return v[:len(v) - len(p.build)]

    if p.short != "":
        return v + p.short

    return v
