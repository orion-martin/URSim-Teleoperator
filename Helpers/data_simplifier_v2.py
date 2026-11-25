import data_loader as dl
import numpy as np
from pathlib import Path
from numpy.dtypes import StringDType

data_name = "KALMAN"

path_name = "Data/" + data_name
path = Path(path_name)

data_as_single_arr = []

for f in path.iterdir():
    if not f.is_file():
        continue

    source = f.name.split("__", 1)[0]  # "TCP" or "postfilter"
    if source not in ("TCP", "postfilter"):
        continue

    with open(f) as fh:
        next(fh)
        rows = [line.rstrip('\n').split(',', 2) for line in fh][0]

    data_as_single_arr.append([source, rows[1], rows[0], rows[2]])  # source, lag, jitter, settings

# sort so all TCP rows sit together, then all postfilter rows
data_as_single_arr.sort(key=lambda r: r[0])

DATA_DIR = Path(__file__).resolve().parent.parent / "Measurement Results"
DATA_DIR.mkdir(parents=True, exist_ok=True)

formatted_name = data_name + "_RESULTS.txt"

np.savetxt(
    f"Measurement Results/{formatted_name}",
    data_as_single_arr,
    fmt=['%s', '%s', '%s', '%s'],
    delimiter=', ',
    header="Source, Lag, Jitter, Settings",
    comments=''
)