# -*- coding: utf-8 -*-

__author__ = 'Andreas Klostermann'
__email__ = 'andreasklostermann@gmail.com'
__version__ = '0.1.0'

from . import plugins
from .porekit import find_fast5_files, open_fast5_files, sanity_check
from .porekit import get_fast5_file_metadata
from .porekit import gather_metadata, Fast5File, make_squiggle
from . import plots
from . import sim
