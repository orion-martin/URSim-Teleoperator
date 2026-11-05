# this file is responsible for tracking data live while the program is running. It writes down data but on it's own it does nothing to preserve data outside of the current program
# if this file was the only one, no data would be preserved outside of the current instance of the program.
import numpy as np
from pathlib import Path

# make sure the Data folder exists before trying to save data to it with data_save_singular(...)
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# list of suffixes that files can use from A to Z. These are used for duplicate runs and such. First runs always get the A suffix even though it may never have duplicates
suffixes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

def data_save_singular(file_name, formatted_data, data_format, data_header, date):

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
def data_save_singular_with_path(file_name, file_path, formatted_data, data_format, data_header, date, save_with_date=True, with_letter_suffix=True):

    formatted_name = file_name

    if (save_with_date):
        formatted_date = date.strftime("%Y_%m_%d__%Hh%Mm%Ss")

        file_name_with_date = file_name + "__" + formatted_date
        
        formatted_name = file_name_with_date + ".txt"

    Path(f"Data/{file_path}").mkdir(exist_ok=True)

    if (with_letter_suffix):
        for cur_suffix in suffixes:
            if not Path(f"Data/{file_path}/" + formatted_name + "__" + cur_suffix).exists():
                formatted_name = formatted_name + "__" + cur_suffix
                break
        else:
            print("WARNING: NO SUFFIXES AVAILABLE!!!")

    np.savetxt(
        f"Data/{file_path}/" + formatted_name,
        formatted_data, 
        fmt=data_format, 
        delimiter=',', 
        header=data_header, 
        comments=''
    )