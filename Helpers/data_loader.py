import numpy as np

# if unpack=False, returns a line-by-line structure, where each sub-array is just the contents of one line
# if unpack=True, returns a variable-based structure, where each sub array is every value for a given variable, ordered from line-0 to line-n
# if verbose_path=True, name must be full file path, structured as "Data/filename.txt", if False, simply the name of the subfolder and file will suffice
def load_data(name, skip_count, unpack=True, verbose_path=False, dtype=None, delimiter=','):

    data = np.loadtxt(
        name if verbose_path else ("Data/" + name + ".txt"),
        delimiter=delimiter,
        skiprows=skip_count,
        unpack=unpack,
        dtype=dtype,
    )

    return data


