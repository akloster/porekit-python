# -*- coding: utf-8 -*-
import os
import sys
import h5py
import pandas as pd


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


def b_to_str(v):
    return v.decode('ascii')

class Fast5File(h5py.File):
    def __init__(self, filename, mode=None, **kwargs):
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
        return {key: converter(attrs[key])  for key, converter in items}

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

    def get_basecalling_info(self):
        info = {'has_basecalling': False}

        try:
            basecall = self['/Analyses/Basecall_2D_000']
        except KeyError:
            return info
        info['has_basecalling'] = True
        info['basecall_time_stamp'] = basecall.attrs['time_stamp'].decode('ascii')
        try:
            info['basecall_version'] = basecall.attrs['version'].decode('ascii')
        except KeyError:
            pass
        info['basecall_name'] = basecall.attrs['name'].decode('ascii')

        # Template
        try:
            template = basecall['BaseCalled_template']
            info['has_template'] = True
        except KeyError:
            template = None
            info['has_template'] = False
        if template:
            fastq = template['Fastq'].value.tobytes().decode('ascii')
            lines = list(fastq.splitlines())
            info['template_length'] = len(lines[1])

        # Complement
        try:
            complement = basecall['BaseCalled_complement']
            info['has_complement'] = True
        except KeyError:
            complement = None
            info['has_complement'] = False
        if complement:
            fastq = complement['Fastq'].value.tobytes().decode('ascii')
            lines = list(fastq.splitlines())
            info['complement_length'] = len(lines[1])
        # 2D
        try:
            b2d = basecall['BaseCalled_2D']
            info['has_2D'] = True
        except KeyError:
            b2d = None
            info['has_2D'] = False
        if b2d:
            fastq = b2d['Fastq'].value.tobytes().decode('ascii')
            lines = list(fastq.splitlines())
            info['2D_length'] = len(lines[1])
        return info
    def get_fastq_from(self,path):
        return self[path].value.tobytes().decode('ascii')

    def get_template_fastq(self):
        return self.get_fastq_from('/Analyses/Basecall_2D_000/BaseCalled_template/Fastq')

    def get_2D_fastq(self):
        return self.get_fastq_from('/Analyses/Basecall_2D_000/BaseCalled_2D/Fastq')

    def get_complement_fastq(self):
        return self.get_fastq_from('/Analyses/Basecall_2D_000/BaseCalled_complement/Fastq')

    def get_events(self):
        reads = self['Analyses/EventDetection_000/Reads']
        for key in reads.keys():
            read = reads[key]
            break
        if read is None:
            return None
        return pd.DataFrame.from_records(read['Events'][:])

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


def gather_metadata_records(path, tracking_info=True, channel_info=True,
                            basecalling_info=True):
    for hdf in open_fast5_files(path):
        record = dict(absolute_filename=hdf.filename,
                      filename=os.path.split(hdf.filename)[-1],
                      format= hdf['/Sequences/Meta'].attrs['version'].tobytes().decode()
                )
        if tracking_info:
            record.update(hdf.get_tracking_info())
        if channel_info:
            record.update(hdf.get_channel_info())
        if basecalling_info:
            record.update(hdf.get_basecalling_info())
        hdf.close()
        yield record


def gather_metadata(path, tracking_info=True, channel_info=True, basecalling_info=True):
    """
        Collects metadata from Fast5 files under the given paths.

        Individual contents can be switched off (on by default):
          * tracking_info: Information about device and flowcell
          * channel_info: Information about the channel this read was generated
                          from

        Returns a DataFrame with Metadata on each read. The relative filenames
        are used as index, because they are assumed to be unique even accross
        different paths, but the exact path/location of these files may change.

        The columns represent a somewhat arbitrary selection of data.

    """
    records = gather_metadata_records(path,
                    tracking_info=tracking_info,
                    channel_info=channel_info,
                    basecalling_info=basecalling_info)

    columns = [ 'filename',
                'absolute_filename',
                'format'
                ]
    if tracking_info:
        columns += ['run_id',
                   'asic_id',
                   'version_name',
                   'device_id',
                   'flow_cell_id',
                   'asic_temp',
                   'heatsink_temp',
                   ]
    if channel_info:
        columns += ['channel_number',
                    'channel_range',
                    'channel_sampling_rate',
                    'channel_digitisation',
                    'channel_offset',
                   ]
    if basecalling_info:
        columns += ['has_basecalling',
                    'basecall_timestamp',
                    'basecall_version',
                    'basecall_name',
                    'has_template',
                    'template_length',
                    'has_complement',
                    'complement_length',
                    'has_2D',
                    '2D_length',
                  ]
    df = pd.DataFrame.from_records(records, index='filename', columns=columns)
    return df
