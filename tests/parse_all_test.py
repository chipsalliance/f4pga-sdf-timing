from sdf_timing import sdfparse
import os


datafiles_path = 'tests/data/'
parsed_sdfs = list()


def test_parse():
    files = os.listdir(datafiles_path)
    for f in files:
        if f.endswith('.sdf'):
            with open(datafiles_path + f) as sdffile:
                parsed_sdfs.append(sdfparse.parse(sdffile.read()))


def test_emit():
    for s in parsed_sdfs:
        sdfparse.emit(s)
