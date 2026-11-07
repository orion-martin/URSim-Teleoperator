import data_loader as dl
import numpy as np
from pathlib import Path
from numpy.dtypes import StringDType

data_name = "LA_VIOLA"


path_name = "Data/" + data_name

path = Path(path_name)

file_names = np.array([path_name + "/" + f.name for f in path.iterdir() if f.is_file()])

# array of average lag as X coordinate and RMSE jitter as Y coordinate
data_as_single_arr = []

for file_name_cur in file_names:

    with open(file_name_cur) as f:
        next(f)
        rows = [line.rstrip('\n').split(',', 2) for line in f][0]

    data_as_single_arr.append([rows[0], rows[1], rows[2]])

# make sure the Data folder exists before trying to save data to it with data_save_singular(...)
DATA_DIR = Path(__file__).resolve().parent.parent / "Measurement Results"
DATA_DIR.mkdir(parents=True, exist_ok=True)

file_name = data_name + "_RESULTS"

formatted_name = file_name + ".txt"

np.savetxt(
    f"Measurement Results/{formatted_name}",
    data_as_single_arr, 
    fmt=['%s', '%s', '%s'],
    delimiter=', ', 
    header="Lag, Jitter, Settings", 
    comments=''
)