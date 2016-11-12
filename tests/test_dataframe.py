import pytest
import porekit
test_data_path = "tests/data/"


def test_gather_metadata():
    df1 = porekit.gather_metadata(test_data_path)
    df2 = porekit.gather_metadata(test_data_path, workers=4)
    assert df1.shape == df2.shape
