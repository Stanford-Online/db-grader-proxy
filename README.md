db-grader-proxy
===============

Simple proxy that forwards grading requests with a student's database query to the grader server, and formats the resulting feedback response to be HTML safe before forwarding the response back. 

Grading Feedback Format
=======================

In formating the grading feedback response HTML, all tags but the following are stripped: 

`p, br, font, table, tbody, tr, td, i, pre, em`

Further, all styling and attributes but the following are stripped: 

`Tag Attributes: style, border`

`Styles: color, font-weight, font-size, padding, border-spacing, border-collapse`

If more tags, attributes, or styles are desired, these lists can be easily updated in the corresponding constants in proxy_server/views.py

Tests
=====
To run tests, which focus on the html sanitization of the grader response, say: 

`python manage.py test`

The tests that are run can be found and editted in /proxy_server/tests.py

