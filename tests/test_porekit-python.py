#!/usr/bin/env python

"""
test_porekit-python
----------------------------------

Tests for `porekit-python` module.
"""

import unittest
import os
import sys
import porekit
import ipdb

test_data_path = '/media/internal_2/nanopore/test_data/'


class TestPorekit(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_find_fast5_files(self):
        filenames = list(porekit.find_fast5_files(test_data_path))
        self.assertGreater(len(filenames), 0,
                           "Should return filenames.")
        for filename in filenames:
            if not os.path.exists(filename):
                self.fail("Returned files should exist.")

    def test_open_fast5_files(self):
        for fast5 in porekit.open_fast5_files(test_data_path):
            fast5
    def test_gather_metadata(self):
        df = porekit.gather_metadata(test_data_path)
        self.assertTrue(df['2D_length'].any())
        self.assertTrue(df['template_length'].any())
        self.assertTrue(df['complement_length'].any())


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
