# Create your views here.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import time
import logging
import json
import requests

@csrf_exempt
def home(request):
    # print(request.POST)

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


    if success:
        graded = json.loads(graded)

        # import ipdb
        # ipdb.set_trace()

        feedback = graded.get('feedback')[0].get('explanation', '<p>No Explanation</p>').strip().encode('ascii', 'ignore')

        # Needs to be enclosed within <p>...</p> tags and <br> must be <br/>
        feedback = '<p><br/><font style="color:green; font-weight:bold;">Correct</font><br/><br/>Your Query Result: <table border="1" style="font-size:90%; padding: 1px;border-spacing: 0px; border-collapse: separate"><tr><td>E.T.</td></tr><tr><td>Raiders of the Lost Ark</td></tr></table><br/>Expected Query Result: <table border="1" style="font-size:90%; padding: 1px;border-spacing: 0px; border-collapse: separate"><tr><td>E.T.</td></tr><tr><td>Raiders of the Lost Ark</td></tr></table></p>'

        # feedback = '<br/><p><table><tr><td>Wooo</td></tr></table></p>'
        # Look @ html5lib, beautifulsoup


        # What is the grader_id suppose to be?
        xqueue_header, xqueue_body = util.create_xqueue_header_and_body(content_header['submission_id'], content_header['submission_key'], graded.get('score', 0), graded.get('maximum-score', 0), feedback, 'reference_dummy_grader')
        # xqueue_header, xqueue_body = util.create_xqueue_header_and_body(content_header['submission_id'], content_header['submission_key'], graded.get('score', 0), graded.get('maximum-score', 0), '<p>No Explanation</p>', 'reference_dummy_grader')

    # Post results back to XQueue
    # (success, msg) = util.post_results_to_xqueue(session, json.dumps(xqueue_header), json.dumps(xqueue_body))

    if success:
        print("successfully posted result back to xqueue")


    # print("\n---\n")
    # print(request.body)
    return HttpResponse('{"correct": true, "score": 1, "msg": "<p>Great! You got the right answer!</p>"}')




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