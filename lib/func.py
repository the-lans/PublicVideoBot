from os.path import isfile, join
from os import remove


def str_to_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    elif val.isnumeric():
        return bool(int(val))
    elif val and val[0].lower() in ('t', 'f'):
        return val[0].lower() == 't'
    else:
        return bool(val)


def read_cookies(filename):
    cookies = []
    with open(filename, 'rt') as ft:
        for line in ft.readlines():
            line = line.replace('\n', '')
            if len(line) > 0 and line[0] != '#':
                row = line.split('\t')
                cookies.append(
                    {
                        'domain': row[0],
                        'httpOnly': str_to_bool(row[1]),
                        'path': row[2],
                        'secure': str_to_bool(row[3]),
                        'expiry': int(row[4]),
                        'name': row[5],
                        'value': row[6],
                        'sameSite': 'None',
                    }
                )
    return cookies


def remove_files(out_names, path=None):
    for out_name in out_names:
        if path is not None:
            out_name = join(path, out_name)
        if isfile(out_name):
            remove(out_name)
