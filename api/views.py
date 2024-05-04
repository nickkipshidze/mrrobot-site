from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from mrrobot import utils, settings
from datetime import datetime
import os, mimetypes

class Ping(APIView):
    def get(self, request):
        return Response(
            status=status.HTTP_200_OK
        )
        
class Open(APIView):
    def get(self, request, path):
        content = []
        
        if path == "*":
            files = utils.list.sources()
        else:
            try:
                path = utils.hashsec.ACCESS_B36_PATH[path]
            except KeyError:
                try:
                    path = utils.hashsec.ACCESS_PATH_B36[path]
                except KeyError:
                    return Response(
                        data={"error": f"Path '{path}' is not found or access is denied."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            files = utils.list.paths(path)
        
        if path == "*" or utils.file.isdir(path):
            for file in files:
                title = file.split("/")[-1]
                
                if utils.file.isdir(file):
                    thumbnail = f"/api/open/{utils.hashsec.pathtob36(
                            utils.file.source(os.path.join(file, 'thumbnail.jpg'))
                        )}" \
                        if "thumbnail.jpg" in os.listdir(utils.file.source(file)) \
                            else "/static/img/directory.png"
                            
                elif file.endswith(settings.EXTS_MEDIA):
                    thumbnail = "/static/img/mediafile.png"
                    
                elif file.endswith(settings.EXTS_IMAGES):
                    thumbnail = "/static/img/imagefile.png"
                    
                else:
                    thumbnail = "/static/img/unknown.png"
                
                if not utils.file.isdir(file):
                    file_count = -1
                    action = f"/api/open/{utils.hashsec.pathtob36(utils.file.source(file))}"
                else:
                    file_count = str(sum([len(files) for root, dirs, files in os.walk(utils.file.source(file))]))
                    action = f"/api/open/{utils.hashsec.pathtob36(utils.file.source(file))}"
                    
                if utils.file.isdir(file):
                    filetype = "directory"
                elif file.endswith(settings.EXTS_MEDIA):
                    filetype = "video"
                elif file.endswith(settings.EXTS_IMAGES):
                    filetype = "image"
                elif utils.file.isbin(utils.file.source(file)):
                    filetype = "binary"
                else:
                    filetype = "unknown"
                
                upload_date = str(datetime.fromtimestamp(os.stat(utils.file.source(file)).st_ctime).strftime("%Y/%m/%d"))
                
                content.append(
                    {
                        "type": filetype,
                        "title": title,
                        "thumbnail": thumbnail,
                        "action": action,
                        "upload_date": upload_date,
                        "file_count": file_count
                    }
                )
            
            return Response(
                data={
                    "type": "directory",
                    "content": content
                },
                status=status.HTTP_200_OK
            )
            
        elif utils.file.isbin(path):
            content_type, _ = mimetypes.guess_type(path)
            if content_type is None:
                content_type = "application/octet-stream"
            
            try:
                response = FileResponse(open(path, "rb"), content_type=content_type)
                response["Content-Disposition"] = f"attachment; filename=\"{os.path.basename(path)}\""
                return response
            except IOError:
                return Response(
                    data={"error": "file does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as error:
                print("[!]", error)
                return Response(
                    data={"error": "unknown error occured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

