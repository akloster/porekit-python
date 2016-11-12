import pytest
import porekit


test_data_path = "tests/data/"


def test_iteration():
    seen = dict()
    for f in porekit.find_fast5_files(test_data_path):
        assert f not in seen
        seen[f] = True


def test_opening_files():
    for fast5 in porekit.open_fast5_files(test_data_path):
        fast5.close()


def test_get_metadata():
    for f in porekit.find_fast5_files(test_data_path):
        result = porekit.get_fast5_file_metadata(f)




