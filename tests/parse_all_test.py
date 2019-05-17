from sdf_timing import sdfparse
import os


datafiles_path = 'tests/data/'
goldenfiles_path = 'tests/data/golden/'
parsed_sdfs = list()
generated_sdfs = list()


def test_parse():
    files = sorted(os.listdir(datafiles_path))
    for f in files:
        if f.endswith('.sdf'):
            with open(datafiles_path + f) as sdffile:
                parsed_sdfs.append(sdfparse.parse(sdffile.read()))


def test_emit():
    for s in parsed_sdfs:
        generated_sdfs.append(sdfparse.emit(s))


def test_output_stability():
    """ This test checks if the generated sdf are
        identical with golde sdfs"""

    parsed_sdfs_check = list()
    # read the golden files
    files = sorted(os.listdir(goldenfiles_path))
    for f in sorted(files):
        if f.endswith('.sdf'):
            with open(goldenfiles_path + f) as sdffile:
                parsed_sdfs_check.append(sdffile.read())

    for s0, s1 in zip(parsed_sdfs, parsed_sdfs_check):
        sdf0 = sdfparse.emit(s0)
        assert sdf0 == s1


def test_parse_generated():
    for s in generated_sdfs:
        sdfparse.parse(s)
