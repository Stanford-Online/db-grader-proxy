# Create your views here.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import time
import logging
import json
import requests
import re

@csrf_exempt
def home(request):
    # import ipdb
    # ipdb.set_trace()

    content = json.loads(request.body)
    body = json.loads(content['xqueue_body'])

    student_info = json.loads(body.get('student_info', '{}'))
    email = student_info.get('student_email', '')
    print("submitted by email: " + email)

    # the 'grader_payload' dict is the dictionary to send to the grader
    grader_payload = json.loads(body['grader_payload'])
    student_response = body.get('student_response', '')
    grader_payload['student_input'] = student_response

    # session = util.xqueue_login()
    REQUESTS_TIMEOUT = 20
    (success, graded) = postRequest('http://grade.prod.c2gops.com/AJAXPostHandler.php', grader_payload, REQUESTS_TIMEOUT)

    feedback = "<p>Whoops, your response wasn't successfully graded. Please contact course staff is problem persists.</p>"
    isCorrect = "false"
    score = "0"

    if success:
    	# print("Successfully returned from the grader")

        graded = json.loads(graded)

        score = str(graded.get('score', 0))
        maxScore = str(graded.get('maximum-score', 1))
        isCorrect = "true" if score == maxScore else "false"

        import ipdb
        ipdb.set_trace()

        # Consider re instead of a bunch of calls to replace function
        feedback = graded.get('feedback')[0].get('explanation', '<p>No Explanation</p>').strip().encode('ascii', 'ignore')
        feedback = "<p>" + feedback.replace("\"", "'").replace("<br>", "<br/>").replace("\n", "<br/>") + "</p>"

        ipdb.set_trace()

    return HttpResponse('{"correct": ' + isCorrect + ', "score": ' + score + ', "msg": "' + feedback + '"}')





def postRequest(url, data, timeout):
    '''
        Contact grading controller, but fail gently.
        Takes following arguments:
        url - url to post to
        data - dictionary with data to post
        timeout - timeout in settings
        
        Returns (success, msg), where:
        success: Flag indicating successful exchange (Boolean)
        msg: Accompanying message; Controller reply when successful (string)
        '''
    
    try:
        r = requests.post(url, data=data, timeout=timeout, verify=False)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        error_message = 'Could not connect to server at %s in timeout=%f' % (url, timeout)
        log.error(error_message)
        return (False, error_message)
            
    if r.status_code == 500 and url.endswith("/"):
        r = session.post(url[:-1], data=data, timeout=timeout, verify=False)
    
    if r.status_code not in [200]:
        error_message = "Server %s returned status_code=%d' % (url, r.status_code)"
        log.error(error_message)
        return (False, error_message)
    
    if hasattr(r, "text"):
        text = r.text
    elif hasattr(r, "content"):
        text = r.content
    else:
        error_message = "Could not get response from http object."
        log.exception(error_message)
        return False, error_message
    
    return (True, text)