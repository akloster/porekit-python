import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import porekit


def read_length_distribution(meta, ax=None):
    """ Plot the distribution of the read length.
        "read length" is measured as the maximum of template vs complement length.

    """
    if ax is None:
        f, ax = plt.subplots()
        f.set_figwidth(14)
        f.set_figheight(4)
        f.suptitle("Read length distribution")
    ax.xaxis.set_label_text("Read length")
    a = meta.template_length.values
    a[np.isnan(a)] = 0
    b = meta.complement_length.values
    b[np.isnan(b)] = 0
    v = np.maximum(a, b)
    vmax = np.percentile(v, 99)
    v = v[v < vmax]
    ax.hist(v, bins=100)
    return ax.get_figure(), ax


def template_vs_complement(meta, ax=None):
    """ Plot template length vs complement length.
    """
    if ax is None:
        f, ax = plt.subplots()
        f.set_figwidth(5)
        f.set_figheight(5)
        f.suptitle("Template vs complement length")

    a = meta.template_length.values
    b = meta.complement_length.values
    nan = np.isnan(a) | np.isnan(b)
    a = a[~nan]
    b = b[~nan]
    amax = np.percentile(a, 99.5)
    bmax = np.percentile(b, 99.5)
    both_max = max(amax, bmax)
    ax.set_xlim(0, both_max)
    ax.set_ylim(0, both_max)
    ax.xaxis.set_label_text("Template length")
    ax.yaxis.set_label_text("Complement length")
    ax.scatter(a, b, s=3, alpha=0.5);
    return ax.get_figure(), ax


def reads_vs_time(meta, ax=None):
    """ Plot reads vs time.
        Useful to assess the degradation of channels over time.
    """
    if ax is None:
        f, ax = plt.subplots()
        f.set_figwidth(14)
        f.set_figheight(4)
        f.suptitle("Number of reads vs time")

    t = meta.read_end_time
    t = t-t.min()
    t /= 10000 * 60 * 60
    ax.hist(t, bins=100);
    ax.xaxis.set_label_text("Time (in hours)")
    return ax.get_figure(), ax


def occupancy(meta, ax=None):
    """ Show channel occupancy over time.
    """
    if ax is None:
        f, ax = plt.subplots()
        f.set_figwidth(14)
        f.suptitle("Occupancy over time")

    start_time = meta.read_start_time.min() / 10000 / 60
    end_time = meta.read_end_time.max() / 10000 / 60
    total_minutes = end_time - start_time
    num_channels = meta.channel_number.max()+1
    X = np.zeros((num_channels, int(np.ceil(total_minutes))))

    for channel, group in meta.groupby("channel_number"):
        for index, read in group.iterrows():
            a, b = read.read_start_time/10000/60, read.read_end_time / 10000 / 60
            X[channel, round(a):round(b)] = 1
    ax.imshow(X, aspect=total_minutes/1800, cmap="Greys")
    ax.xaxis.set_label_text("Time (in minutes)")
    ax.yaxis.set_label_text("Channel number")
    return ax.get_figure(), ax


def yield_curves(meta, ax=None):
    """ Show yield curves for template, complement and 2D sequences
    """
    if ax is None:
        f, ax = plt.subplots()
        f.set_figwidth(14)
        f.set_figheight(4)

    def plot_length(which, label):
        d = meta[~np.isnan(meta[which])][[which, "read_end_time"]]
        d = d.sort_values("read_end_time")
        x = d["read_end_time"].values / 10000 / 60 / 60
        y = d[which].values.cumsum() / 1e6
        ax.plot(x, y, label=label);

    plot_length("2D_length", "2D")
    plot_length("template_length", "Template")
    plot_length("complement_length", "Complement")
    ax.legend(loc=0);
    ax.xaxis.set_label_text("Time (in hours)")
    ax.yaxis.set_label_text("Yield (in Mb)")
    return ax.get_figure(), ax


def squiggle_dots(fast5, ax=None):
    if isinstance(fast5, porekit.Fast5File):
        close_later = False
        f5 = fast5
    else:
        f5 = porekit.Fast5File(fast5)
        close_later = True

    if ax is None:
        f, ax = plt.subplots()
        f.set_figwidth(14)
        f.set_figheight(4)

    events = f5.get_events()
    start = events.start.min()
    try:
        hairpin_index = f5.get_read_node().attrs["hairpin_event_index"]
    except KeyError:
        hairpin_index = None

    means = events["mean"]
    times = events["start"]-start
    times /= 10000
    mine = means.min()
    maxe = means.max()
    ax.set_xlim(0, times.max())
    ax.set_ylim(mine-10, maxe+10)
    ax.grid(None)
    ax.set_axis_bgcolor("white")
    ax.scatter(times, means, alpha=1, s=1, color=(0, 0, 0))
    if hairpin_index:
        hairpin_index = fast5.get_read_node().attrs['hairpin_event_index']
        hairpin_x = times[hairpin_index]
        r = matplotlib.patches.Rectangle((hairpin_x, mine-10),
                                         1, 5, color="black", alpha=1)
        ax.add_patch(r)
        ax.annotate("hairpin detected", xy=(hairpin_x+1.5, mine-10))
    ax.xaxis.set_label_text("Time (in seconds)")
    ax.yaxis.set_label_text("Voltage")

    return ax.get_figure(), ax
