import sdfparse
import os


datafiles_path = 'tests/data/'


def test_parse():
    files = os.listdir(datafiles_path)
    for f in files:
        if f.endswith('.sdf'):
            with open(datafiles_path + f) as sdffile:
                sdfparse.parse(sdffile.read())
