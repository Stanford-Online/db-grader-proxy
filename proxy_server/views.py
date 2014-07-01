# Implementation of the db_grader_proxy server
# Forwards requests containing student db queries to be graded to grader server
# Html formats/sanitizes response and returns to server 

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import time
import logging
import json
import requests
import re
import bleach 


MAX_FEEDBACK_LENGTH = 16000
FEEDBACK_TRIM_LENGTH = 15900
FEEDBACK_TAGS = ['p', 'br', 'font', 'table', 'tbody', 'tr', 'td', 'i', "pre", "em"]
FEEDBACK_ATTRS = { '*' : ['style', 'border'] } # hash of tag name --> allowed attributes
FEEDBACK_STYLES = ['color', 'font-weight', 'font-size', 'padding', 'border-spacing', 'border-collapse']
log = logging.getLogger(__name__)


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
    
    (success, msg) = postRequest(settings.DB_GRADER, grader_payload, settings.REQUESTS_TIMEOUT)

    feedback = "<p>Whoops, your response wasn't successfully graded. Please contact course staff if the problem persists. Specific error: <b>%s</b></p>" % (msg)
    isCorrect = "false"
    score = "0"

    # If successful post request, then return information from grader
    if success:
        graded = json.loads(msg)
        score = str(graded.get('score', 0))
        maxScore = str(graded.get('maximum-score', 1))
        isCorrect = "true" if score == maxScore else "false"

        # Get feedback field from grader
        feedback = graded.get('feedback')[0].get('explanation', '<p>No Explanation</p>').strip().encode('ascii', 'ignore')

        # Clean up feedback to be html safe and well formatted for EdX 
        feedback = re.sub(r'<class \'sqlite3\..*\'>', '', feedback)
        feedback = sanitizeFeedback(feedback)

        # Trim if feedback too long
        if len(feedback) > MAX_FEEDBACK_LENGTH:
            feedback = truncateFeedback(feedback)

    return HttpResponse('{"correct": ' + isCorrect + ', "score": ' + score + ', "msg": "' + feedback + '"}')

def truncateFeedback(feedback):
    """
    Trims feedback to an acceptable length for displaying
    """
    tmp = "<p>Message Too Long. Here is a snapshot:"

    feedback = feedback[0:FEEDBACK_TRIM_LENGTH]
    lastIndex = feedback.rfind(">")
    feedback = feedback[0:lastIndex + 1]

    # Now sanitize the newly trimmed html, to fix mismatched tags
    feedback = sanitizeFeedback(feedback)
    feedback = tmp + feedback + "</p>"
    
    return feedback
    
def sanitizeFeedback(feedback):
    """
    Cleans the html feedback string, ensuring proper escaping
    """
    feedback = feedback.replace('\r', '')
    feedback = re.sub('<!', '&lt;!', feedback) # clean for DTD/XML syntax so those error messages aren't stripped 
    feedback = bleach.clean(feedback, FEEDBACK_TAGS, FEEDBACK_ATTRS, FEEDBACK_STYLES)

    # Bleach uncloses br tags, switches single quotes with doubles. 
    # Also replace any new lines with break tags, and backslashs that break XML/DTD
    feedback = feedback.replace("\n", "<br/>").replace("<br>", "<br/>").replace("\"", "\'").replace("\\", "")

    return feedback


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

    code2description = {}
    code2description[500] = "Internal Server Error"
    code2description[502] = "Bad Gateway"
    code2description[503] = "Service Unavailable"
    code2description[504] = "Gateway Timeout"
    code2description[505] = "Version Not Supported"
    code2description[400] = "Bad Request"
    code2description[401] = "Unathorized"
    code2description[403] = "Forbidden"
    code2description[404] = "Not Found"
    code2description[408] = "Request Timeout"
    
    try:
        r = requests.post(url, data=data, timeout=timeout, verify=False)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        error_message = 'Could not connect to server at %s in timeout: %f' % (url, timeout)
        log.error(error_message)
        return (False, error_message)
            
    # if r.status_code == 500 and url.endswith("/"):
    #     r = session.post(url[:-1], data=data, timeout=timeout, verify=False)
    
    if r.status_code not in [200]:
        description = ''
        if r.status_code in code2description:
            description = ' - %s' % (code2description[r.status_code])
        error_message = 'The server returned status code %d%s' % (r.status_code, description)
        log.error(error_message)
        return (False, error_message)
    
    if hasattr(r, "text"):
        text = r.text
    elif hasattr(r, "content"):
        text = r.content
    else:
        error_message = "Could not get response from HTTP object."
        log.exception(error_message)
        return False, error_message
    
    return (True, text)
