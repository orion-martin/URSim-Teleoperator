# this file is responsible for tracking data live while the program is running. It writes down data but on it's own it does nothing to preserve data outside of the current program
# if this file was the only one, no data would be preserved outside of the current instance of the program.
import numpy as np
from numpy.typing import NDArray
import queue
import threading

# Architecture note (SUPER IMPORTANT).
# the way this all works is that a new piece is created under a name, let's call it ts.
# a new data_availability_set is created, 5 new data_dicts are created,
# a data array is created, and a data_type_dict and data_format_dict are created, all of which are under the name ts.

data_availability_queue_empty = threading.Event()

data_availability_queue = {}
data_dicts = {} # array of dictionaries.
data_array = {} # dictionary of arrays
data_type_dict = {}
data_format_dict = {}
data_flags_dict = {}

data_log_queue = queue.Queue() # every time a piece of data is marked to be logged, it's added to a queue under this structure ("name", index:int), index is an integer. It is then processed in order.

# appends new data under the given name, with the value being a unique data type, this is used for formatting and saving later
# data flags indicates whether to also save a zero-phase-filtered version of the data, and a zero-phased-then-lagged version of the data respectively
def data_structure_add(name, data_type, data_format, data_flags = [False, False]):
    data_type_dict[name] = data_type
    data_format_dict[name] = data_format
    data_array[name] = []
    data_dicts[name] = [{} for _ in range(4)]
    data_flags_dict[name] = data_flags
    data_availability_queue[name] = queue.Queue()
    for i in range(4):
        data_availability_queue[name].put(i)

def data_dict_init(name) -> int:
    data_ind = -1

    slots = data_availability_queue[name] # KeyError here means "no such name"

    try:
        data_ind = slots.get_nowait()
    except queue.Empty:
        data_availability_queue_empty.set()
        raise KeyError(f"RAN OUT OF DATA SLOTS: dict_name = {name}")

    return data_ind
def data_dict_kill(name, index):
    data_availability_queue[name].put(index)
def data_element_add(name, index, element_name, element_value):
    data_dicts[name][index][element_name] = element_value
def data_element_add_group(name, index, element_names, element_values):
    for name_cur, value_cur in zip(element_names, element_values):
        data_dicts[name][index][name_cur] = value_cur
# please note that when you call this function, the data you've been logging MUST be complete (I.E. fully populated to match the data_type you assigned). If it's not, an error will be thrown.
def data_report(name, index):
    data_log_queue.put((name, index))
# logs/processes the next data element
def data_log(name, index):    
    data_array[name].append(data_dicts[name][index].copy())
    data_dict_kill(name, index)

def data_quick_write(name, element_names, element_values):
    index = data_dict_init(name)
    data_element_add_group(name, index, element_names, element_values)
    data_report(name, index)

def data_format(name):

    data_format = data_format_dict[name]
    data_type = data_type_dict[name]
    data_flags = data_flags_dict[name]
    data = data_array[name]

    data_header = ""
    for data_type_key, data_type_element in data_type:
        if (data_header == ""):
            data_header = data_type_key
        else:
            data_header = data_header + ", " + data_type_key

    formatted_data = []
    for data_dict_cur in data:

        tuple = ()

        for data_element_cur in data_type:
            tuple += (data_dict_cur[data_element_cur[0]],)
        formatted_data.append(tuple)


    final_data: NDArray[np.void] = np.array(formatted_data, dtype=data_type)


    return {"data":final_data, "format":data_format, "header":data_header, "flags":data_flags}

def log_data_async():
    while (True):

        name, index = data_log_queue.get()

        if index == -1:
            break

        data_log(name, index)


data_log_thread = threading.Thread(target=log_data_async)

def logging_start():
    data_log_thread.start()

def logging_end():
    data_log_queue.put(("Exit", -1))
    data_log_thread.join()


### example usage of the data tracker system below (please note this incorporates functions from both data_tracker.py AND data_saver.py):
# data_structure_add("pos", [('x', 'f8'), ('y', 'f8'), ('z', 'f8')], ['%.16f', '%.16f', '%.16f'])
#
# data_element_add("pos", 'x', 1)
# data_element_add("pos", 'y', 2)
# data_element_add("pos", 'z', 3)
# data_log("pos")
#
# data_element_add_group("pos", ['x', 'y', 'z'], [4, 5, 6])
# data_log("pos")
#
# data_element_add_group("pos", ['x', 'y', 'z'], [7, 8, 9])
# data_element_add("pos", 'x', -999)
# data_log("pos")
#
# data = data_format("pos")
#
# import data_saver # we import data_saver here to show that past this point we use a function from it, and that prior to this point we use nothing from data_saver
#
# data_saver.data_save_singular("pos.txt", data["data"], data["format"], data["header"])
#
# this will be written to a file named "pos.txt":
#
# x, y, z
# 1.0000000000000000, 2.0000000000000000, 3.0000000000000000
# 4.0000000000000000, 5.0000000000000000, 6.0000000000000000
# -999.0000000000000000, 8.0000000000000000, 9.0000000000000000
###