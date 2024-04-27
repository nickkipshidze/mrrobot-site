import os, re, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import settings

random.seed(
    sum(
        [ord(char) for char in settings.SECRET_KEY]
    )
)

ACCESS_B36_PATH = {}
ACCESS_PATH_B36 = {}

def base36encode(number):
    is_negative = number < 0
    number = abs(number)

    alphabet, base36 = ["0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", ""]

    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    if is_negative:
        base36 = "-" + base36

    return base36 or alphabet[0]

def list_paths(directory):
    return [str(path) for path in Path(directory).rglob('*')]

def paths_concurrent(directories):
    paths = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(list_paths, dir): dir for dir in directories}
        for future in as_completed(futures):
            paths.extend(future.result())
    return paths

def generate_hashmaps():
    global ACCESS_B36_PATH, ACCESS_PATH_B36
    
    print("[.] Generating all paths...")
    paths = paths_concurrent(settings.SOURCES)
    print("[+] Done")
    
    ipath = 0
    while ipath < len(paths):
        base36 = base36encode(random.randint(0, 7958661109946400884391935))
        if not base36 in ACCESS_B36_PATH:
            print(f"[+] Appending: {base36} | {(ipath/len(paths))*100:.2f}%", end="\r")
            ACCESS_B36_PATH[base36] = paths[ipath]
            ipath += 1
        else:
            print(f"[!] Base36 number already exists! ({base36})")
    print("\n[+] Done")
    
    print("[.] Generating reverse hashmap")
    ACCESS_PATH_B36 = {
        path:base36 for base36, path in ACCESS_B36_PATH.items()
    }
    print("[+] Done | Ready to start")

def b36topath(base36):
    try:
        return ACCESS_B36_PATH[base36]
    except KeyError:
        return base36

def pathtob36(path):
    try:
        return ACCESS_PATH_B36[path]
    except KeyError:
        return path

def access(path):
    try:
        return ACCESS_B36_PATH[path]
    except KeyError:
        try:
            return ACCESS_PATH_B36[path]
        except KeyError:
            return False

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
    elif os.path.exists(get_source(path)):
        return sort(filter_items(os.listdir(get_source(path))))
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

generate_hashmaps()
