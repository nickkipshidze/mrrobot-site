from django.http import HttpResponse, FileResponse, StreamingHttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
import os, re, mimetypes
from datetime import datetime
from functools import wraps

from .utils import list_sources, list_item, get_source, is_directory
from . import utils
    
from . import settings

def securitycheck(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if kwargs.get("path") != None:
            path = get_source(kwargs.get("path"))
            if path != None and not utils.access(path):
                return HttpResponse("<h1>Access Denied</h1><p>You are not authorized to access requested resource on this server.</p>", status=403)
        return function(*args, **kwargs)
    return wrapper

def resolvepath(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if kwargs.get("path") != None:
            kwargs["path"] = utils.b36topath(
                kwargs.get("path")
            )
        return function(*args, **kwargs)
    return wrapper

def home(request):
    if request.method != "GET":
        return HttpResponse("Nope", status=403)
    
    if request.method == "GET":
        directories = {key:[] for key in list_sources() if is_directory(key)}
        
        for key in directories:
            for file in sorted(list_item(get_source(key))):
                directories[key].append(file)
        
        return render(request, "listing.html", {
            "directories": directories
        })

@resolvepath
@securitycheck
def openitem(request, path):
    full_path = get_source(path)
    
    if is_directory(full_path):
        directories = {path: list_item(full_path)} 
        
        return render(request, "listing.html", {
            "title": f"{path} Listing",
            "directories": directories,
            "path": path
        })
    
    elif "raw" in request.GET and request.GET["raw"] == "":
        return download(path=utils.pathtob36(full_path))
        
    elif full_path.endswith(settings.EXTS_MEDIA):
        return HttpResponseRedirect(f"/watch/{utils.pathtob36(full_path)}")
    
    elif full_path.endswith(settings.EXTS_IMAGES):
        return preview_image(path=utils.pathtob36(full_path))

    elif not utils.is_binay_file(full_path):
        return preview_text(path=utils.pathtob36(full_path))
    
    else:
        return download(path=utils.pathtob36(full_path))

@resolvepath
@securitycheck
def viewitem(request, path = None):
    if path:
        files = list_item(path)
        for i in range(len(files)): files[i] = os.path.join(path, files[i])
    else:
        files = list_sources()
        
    content = []
    
    for file in files:
        title = file.split("/")[-1]
        
        if is_directory(file): thumbnail = f"/open/{os.path.join(file, 'thumbnail.jpg')}?raw" if "thumbnail.jpg" in os.listdir(get_source(file)) else "/static/img/directory.png"
        elif file.endswith(settings.EXTS_MEDIA): thumbnail = "/static/img/mediafile.png"
        elif file.endswith(settings.EXTS_IMAGES): thumbnail = "/static/img/imagefile.png"
        else: thumbnail = "/static/img/unknown.png"
        
        if not is_directory(file):
            file_count = -1
            action = f"/open/{utils.pathtob36(get_source(file))}"
        else:
            file_count = str(sum([len(files) for root, dirs, files in os.walk(get_source(file))]))
            action = f"/view/{utils.pathtob36(get_source(file))}"
        
        upload_date = str(datetime.fromtimestamp(os.stat(get_source(file)).st_ctime).strftime("%Y/%m/%d"))
        
        content.append(
            {
                "title": title,
                "thumbnail": thumbnail,
                "action": action,
                "upload_date": upload_date,
                "file_count": file_count
            }
        )
        
    return render(request, "view.html", {
        "content": content
    })

def dbstat(request):
    available = 0
    capacity = 0
    
    for partition in settings.PARTITIONS:
        data = utils.get_partition_data(partition)
        available += data["avail"]
        capacity += data["size"]
    
    available = round(available / (1024**2), 2)
    capacity = round(capacity / (1024**2), 2)
        
    return render(request, "database.html", {
        "dircount": len(list_sources()),
        "partitions": len(settings.PARTITIONS),
        "available": available,
        "capacity": capacity,
        "percentage": round((available / capacity) * 100, 2),
    })

@resolvepath
@securitycheck
def watch(request, path):
    return render(request, "watch.html", {
        "video_path": path,
        "video_name": path.split("/")[-1][:-4]}
    )

@resolvepath
@securitycheck
def download(path):
    if not os.path.exists(path):
        return HttpResponseNotFound("<h1>File does not exist</h1>")
    
    content_type, _ = mimetypes.guess_type(path)
    if content_type is None:
        content_type = "application/octet-stream"
    
    try:
        response = FileResponse(open(path, "rb"), content_type=content_type)
        response["Content-Disposition"] = f"attachment; filename=\"{os.path.basename(path)}\""
        return response
    except IOError:
        raise HttpResponseNotFound("File does not exist")
    except Exception as error:
        print("[!]", error)
        raise HttpResponse("Unknown error occured", status=500)
    
@resolvepath
@securitycheck
def preview_image(path):
    path = utils.pathtob36(get_source(path))
    return HttpResponse(
        f"<body style=\"display: flex; align-items: center; justify-content: center; height: 100vh; background-color: #000; overflow: hidden;\"><img src=\"/open/{path}?raw\" style=\"background-color: white;\"/></body>"
    )

@resolvepath
@securitycheck
def preview_text(path):
    try:
        return HttpResponse(
            f"<pre>{open(path).read()}</pre>"
        )
    except IOError:
        return HttpResponse(
            f"<h1>Failed to read</h1>"
        )

@resolvepath
@securitycheck
def stream(request, path):
    file_path = os.path.join(get_source(path))
    
    if not os.path.exists(file_path):
        raise HttpResponseNotFound("Video not found!")

    file_size = os.path.getsize(file_path)
    content_type = "video/mp4"

    range_header = request.META.get("HTTP_RANGE", "").strip()
    range_match = re.match(r"bytes=(?P<start>\d+)-(?P<end>\d+)?", range_header)

    if range_match:
        start = int(range_match.group("start"))
        end = int(range_match.group("end")) if range_match.group("end") is not None else file_size - 1
        if end >= file_size:
            end = file_size - 1
        length = end - start + 1
        response = StreamingHttpResponse(open(file_path, "rb"), status=206, content_type=content_type)
        response["Content-Length"] = str(length)
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response.streaming_content = file_iterator(file_path, start, end)
    else:
        response = StreamingHttpResponse(open(file_path, "rb"), content_type=content_type)
        response["Content-Length"] = str(file_size)
        response["Accept-Ranges"] = "bytes"

    return response

def file_iterator(file_path, start, end, chunk_size=8192):
    with open(file_path, "rb") as file:
        file.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk_length = min(chunk_size, remaining)
            chunk = file.read(chunk_length)
            if not chunk:
                break
            yield chunk
            remaining -= chunk_length
