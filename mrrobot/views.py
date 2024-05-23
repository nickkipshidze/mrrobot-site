from django.http import HttpResponse, FileResponse, StreamingHttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
import os, re, mimetypes
from datetime import datetime
from functools import wraps

from .utils import list as utlist
from .utils import file as utfile
from .utils import hashsec as hs
from . import utils
    
from . import settings

def securitycheck(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if kwargs.get("path") != None:
            path = utfile.source(kwargs.get("path"))
            if path != None and not utils.hashsec.access(path):
                return HttpResponse("<h1>Access Denied</h1><p>You are not authorized to access requested resource on this server.</p>", status=403)
            elif path == None and kwargs.get("path") != None:
                return HttpResponseNotFound("<h1>Not found</h1><p>The requested resource was not found on this server.</p>")
        return function(*args, **kwargs)
    return wrapper

def resolvepath(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if kwargs.get("path") != None:
            try:
                kwargs["path"] = hs.b36topath(
                    kwargs.get("path")
                )
            except FileNotFoundError:
                return HttpResponseNotFound("<h1>Not found</h1><p>The requested resource was not found on this server.</p>")
        return function(*args, **kwargs)
    return wrapper

def home(request):
    if request.method != "GET":
        return HttpResponse("Nope", status=403)
    
    if request.method == "GET":
        directories = {key:[] for key in utlist.sources() if utfile.isdir(key)}
        
        for key in directories:
            for file in sorted(utlist.items(utfile.source(key))):
                directories[key].append(file)
        
        return render(request, "listing.html", {
            "directories": directories
        })

@resolvepath
@securitycheck
def openitem(request, path):
    full_path = utfile.source(path)
    
    if utfile.isdir(full_path):
        directories = {path: utlist.items(full_path)} 
        
        return render(request, "listing.html", {
            "title": f"{path} Listing",
            "directories": directories,
            "path": path
        })
    
    elif "raw" in request.GET and request.GET["raw"] == "":
        return download(path=hs.pathtob36(full_path))
        
    elif full_path.endswith(settings.EXTS_MEDIA):
        return HttpResponseRedirect(f"/watch/{hs.pathtob36(full_path)}")
    
    elif full_path.endswith(settings.EXTS_IMAGES):
        return preview_image(path=hs.pathtob36(full_path))

    elif not utfile.isbin(full_path):
        return preview_text(path=hs.pathtob36(full_path))
    
    else:
        return download(path=hs.pathtob36(full_path))

@resolvepath
@securitycheck
def viewitem(request, path = None):
    if path:
        files = utlist.items(path)
        for i in range(len(files)): files[i] = os.path.join(path, files[i])
    else:
        files = utlist.sources()
        
    content = []
    
    for file in files:
        title = file.split("/")[-1]
        
        if utfile.isdir(file): thumbnail = f"/open/{hs.pathtob36(utfile.source(os.path.join(file, 'thumbnail.jpg')))}?raw" if "thumbnail.jpg" in os.listdir(utfile.source(file)) else "/static/img/directory.png"
        elif file.endswith(settings.EXTS_MEDIA): thumbnail = "/static/img/mediafile.png"
        elif file.endswith(settings.EXTS_IMAGES): thumbnail = "/static/img/imagefile.png"
        else: thumbnail = "/static/img/unknown.png"
        
        if not utfile.isdir(file):
            file_count = -1
            action = f"/open/{hs.pathtob36(utfile.source(file))}"
        else:
            file_count = str(sum([len(files) for root, dirs, files in os.walk(utfile.source(file))]))
            action = f"/view/{hs.pathtob36(utfile.source(file))}"
        
        upload_date = str(datetime.fromtimestamp(os.stat(utfile.source(file)).st_ctime).strftime("%Y/%m/%d"))
        
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
        data = utils.partdat(partition)
        available += data["avail"]
        capacity += data["size"]
    
    available = round(available / (1024**2), 2)
    capacity = round(capacity / (1024**2), 2)
        
    return render(request, "database.html", {
        "dircount": len(utlist.sources()),
        "partitions": len(settings.PARTITIONS),
        "available": available,
        "capacity": capacity,
        "percentage": round((available / capacity) * 100, 2),
    })

def about(request):
    return render(request, "about.html")

@resolvepath
@securitycheck
def watch(request, path):
    return render(request, "watch.html", {
        "video_path": hs.pathtob36(path),
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
    path = hs.pathtob36(utfile.source(path))
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
    file_path = os.path.join(utfile.source(path))
    
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
