import os, re, random, pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import settings

random.seed(
    sum(
        [ord(char) for char in settings.SECRET_KEY]
    )
)

def natsort(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split("(\d+)", s)] 

def sort(items):
    return sorted(items, key=natsort)

def filter_items(items):
    filtered = []
    for item in items:
        try:
            if not (file.isdir(item) and ".mrignore" in os.listdir(file.source(item))):
                filtered.append(item)
        except PermissionError:
            continue
    return filtered

class hashsec:
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

    def paths_concurrent(directories):
        paths = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(list.paths, dir): dir for dir in directories}
            for future in as_completed(futures):
                paths.extend(future.result())
        return paths

    def generate(update=False):        
        if os.path.exists(settings.CACHEPATH):
            try:
                hashsec.load(settings.CACHEPATH)
                if not update: return True
            except Exception as error:
                print(f"[!] Error occured while importing cache: {error}")
                
        if update: print("[.] Updating hashmaps...")
        
        print("[.] Generating all paths...")
        paths = hashsec.paths_concurrent(settings.SOURCES)
        
        ipath = 0
        while ipath < len(paths):
            base36 = hashsec.base36encode(random.randint(0, 7958661109946400884391935))
            if not paths[ipath] in hashsec.ACCESS_PATH_B36:
                if not base36 in hashsec.ACCESS_B36_PATH:
                    print(f"[+] Appending: {base36} | {(ipath/len(paths))*100:.2f}%", end="\r")
                    hashsec.ACCESS_B36_PATH[base36] = paths[ipath]
                else:
                    print(f"[!] Base36 number already exists! ({base36})", end="\r")
                    ipath -= 1
            else:
                print(f"[+] Skipping: {hashsec.ACCESS_PATH_B36[paths[ipath]]} | {(ipath/len(paths))*100:.2f}%", end="\r")
            ipath += 1
        print(end="\n")
        
        print("[.] Generating reverse hashmap")
        hashsec.ACCESS_PATH_B36 = {
            path:base36 for base36, path in hashsec.ACCESS_B36_PATH.items()
        }
        
        print(f"[.] Writing generated data to cache file ({settings.CACHEPATH})")
        hashsec.write(settings.CACHEPATH)
        
        print("[+] Done | Finished generating hashmaps" if not update else "[+] Done | Finished updating hashmaps")
        
    def write(path):
        pickle.dump({
            "PATH_B36": hashsec.ACCESS_PATH_B36,
            "B36_PATH": hashsec.ACCESS_B36_PATH
        }, open(path, "wb"))
        print(f"[+] Wrote to cache")
    
    def load(path):
        print(f"[.] Importing cache ({path})")
        cache = pickle.load(open(path, "rb"))
        hashsec.ACCESS_PATH_B36 = cache["PATH_B36"]
        print("[+] Imported ACCESS_B36_PATH")
        hashsec.ACCESS_B36_PATH = cache["B36_PATH"]
        print("[+] Imported ACCESS_PATH_B36")
        print("[+] Done | Finished importing from cache")
        
    def prune():
        print(f"[.] Cleaning hashmap... ({len(hashsec.ACCESS_PATH_B36.keys())})")
        
        ACCESS_PATH_B36 = hashsec.ACCESS_PATH_B36.copy()
        ACCESS_B36_PATH = hashsec.ACCESS_B36_PATH.copy()
        
        for path, base36 in hashsec.ACCESS_PATH_B36.items():
            try:
                file.source(path)
                continue
            except (FileNotFoundError, FileExistsError):
                print(f"[-] Removing {base36} : {path}")
                ACCESS_PATH_B36.pop(path)
                ACCESS_B36_PATH.pop(base36)
                
        hashsec.ACCESS_PATH_B36 = ACCESS_PATH_B36.copy()
        hashsec.ACCESS_B36_PATH = ACCESS_B36_PATH.copy()
        
        print(f"[+] Finished ({len(hashsec.ACCESS_PATH_B36.keys())})")
        hashsec.write(path=settings.CACHEPATH)
        print(end="\n")

    def b36topath(base36):
        try:
            return hashsec.ACCESS_B36_PATH[base36]
        except KeyError:
            raise FileNotFoundError(f"Code '{base36}' not found in ACCESS_B36_PATH. Did you mean to call 'file.source'")

    def pathtob36(path):
        try:
            return hashsec.ACCESS_PATH_B36[path]
        except KeyError:
            raise FileNotFoundError(f"Path '{path}' not found in ACCESS_PATH_B36. Did you mean to call 'file.source'")

    def access(path):
        try:
            return hashsec.ACCESS_B36_PATH[path]
        except KeyError:
            try:
                return hashsec.ACCESS_PATH_B36[path]
            except KeyError:
                return False

class list:
    def sources():
        files = []
        for source in settings.SOURCES:
            for file in sort(os.listdir(source)):
                files.append(file)
        return filter_items(files)
    
    def items(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' not found. Did you mean to call 'file.source'")
        elif not file.isdir(path):
            raise NotADirectoryError(f"File '{path}' is not a directory")
        else:
            return sort(filter_items([os.path.join(path, file) for file in os.listdir(path)]))
        
    def paths(directory):
        return [str(path) for path in Path(directory).rglob('*')]
    
class file:
    def isbin(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' not found. Did you mean to call 'file.source'")
        
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
        
    def isdir(path):
        if os.path.isdir(path):
            return True
        elif os.path.isdir(file.source(path)):
            return True
        return False

    def source(path):        
        if not os.path.exists(path):
            for source in settings.SOURCES:
                if os.path.exists(os.path.join(source, path)):
                    path = os.path.join(source, path)
                    break
            else:
                raise FileNotFoundError(f"File '{path}' was not found.")
        
        for source in settings.SOURCES:
            if path[:len(source)] == source:
                break
        else:
            raise FileExistsError(f"File '{path}' exists, but not in any of the sources.")
        
        return path

def partdat(filesystem = None, mount = None):
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

hashsec.generate(update=True)
hashsec.prune()
