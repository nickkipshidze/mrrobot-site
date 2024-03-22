import os, re
from . import settings

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r"(\d+)", text)]

def sort(items):
    items.sort(key=natural_keys)
    return items

def list_sources():
    files = []
    for source in settings.SOURCES:
        for file in sort(os.listdir(source)):
            files.append(file)
    return files

def list_item(path):
    if os.path.exists(path):
        return sort(os.listdir(path))
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
