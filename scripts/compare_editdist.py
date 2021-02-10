import difflib
import argparse

from collections import Counter
from itertools import chain, cycle, zip_longest
from statistics import mean
import edit_distance
from xml_serializer.xml_serializer import XMLSerializer, create_html_header, create_html_footer, create_table_footer, create_table_header


def generate_diff(old, new):
    s = difflib.SequenceMatcher(None, old, new)

    for (tag, i1, i2, j1, j2) in s.get_opcodes():
        if tag == "replace":
            yield "replace", " ".join(old[i1:i2]), " ".join(new[j1:j2])
        elif tag == "delete":
            yield "delete", " ".join(old[i1:i2])
        elif tag == "insert":
            yield "insert", " ".join(new[j1:j2])
        elif tag == "equal":
            yield "equal", " ".join(old[i1:i2])
        else:
            raise Exception


def distance(old, new):
    s = difflib.SequenceMatcher(None, old, new)
    return s.ratio()
    
parser = argparse.ArgumentParser()
parser.add_argument("--hyp", required=True, type=argparse.FileType("r"))
parser.add_argument("--ref", required=True, type=argparse.FileType("r"))
parser.add_argument("--src", type=argparse.FileType("r"), default=None)
parser.add_argument("--output", default=None, type=argparse.FileType("wt"))
parser.add_argument("--normalize_case", action="store_true")
parser.add_argument("--what", choices=["word", "char"], default="word")

parser.add_argument("--best_trads_pred", required=True, type=argparse.FileType("w"))
parser.add_argument("--best_trads_src", required=True, type=argparse.FileType("w"))
parser.add_argument("--best_trads_ref", required=True, type=argparse.FileType("w"))
parser.add_argument("--best_trads_idx", required=True, type=argparse.FileType("w"))

parser.add_argument("--worst_trads_pred", required=True, type=argparse.FileType("w"))
parser.add_argument("--worst_trads_src", required=True, type=argparse.FileType("w"))
parser.add_argument("--worst_trads_ref", required=True, type=argparse.FileType("w"))
parser.add_argument("--worst_trads_idx", required=True, type=argparse.FileType("w"))


parser.add_argument("--how_many", required=True, type=int, default=200)

args = parser.parse_args()

if args.src is None:
    args.src = cycle([""])

if args.normalize_case:
    args.ref = [r.lower() for r in args.ref]
    args.hyp = [h.lower() for h in args.hyp]
else:
    args.ref = list(args.ref)
    args.hyp = list(args.hyp)
    
with XMLSerializer(output=args.output) as doc:

    create_html_header(doc, css="diff.css")

    if args.what == "word":
        data = [(h.strip().split(), r.strip().split()) for h, r in zip(args.hyp, args.ref)]
        data_dist = [(h.strip().split(), r.strip().split(), s.strip().split()) for h, r, s in zip(args.hyp, args.ref, args.src)]

    else:
        data = [(h.strip(), r.strip()) for h, r in zip(args.hyp, args.ref)]

    diff = list(chain.from_iterable(generate_diff(h, r) for h, r in data))

    # XXX we should not compute the diff several times!
    doc.element("h1", "Distance")
    doc.element("p", f"average edit distance (using the Ratcliff-Obershelp algorithm): {mean(distance(h, r) for h, r in data):.3}")

    #dists = sorted([(edit_distance(h, r), ' '.join(h), ' '.join(r), ' '.join(s), idx) for (h, r, s), idx in zip(data_dist, range(1,777))])
    #dists = [(edit_distance(h, r), ' '.join(h), ' '.join(r), ' '.join(s), idx) for (h, r, s), idx in zip(data_dist, range(1,777))]
    dists = sorted([(edit_distance.SequenceMatcher(r, h).distance()/len(r), ' '.join(h), ' '.join(r), ' '.join(s), idx) for (h, r, s), idx in zip(data_dist, range(1, 777))])

    best_trads = dists[0:args.how_many]
    worst_trads = dists[-1*args.how_many:]

    for dist, h, r, s, id in best_trads:
        args.best_trads_src.write(s)
        args.best_trads_src.write('\n')

        args.best_trads_pred.write(h)
        args.best_trads_pred.write('\n')

        args.best_trads_ref.write(r)
        args.best_trads_ref.write('\n')

        args.best_trads_idx.write(str(id)+","+str(dist))
        args.best_trads_idx.write('\n')


    for dist, h, r, s, id in worst_trads:
        args.worst_trads_src.write(s)
        args.worst_trads_src.write('\n')

        args.worst_trads_pred.write(h)
        args.worst_trads_pred.write('\n')

        args.worst_trads_ref.write(r)
        args.worst_trads_ref.write('\n')

        args.worst_trads_idx.write(str(id)+","+str(dist))
        args.worst_trads_idx.write('\n')
