# -*- coding: utf-8 -*-
from .utils import b_to_str, node_to_seq, rename_key
import skbio
from itertools import chain


class Plugin(object):
    """ 
        Each plugin extracts data from a Fast5File.

        Plugin classes are usually instantiated only once, when the plugin is first used on a Fast5 file.

        The instance members should not be used to accumulate state,
        like running averages etc., but they can be used to initialize
        libraries, cache values and so on.

        The output of running a plugin against a file must never depend on what other files have been run
        against this plugin instance.

        the `run_on_fast5` method must return a dictionary, and it must only contain keys listed in
        `expected_keys`. The output does not need to contain all `expected_keys`, but then the value will
        be filled in as None, and the resulting DataFrame will still contain this column.

        In the final DataFrame, each key of the output will be prepended with the string in `base_name`.

    """
    base_name = None
    def __init__(self):
        if self.base_name is None:
            raise NotImplementedError("Plugin classes must set a 'base_name' class member")
        self.load()

    def load(self):
        pass


class Channel(Plugin):
    base_name = 'channel'
    expected_keys = ['number',
                     'range',
                     'sampling_rate',
                     'digitisation',
                     'offset',
            ]


    def run_on_fast5(self, fast5):
        attrs = fast5['/UniqueGlobalKey/channel_id'].attrs
        return dict(number=attrs['channel_number'],
                 sampling_rate=attrs['sampling_rate'],
                 digitisation=attrs['digitisation'],
                 offset=attrs['offset'])


class Tracking(Plugin):
    base_name = 'channel'
    expected_keys = ['run_id',
                     'asic_id',
                     'version_name',
                     'asic_temp',
                     'heatsink_temp',
                     'exp_script_purpose',
                     'flow_cell_id',
                     'device_id',
            ]


    def run_on_fast5(self, fast5):
        items = [('run_id', b_to_str),
                 ('asic_id', b_to_str),
                 ('version_name', b_to_str),
                 ('asic_temp', float),
                 ('heatsink_temp', float),
                 ('exp_script_purpose', b_to_str),
                 ('flow_cell_id', b_to_str),
                 ('device_id', b_to_str),
                ]
        attrs = fast5['/UniqueGlobalKey/tracking_id'].attrs
        return {key: converter(attrs[key])  for key, converter in items}


class Basecall(Plugin):
    base_name = 'basecall'
    expected_keys = ['has_basecall',
                     'has_template',
                     'has_complement',
                     'has_2D',
                     'template_length',
                     'complement_length',
                     'template_mean_qscore',
                     'complement_mean_qscore',
                     '2D_length',
                     '2D_mean_qscore'
                     ]


    def run_on_fast5(self, fast5):
        basecallers = chain(fast5.find_analysis_base("Basecall_2D"), fast5.find_analysis_base("Basecall_1D"))
        result =dict(has_basecall=False)
        for basename, number in basecallers:
            result['has_basecall'] = True
            node = fast5["Analyses"][basename+'_'+number]
            if 'BaseCalled_template' in node:
                result["has_template"] = True
                seq = node_to_seq(node['BaseCalled_template/Fastq'])
                result["template_length"] = len(seq)
                result["template_mean_qscore"] = seq.positional_metadata.quality.mean()

            if 'BaseCalled_complement' in node:
                result["has_complement"] = True
                seq = node_to_seq(node['BaseCalled_complement/Fastq'])
                result["complement_length"] = len(seq)
                result["complement_mean_qscore"] = seq.positional_metadata.quality.mean()

            if 'BaseCalled_2D' in node:
                result["has_2D"] = True
                seq = node_to_seq(node['BaseCalled_2D/Fastq'])
                result["2D_length"] = len(seq)
                result["2D_mean_qscore"] = seq.positional_metadata.quality.mean()
        return result


class Read(Plugin):
    base_name = 'read'
    expected_keys = ['start_time',
                     'duration',
                     'id',
                     'number',
                     ]

    def run_on_fast5(self, fast5):
        items = [('start_time', int),
                 ('duration', float),
                 ('read_id', b_to_str),
                 ('read_number', int),
                ]

        attrs = fast5.get_read_node().attrs
        info = {key: converter(attrs[key]) for key, converter in items}
        info["end_time"] = info["start_time"] + info["duration"]

        rename_key(info, "read_number", "number")
        rename_key(info, "read_id", "id")
        return info


DEFAULT_PLUGINS = [Channel, Tracking, Basecall, Read]
