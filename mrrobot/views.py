from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.shortcuts import render
import os, re

sources = ["/source1/", "/source2/"]

def watch(request, path):
    return render(request, "watch.html", {
        "video_path": path,
        "video_name": path.split("/")[-1].strip(".mp4")}
    )

def list_sources():
    files = []
    for source in sources:
        for file in os.listdir(source):
            files.append(file)
    return files

def list_item(path):
    if os.path.exists(path):
        return os.listdir(path)
    return []

def get_source(item):
    for source in sources:
        if os.path.exists(os.path.join(source, item)):
            return os.path.join(source, item).__str__()
    return None

def is_directory(path):
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
                    if file.endswith(".mp4"):
                        directories[key].append(file)
            
            return render(request, "home.html", {"directories": directories})
        else:
            return HttpResponse("Nope", status=403)

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
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk_length = min(chunk_size, remaining)
            chunk = f.read(chunk_length)
            if not chunk:
                break
            yield chunk
            remaining -= chunk_length
