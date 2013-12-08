# Create your views here.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import time
import logging
import json
import requests
import re

@csrf_exempt
def home(request):
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
    
    # (success, msg) = postRequest(settings.DB_GRADER, grader_payload, settings.REQUESTS_TIMEOUT)
    (success, msg) = postRequest('http://httpstat.us/500', grader_payload, settings.REQUESTS_TIMEOUT)

    feedback = "<p>Whoops, your response wasn't successfully graded. Please contact course staff is problem persists. Specific error: %s</p>" % (msg)
    isCorrect = "false"
    score = "0"

    # If successful post request, then return information from grader
    if success:
        graded = json.loads(msg)
        score = str(graded.get('score', 0))
        maxScore = str(graded.get('maximum-score', 1))
        isCorrect = "true" if score == maxScore else "false"

        import ipdb
        ipdb.set_trace()

        # Consider re instead of a bunch of calls to replace function
        # Alternatively, could change PHP code to correct returned XML/HTML

        # Get feedback field from grader
        feedback = graded.get('feedback')[0].get('explanation', '<p>No Explanation</p>').strip().encode('ascii', 'ignore')

        # Format to something that EdX will not complain about
        feedback = "<p>" + feedback.replace("\"", "'").replace("<br>", "<br/>").replace("\n", "<br/>").replace("<pre/>", "<pre>") + "</p>"
        feedback = re.sub(r'<class \'sqlite3\..*\'>', '', feedback)

    return HttpResponse('{"correct": ' + isCorrect + ', "score": ' + score + ', "msg": "' + feedback + '"}')


# TODO: Change "Queued..." in UI to something like "Checking"

# TODO: Demonstrate 503 (and other error codes sent back) from grader is responded correctly!
# On same machine as graders; run server on localhost
# Proxy goes on 8000, not 80
# Don't use runServer -- look at nGINx - gUNICORN -- ask Jason about this!

# Generally, check this request to make sure it makes sense
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