# -*- coding: utf-8 -*-
import os
import re
import io
import h5py
import pandas as pd
import numpy as np
import Bio
from itertools import chain
from .utils import b_to_str, node_to_seq
from .plugins import DEFAULT_PLUGINS


class Fast5File(h5py.File):
    def __init__(self, filename, mode="r", **kwargs):
        super().__init__(filename, mode, **kwargs)

    def get_tracking_info(self):
        """
            Return a dictionary with "tracking" information.

            Keys and their meaning (as guessed by the author(s)):
                run_id: Unique string id for this run
                asic_id: Unique string id for the ASIC
                flow_cell_id: seems to be empty. May become significant
                              when the new ASIC/membrane bonding is rolled out.
                device_id: MinION device id
                version_name: Version of the flowcell/ASIC
                asic_temp: Temperature inside the ASIC
                heatsink_temp: Temperature in the heatsink, which is probably
                               in the MinION device itself.
                exp_script_purpose: Probably the kind of application the primary
                                interface software is running.
        """
        items = [('run_id', b_to_str),
                 ('asic_id', b_to_str),
                 ('version_name', b_to_str),
                 ('asic_temp', float),
                 ('heatsink_temp', float),
                 ('exp_script_purpose', b_to_str),
                 ('flow_cell_id', b_to_str),
                 ('device_id', b_to_str),
                ]
        attrs = self['/UniqueGlobalKey/tracking_id'].attrs
        return {key: converter(attrs[key]) for key, converter in items}

    def get_channel_info(self):
        """
            Return a dictionary with "channel" information.

            Keys and their meaning (as guessed by the author(s)):
                channel_number: Each pore/channel has a number
                channel_range: ['range' in hdf5] no idea currently...
                channel_sampling_rate: ['sampling_rate'] Probably samples per second
                channel_digitisation: ['digitisation'] ADC resolution
                channel_offset: ['offset'] ADC bias
        """
        items = [('channel_number', int),
                 ('range', float),
                 ('sampling_rate', float),
                 ('digitisation', float),
                 ('offset', float),
                ]

        attrs = self['/UniqueGlobalKey/channel_id'].attrs
        info = {key: converter(attrs[key]) for key, converter in items}
        new_names = [('range','channel_range'),
                     ('sampling_rate', 'channel_sampling_rate'),
                     ('digitisation', 'channel_digitisation'),
                     ('offset', 'channel_offset'),
                     ]
        for old, new in new_names:
            info[new] = info[old]
            del info[old]
        return info

    def find_analysis_base(self, base):
        for key in list(self['Analyses'].keys()):
            match = re.match(base+r'_(?P<number>\d\d\d)', key)
            if match:
                yield base, match.groups()[0]

    def get_basecalling_info(self):
        info = {'has_basecalling': False}
        has_template = False
        basecallers = chain(self.find_analysis_base("Basecall_2D"), self.find_analysis_base("Basecall_1D"))
        for basename, number in basecallers:
            info['has_basecalling'] = True
            node = self["Analyses"][basename+'_'+number]
            if 'BaseCalled_template' in node:
                info["has_template"] = True
                seq = node_to_seq(node['BaseCalled_template/Fastq'])
                info["template_length"] = len(seq)
                info["template_mean_qscore"] = seq.positional_metadata.quality.mean()

            if 'BaseCalled_complement' in node:
                info["has_complement"] = True
                seq = node_to_seq(node['BaseCalled_complement/Fastq'])
                info["complement_length"] = len(seq)
                info["complement_mean_qscore"] = seq.positional_metadata.quality.mean()

            if 'BaseCalled_2D' in node:
                info["has_2D"] = True
                seq = node_to_seq(node['BaseCalled_2D/Fastq'])
                info["2D_length"] = len(seq)
                info["2D_mean_qscore"] = seq.positional_metadata.quality.mean()

        return info

    def get_read_info(self):
        items = [
            ('start_time', int),
            ('duration', float),
            ('read_id', b_to_str),
            ('read_number', int),
        ]
        attrs = self.get_read_node().attrs
        info = {key: converter(attrs[key]) for key, converter in items}
        new_names = [
            ('start_time', 'read_start_time'),
            ('duration', 'read_duration'),
        ]
        for old, new in new_names:
            info[new] = info[old]
            del info[old]
        info["read_end_time"] = info["read_start_time"] + info["read_duration"]
        return info

    def get_read_id(self):
        rn = self.get_read_node()
        return rn.attrs['read_id']

    def path_to_seq(self, path):
        node = self[path]
        f = io.BytesIO(node.value.tobytes())
        seqs = Bio.SeqIO.parse(f, "fastq-sanger")
        f.close()
        return list(seqs)[0]

    def get_fastq_from(self, path):
        return self[path].value.tobytes().decode('ascii')

    def get_template_fastq(self):
        try:
            return self.get_fastq_from('/Analyses/Basecall_2D_000/BaseCalled_template/Fastq')
        except KeyError:
            return self.get_fastq_from('/Analyses/Basecall_1D_000/BaseCalled_template/Fastq')

    def get_2D_fastq(self):
        return self.get_fastq_from('/Analyses/Basecall_2D_000/BaseCalled_2D/Fastq')

    def get_complement_fastq(self):
        return self.get_fastq_from('/Analyses/Basecall_2D_000/BaseCalled_complement/Fastq')

    def get_fastq(self, which=["template", "complement", "2D"]):
        output = ""
        if "template" in which:
            try:
                output += self.get_template_fastq()
            except KeyError:
                pass

        if "complement" in which:
            try:
                output += self.get_complement_fastq()
            except KeyError:
                pass
        if "2D" in which:
            try:
                output += self.get_2D_fastq()
            except:
                pass
        return output

    def get_read_node(self):
        reads = self['Analyses/EventDetection_000/Reads']
        for key in reads.keys():
            read = reads[key]
            break
        return read

    def get_events(self):
        read = self.get_read_node()
        if read is None:
            return None
        return pd.DataFrame.from_records(read['Events'][:])

    def get_model(self):
        model_frame = pd.DataFrame(self["Analyses/Basecall_2D_000/BaseCalled_template/Model"][:])
        model_frame.index = model_frame.kmer
        return model_frame


def open_fast5_files(path, mode="r"):
    """
    Recursively searches for files with ending '.fast5' and yields
    opened Fast5File objects. It omits those files which don't open correctly
    or don't pass a couple of simple and fast sanity checks.
    """
    for filename in find_fast5_files(path):
        try:
            hdf = Fast5File(filename, mode=mode)
            if sanity_check(hdf):
                yield hdf
        except OSError:
            try:
                hdf.close()
            except:
                pass


def find_fast5_files(path):
    """
        Recursively searches files with ending '.fast5'.
        Use this if you want to find filenames
        without opening them.
    """
    for dirpath, dirnames, filenames in os.walk(path):
        for fname in filenames:
            if fname.endswith('.fast5'):
                yield os.path.join(dirpath, fname)


def sanity_check(hdf):
    """ Minimalistic sanity check for Fast5 files."""
    required_paths = ['Analyses', 'UniqueGlobalKey', 'Analyses/EventDetection_000']
    try:
        for p in required_paths:
            if p not in hdf:
                return False
        return True
    except:
        return False


def get_fast5_file_metadata(file_name, plugins=None, raise_errors=False):
    record = {
        "absolute_filename": file_name,
        "filename": os.path.split(file_name)[-1]
    }
    try:
        fast5 = Fast5File(file_name)
    except OSError:
        return record

    if plugins is None:
        plugins = [plugin_class() for plugin_class in DEFAULT_PLUGINS]

    try:
        for plugin in plugins:
            result = []
            try:
                result = plugin.run_on_fast5(fast5)
            except:
                if raise_errors:
                    raise
            else:
                for k in result.keys():
                    record[plugin.base_name + '_' + k] = result[k]
    finally:
        fast5.close()
    for k, v in record.items():
        if isinstance(v, (bytes, bytearray)):
            record[k] = v.decode("utf-8")
    try:
        if "channel_number" in record:
            record["channel_number"] = int(record["channel_number"])
    except:
        record["channel_number"] = 0
    return record


def gather_metadata_records(path, plugins=None, workers=1, raise_errors=False, progress_callback=None):
    # `workers` feature is more or less broken right now,
    # because it has to recreate all Plugins whenever it is called
    file_names = list(find_fast5_files(path))
    files_read = 0
    files_total = len(file_names)
    if workers == 1:
        for file_name in file_names:
            if progress_callback:
                progress_callback(files_read, files_total)
            record = get_fast5_file_metadata(file_name, plugins, raise_errors=raise_errors)
            files_read += 1
            yield record
    elif workers > 1:
        import multiprocessing
        pool = multiprocessing.Pool(workers)
        for record in pool.map(get_fast5_file_metadata, file_names):
            if progress_callback:
                progress_callback(files_read, files_total)
            yield record
            files_read += 1
    else:
        raise ValueError("`workers` parameter needs a positive integer")


def gather_metadata(path, workers=1, plugins=None, raise_errors=False, progress_callback=None):
    """
    Collects metadata from Fast5 files under the given paths.

    Returns a DataFrame with Metadata on each read.

    The columns represent a somewhat arbitrary selection of data.
    """
    records = gather_metadata_records(path, plugins=plugins, workers=workers, raise_errors=raise_errors, progress_callback=progress_callback)
    records = list(records)
    print(len(records))
    columns = [
        'filename',
        'absolute_filename',
    ]
    if plugins is None:
        plugins = [plugin_class() for plugin_class in DEFAULT_PLUGINS]
    for plugin in plugins:
        columns += [(plugin.base_name + '_' + k) for k in plugin.expected_keys]

    df = pd.DataFrame.from_records(records, columns=columns)
    return df


def make_squiggle(sequence, model, std_multiplier=1.0):
    """
    Turn a SciKit Bio Sequence object into a squiggle.

    `sequence` must be a SciKit Bio Sequence, `model` is a `pandas.DataFrame`
    like returned from `Fast5File.get_model()` and `std_multiplier` is a float
    to multiply the level_stdv by. Setting `std_multiplier` above 1 means the
    squiggles are noisier than expected by the model.
    """
    # Find k for kmers from model
    k = len(model.index.values[0])

    # number of events
    n = len(sequence) - k

    # prepare means
    means = np.zeros(n, dtype="float64")
    stdvs = np.zeros(n, dtype="float64")

    for i in range(n):
        kmer = sequence[i:i + k].values.tostring()
        means[i] = model.ix[kmer]["level_mean"]
        stdvs[i] = model.ix[kmer]["level_stdv"]
    x = np.random.normal(means, stdvs * std_multiplier)
    return x
