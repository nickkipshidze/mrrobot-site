import os
from . import settings

def list_sources():
    files = []
    for source in settings.SOURCES:
        for file in sorted(os.listdir(source)):
            files.append(file)
    return files

def list_item(path):
    if os.path.exists(path):
        return sorted(os.listdir(path))
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
