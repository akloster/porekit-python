import pytest
import porekit.plugins as plugins
import porekit
import os



def test_implementation_checks():
    with pytest.raises(NotImplementedError):
        class MyPlugin(plugins.Plugin):
            pass
        MyPlugin() 


def check_plugin_default(plugin_class, fast5_file_name, output=None):
    plugin = plugin_class()
    fast5 = porekit.Fast5File(fast5_file_name)
    try:
        result = plugin.run_on_fast5(fast5)
    finally:
        fast5.close()
    if output is not None:
        assert result == output
    for k in result.keys():
        assert k in plugin.expected_keys


def test_channel_plugin():
    check_plugin_default(plugins.Channel,
            "tests/data/2016_3_4_3507_1_ch120_read635_strand.fast5",
            {'offset': 8.0, 'sampling_rate': 3012.0, 'digitisation': 8192.0, 'number': b'120'})

def test_all_plugins_basic():
    for plugin_class in (plugins.Channel,
                         plugins.Tracking,
                         plugins.Basecall):
       for file_name in os.listdir("tests/data"):
           result = check_plugin_default(plugin_class, "tests/data/"+file_name)

