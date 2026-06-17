"""Export a word list to JSONL and CSV.

    PYINFOPEDIA_FLARESOLVERR=http://host:8191 \
        python examples/build_dataset.py palavras.txt out/

`palavras.txt` is one word per line. Writes out/infopedia.jsonl (full typed
entries) and out/infopedia.csv (one row per pronunciation/POS reading).
"""
import os
import sys

from pyinfopedia import Transport
from pyinfopedia.dataset import export_csv, export_jsonl


def make_transport():
    url = os.environ.get("PYINFOPEDIA_FLARESOLVERR")
    if url:
        return Transport(mode="flaresolverr", flaresolverr_url=url)
    return Transport(mode="curl_cffi")


def main(words_file, out_dir):
    words = [w.strip() for w in open(words_file, encoding="utf-8") if w.strip()]
    t = make_transport()
    n_jsonl = export_jsonl(words, f"{out_dir}/infopedia.jsonl", append=False, transport=t)
    n_csv = export_csv(words, f"{out_dir}/infopedia.csv", transport=t)
    print(f"wrote {n_jsonl} entries (jsonl), {n_csv} rows (csv) → {out_dir}/")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
