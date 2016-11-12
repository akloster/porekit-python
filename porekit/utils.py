import skbio
import io

def b_to_str(v):
    return v.decode('ascii')

def node_to_seq(node):
    t = node.value.tobytes()
    f = io.BytesIO(t)
    seqs = skbio.io.read(f, format="fastq", variant="sanger")
    return list(seqs[0])

def rename_key(d, key, new_name):
    d[new_name] = d[key]
    del d[key]

