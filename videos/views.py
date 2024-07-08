from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from pytube import YouTube
from urllib.parse import urlencode
from django.urls import reverse
import io
import logging

# Set up logging
logger = logging.getLogger(__name__)

def searching(request):
    if request.method == "POST":
        url = request.POST.get('linkinp')
        if url:
            query_params = urlencode({'url': url})
            target_url = reverse('download') + f'?{query_params}'
            return redirect(target_url)
        else:
            logger.error("No URL provided in POST request")
            return redirect('goback_with_error')
    return render(request, "index.html")

def download(request):
    if request.method == "GET":
        url = request.GET.get('url')
        if url:
            try:
                obj = YouTube(url)
                title = obj.title
                thumbnail = obj.thumbnail_url
                data = {
                    "title": title,
                    "thumbnail": thumbnail,
                }
                return render(request, "download.html", data)
            except Exception as e:
                logger.error(f"Error fetching YouTube video: {e}")
                return redirect('goback_with_error')
        else:
            logger.error("No URL provided in GET request")
            return redirect('goback_with_error')

    elif request.method == "POST":
        url = request.GET.get('url')
        if url:
            try:
                obj = YouTube(url)
                title = obj.title

                # Determine the requested stream
                video_stream = None
                if '720p' in request.POST:
                    video_stream = obj.streams.filter(progressive=True, file_extension='mp4', res='720p').first()
                elif '360p' in request.POST:
                    video_stream = obj.streams.filter(progressive=True, file_extension='mp4', res='360p').first()
                elif '1080pns' in request.POST:
                    video_stream = obj.streams.filter(only_video=True, file_extension='mp4', res='1080p').first()
                elif '720pns' in request.POST:
                    video_stream = obj.streams.filter(only_video=True, file_extension='mp4', res='720p').first()
                elif '360pns' in request.POST:
                    video_stream = obj.streams.filter(only_video=True, file_extension='mp4', res='360p').first()
                elif 'audio' in request.POST:
                    video_stream = obj.streams.filter(only_audio=True, file_extension='mp4', abr='128kbps').first()

                if video_stream:
                    video_bytes = io.BytesIO()
                    video_stream.stream_to_buffer(video_bytes)
                    video_bytes.seek(0)
                    response = HttpResponse(video_bytes, content_type='video/mp4')
                    response['Content-Disposition'] = f'attachment; filename="{title}.mp4"'
                    response['X-Download-Success'] = 'true'
                    return response
                else:
                    logger.error("No suitable stream found")
                    return JsonResponse({'error': 'No suitable stream found'}, status=500)

            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                return JsonResponse({'error': 'Error downloading video'}, status=500)
        else:
            logger.error("No URL provided in POST request")
            return redirect('goback_with_error')

    return redirect('searching')

def goback_with_error(request):
    return render(request, "goback.html", {"error_message": "An error occurred. Please try again."})