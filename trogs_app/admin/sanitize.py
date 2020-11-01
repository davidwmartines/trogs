def trim_strings(data):
    for key, val in data.items():
        if isinstance(val, str) and val:
            val = val.strip()
            data[key] = val