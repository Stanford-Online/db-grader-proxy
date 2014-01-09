# Create your views here.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import time
import logging
import json
import requests
import re

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

        # Consider re instead of a bunch of calls to replace function
        # Alternatively, could change PHP code to correct returned XML/HTML

        # Get feedback field from grader
        feedback = graded.get('feedback')[0].get('explanation', '<p>No Explanation</p>').strip().encode('ascii', 'ignore')

        # Format to something that EdX will not complain about
        feedback = "<p>" + feedback.replace("\"", "'").replace("<br>", "<br/>").replace("\n", "<br/>").replace("<pre/>", "<pre>").replace("\\", "&#92;") + "</p>"
        feedback = re.sub(r'<class \'sqlite3\..*\'>', '', feedback)

        # Change all to &lttt; (this allows any original &lt; to not be lumped in here)
        feedback = re.sub(r'<', '&lttt;', feedback)

        # Change back to < for those we want
        feedback = re.sub(r'&lttt;(br/|p|pre|font|i|font|table|th|tr|td)', r'<\1', feedback)
        feedback = re.sub(r'&lttt;/(p|pre|font|i|font|table|th|tr|td)>', r'</\1>', feedback)
        feedback = re.sub(r'&lttt;', '&lt;', feedback)

        # Make sure there are no <br/> inside <pre>...</pre> block
        # parts = feedback.split("pre>")
        # if len(parts) > 0:
        #     # Odd-indexed parts are within a pre block
        #     for i in range(1, len(parts), 2):
        #         parts[i] = re.sub(r'<br/>', '</pre><pre>', parts[i])
        #     feedback = "pre>".join(parts)

        # # Ensure no empty <pre>...</pre> blocks
        # feedback = re.sub(r'<pre></pre>', '', feedback)

        # If feedback too long
        if len(feedback) > 16000:
            tmp = "<p>Message Too Long. Here is a snapshot:"

            feedback = feedback[0:15900]
            lastIndex = feedback.rfind(">")
            feedback = feedback[0:lastIndex + 1]

            if feedback.count('pre>') % 2 == 1:
                feedback += "</pre>"
            if feedback.count('<font') != feedback.count('</font'):
                feedback += "</font>"
            if feedback.count('<td') != feedback.count('</td'):
                feedback += "</td>"
            if feedback.count('<tr') != feedback.count('</tr'):
                feedback += "</tr>"
            if feedback.count('<table') != feedback.count('</table'):
                feedback += "</table>"
            if feedback.count('p>') % 2 == 1:
                feedback += "</p>"
            feedback = tmp + feedback + "</p>"

        elif feedback.count('<font') != feedback.count('</font'):
            feedback = feedback[0:len(feedback)-4] + "</font></p>"

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