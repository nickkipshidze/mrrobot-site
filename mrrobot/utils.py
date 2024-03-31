import os, re
from . import settings

def natsort(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split("(\d+)", s)] 

def sort(items):
    return sorted(items, key=natsort)

def filter_items(items):
    return [item for item in items if not (is_directory(get_source(item)) and ".mrignore" in os.listdir(get_source(item)))]

def list_sources():
    files = []
    for source in settings.SOURCES:
        for file in sort(os.listdir(source)):
            files.append(file)
    return filter_items(files)

def list_item(path):
    if os.path.exists(path):
        return sort(filter_items(os.listdir(path)))
    return []

def get_source(item):
    if os.path.exists(item):
        return item
    
    for source in settings.SOURCES:
        if os.path.exists(os.path.join(source, item)):
            return os.path.join(source, item).__str__()
    return None

def is_directory(path):
    if path == None:
        return False
    
    if os.path.isdir(path):
        return True
    
    for source in settings.SOURCES:
        if os.path.isdir(os.path.join(source, path)):
            return True
        
    return False

def is_binay_file(path):
    textchars = bytearray([7, 8, 9, 10, 12, 13, 27]) + bytearray(range(0x20, 0x7f)) + bytearray(range(0x80, 0x100))
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

    if is_binary_string(open(path, "rb").read(1024)):
        return True
    else:
        try:
            with open(path, "r") as file:
                file.read()
            return False
        except UnicodeDecodeError:
            return True

def get_partition_data(filesystem = None, mount = None):
    # Only works on Linux lol
    # Why would you even use Windows as a server anyway?
    
    columns = ["filesystem", "size", "used", "avail", "use%", "mounted on"]
    output = os.popen("df", "r").read().split("\n")[1:-1]

    partitions = []
    
    for row in output:
        data = row.split(" ")
        [data.remove("") for _ in range(data.count(""))]
        data = dict(zip(columns, data))
        
        data["size"] = int(data["size"])
        data["used"] = int(data["used"])
        data["avail"] = int(data["avail"])
        
        if mount:
            if data["mounted on"] == mount:
                return data
        elif filesystem:
            if data["filesystem"] == filesystem:
                return data
        else:
            partitions.append(data)
    
    return partitions
