import data_loader as dl
import numpy as np
from pathlib import Path
from numpy.dtypes import StringDType


average_lag_path_name = "Data/average_lag"
RMSE_jitter_path_name = "Data/RMSE_jitter"
settings_name = "Data/Settings"

average_lag_path = Path(average_lag_path_name)
RMSE_jitter_path = Path(RMSE_jitter_path_name)
settings_path = Path(settings_name)

average_lag_filenames = np.array([(average_lag_path_name + "/" + f.name) for f in average_lag_path.iterdir() if f.is_file()])
RMSE_jitter_filenames = np.array([(RMSE_jitter_path_name + "/" + f.name) for f in RMSE_jitter_path.iterdir() if f.is_file()])
settings_filenames = np.array([(settings_name + "/" + f.name) for f in settings_path.iterdir() if f.is_file()])

# array of average lag as X coordinate and RMSE jitter as Y coordinate
lag_jitter_coord_array = []

for i in range(0, len(average_lag_filenames)):

    lag_coord = dl.load_data(name=average_lag_filenames[i], skip_count=1, unpack=False, verbose_path=True)[3]
    RMSE_coord = dl.load_data(name=RMSE_jitter_filenames[i], skip_count=1, unpack=False, verbose_path=True)[3]
    settings_for_coord = dl.load_data(name=settings_filenames[i], skip_count=1, unpack=False, verbose_path=True, dtype=StringDType, delimiter='\x00') # the settings that produced the corresponding lag and jitter

    lag_jitter_coord_array.append([lag_coord, RMSE_coord, settings_for_coord])

# make sure the Data folder exists before trying to save data to it with data_save_singular(...)
DATA_DIR = Path(__file__).resolve().parent.parent / "Measurement Results"
DATA_DIR.mkdir(parents=True, exist_ok=True)

file_name = "Results"

formatted_name = file_name + ".txt"

np.savetxt(
    f"Measurement Results/{formatted_name}",
    lag_jitter_coord_array, 
    fmt=['%.16f', '%.16f', "%s"], 
    delimiter=', ', 
    header="Lag, Jitter, Settings", 
    comments=''
)