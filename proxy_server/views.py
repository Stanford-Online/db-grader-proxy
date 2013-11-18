# Create your views here.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def home(request):
    print(request.POST)
    print("\n---\n")
    print(request.body)
    return HttpResponse('{"correct": true, "score": 1, "msg": "<p>Great! You got the right answer!</p>"}')
