from django.http import HttpResponse, HttpRequest

def health(request: HttpRequest):
    response = HttpResponse()
    response.status_code = 200

    return response
