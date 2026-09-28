# this file is responsible for tracking data live while the program is running. It writes down data but on it's own it does nothing to preserve data outside of the current program
# if this file was the only one, no data would be preserved outside of the current instance of the program.
import numpy as np
from datetime import datetime
from pathlib import Path

# make sure the Data folder exists before trying to save data to it with data_save_singular(...)
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def data_save_singular(file_name, formatted_data, data_format, data_header):

    date = datetime.now()

    formatted_date = date.strftime("%Y_%m_%d__%Hh%Mm%Ss")

    file_name_with_date = file_name + "__" + formatted_date

    Path(f"Data/{file_name}").mkdir(exist_ok=True)

    formatted_name = file_name_with_date + ".txt"
    
    np.savetxt(
        f"Data/{file_name}/" + formatted_name,
        formatted_data, 
        fmt=data_format, 
        delimiter=',', 
        header=data_header, 
        comments=''
    )