from django.http import HttpResponse, FileResponse, StreamingHttpResponse, Http404, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
import os, re, mimetypes

sources = ["/source1/", "/source2/"]

def watch(request, path):
    return render(request, "watch.html", {
        "video_path": path,
        "video_name": path.split("/")[-1].strip(".mp4")}
    )

def list_sources():
    files = []
    for source in sources:
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
    
    for source in sources:
        if os.path.exists(os.path.join(source, item)):
            return os.path.join(source, item).__str__()
    return None

def is_directory(path):
    if path == None:
        return False
    
    if os.path.isdir(path):
        return True
    
    for source in sources:
        if os.path.isdir(os.path.join(source, path)):
            return True
        
    return False

def home(request):
    if request.method != "GET":
        return HttpResponse("Nope", status=403)
    
    if request.method == "GET":
        if request.GET.get("token") is None:
            return HttpResponse("Nope", status=403)
        
        if request.GET["token"] == "RXBpY0hhY2tlcnM6R2VvcmdlJk5pY2s=":
            directories = {key:[] for key in list_sources() if is_directory(key)}
            
            for key in directories:
                for file in sorted(list_item(get_source(key))):
                    directories[key].append(file)
            
            return render(request, "home.html", {
                "title": "Directory Listing",
                "directories": directories
            })
        else:
            return HttpResponse("Nope", status=403)

def openitem(request, path):
    file_path = get_source(path)
    
    if is_directory(file_path):
        directories = {path: list_item(file_path)} 
        
        return render(request, "home.html", {
            "title": f"{path} Listing",
            "directories": directories,
            "path": path
        })
        
    elif file_path.endswith("mp4"):
        return HttpResponseRedirect(f"/watch/{path}")
    
    else:
        if not os.path.exists(file_path):
            return HttpResponseNotFound("<h1>File does not exist</h1>")
        
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"
        
        try:
            response = FileResponse(open(file_path, "rb"), content_type=content_type)
            response["Content-Disposition"] = f"attachment; filename=\"{os.path.basename(path)}\""
            return response
        except IOError:
            raise Http404("File does not exist")

def stream(request, path):
    file_path = os.path.join(get_source(path))
    
    if not os.path.exists(file_path):
        raise Http404("Video not found!")

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
        resp = StreamingHttpResponse(open(file_path, "rb"), status=206, content_type=content_type)
        resp["Content-Length"] = str(length)
        resp["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        resp["Accept-Ranges"] = "bytes"
        resp.streaming_content = file_iterator(file_path, start, end)
    else:
        resp = StreamingHttpResponse(open(file_path, "rb"), content_type=content_type)
        resp["Content-Length"] = str(file_size)
        resp["Accept-Ranges"] = "bytes"

    return resp

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
