from django.test import TestCase
from views import sanitizeFeedback, truncateFeedback
from mock import patch


class FeedbackSanitizationTests(TestCase):
    """
    Ensure that grading feedback has proper html formatting
    """
    def setUp(self):
        self.needSanitization = [
            ("<p>Test", "<p>Test</p>"),
            ("<p><br>Test</p>", "<p><br/>Test</p>"),
            ("&&", "&amp;&amp;"),
            ("<br>", "<br/>"),
            ("&&&&", "&amp;&amp;&amp;&amp;"),
            ("<p>&&''", "<p>&amp;&amp;''</p>"),
            ("<", "&lt;"),
            ("\"", "'"),      #edX expects single quotes when defining attributes
            ("<class><p>Test</p>", "<p>Test</p>"),
            ("\r", ""),
            ("\n", "<br/>"),
            ("<><><><><><>", "&lt;&gt;&lt;&gt;&lt;&gt;&lt;&gt;&lt;&gt;&lt;&gt;"),
            ("<table>", "<table></table>"),
            ("<i>hey, fix this<", "<i>hey, fix this&lt;</i>")
        ]

        self.noSanitizingNeeded = [
            "", 
            " ",
            "Hello",
            "<p>Test</p>",
            "<font style='color: red;'></font>", 
            "<table><tbody><tr><td></td></tr></tbody></table>",
            "<i>This is fine</i>"
        ]

    @patch('proxy_server.tests.sanitizeFeedback', side_effect= lambda x:x)
    def test_lack_of_sanitization_function(self, mock_function):
        """
        Confirm that lack of html cleaning/escaping causes errors
        """
        for (broken, clean) in self.needSanitization:
            self.assertNotEqual(clean, sanitizeFeedback(broken))        

    def test_sanitization_function(self):
        """
        Sanitize function should return properly formatted html
        """
        for (broken, clean) in self.needSanitization:
            self.assertEquals(clean, sanitizeFeedback(broken))

        for test in self.noSanitizingNeeded:
            self.assertEquals(test, sanitizeFeedback(test))
            
    def test_ampersand_properly_escaped(self):
        """
        Ampersands should be properly escaped
        """
        test_string = "<p>This contains an ampersand right here '&'</p>"
        cleaned = sanitizeFeedback(test_string)
        self.assertIn("&amp;", cleaned)

    def test_style_maintained(self):
        """
        Inline styling should be maintained
        """
        test_string = "<p><font style='color: red'></p>"
        cleaned = sanitizeFeedback(test_string)
        self.assertIn("style='color: red;'", cleaned)

        test_string = "<p><table border=\"1\"></table></p>"
        cleaned = sanitizeFeedback(test_string)
        self.assertIn("border='1'", cleaned)

    def test_single_quotes_returned(self):
        """
        Single quotes should be used when stating tag attributes
        """
        test_string = "<p style=\"font-weight: bold;\">Test</p>"
        cleaned = sanitizeFeedback(test_string)
        self.assertIn("'", cleaned)
        self.assertEqual(cleaned, 
             "<p style='font-weight: bold;'>Test</p>"
        )


class FeedbackTruncationTest(TestCase):
    """
    Ensure feedback well-formed after truncation
    """
    def setUp(self):
        self.simpleTestString = self.buildLongString()
        self.complicatedString = self.buildComplexLongString()
        self.tags = [
            ('<p', '</p'), 
            ('<table', '</table'), 
            ('<tbody', '</tbody'), 
            ('<tr', '</tr'), 
            ('<td', '</td'), 
            ('<font', '</font')
        ]
        
    def buildLongString(self):
        """
        Constructs simple string similar to grader feedback
        """
        result = "<p><table><tbody>"
        while len(result) < 16100:
            result += "<tr><td><p>Test</p></td></tr>"
        result += "</tbody></table></p>"
        return result

    def buildComplexLongString(self):
        """
        Constructs complex string similar to grader feedback
        """
        result = "<p><table><tbody>"
        while len(result) < 16100:
            result += "<tr><td><font style='font-weight: bold;'>"
            result += "Test</font></td></tr>"
        result += "</tbody></table></p>"
        return result

    def test_truncates_to_correct_size(self):
        """
        Truncated feedback must be less than max length
        """
        truncated = truncateFeedback(self.simpleTestString)
        self.assertTrue(len(truncated) < 16000)
        truncated = truncateFeedback(self.complicatedString)
        self.assertTrue(len(truncated) < 16000)

    def test_truncated_feedback_well_formed(self):
        """
        Truncated feedback must still be well-formed
        """
        simpleTruncated = truncateFeedback(self.simpleTestString)
        complexTruncated = truncateFeedback(self.complicatedString)
        for (openTag, closedTag) in self.tags:
            self.assertNumTagsEqual(openTag, closedTag, simpleTruncated)
            self.assertNumTagsEqual(openTag, closedTag, complexTruncated)

    def test_diffrent_truncation_points_properly_fixed(self):
        """
        Test different malformities after truncation
        """
        for index in range(15990, 16000):
            simpletest = self.simpleTestString[0:index]
            lastIndex = simpletest.rfind(">")
            simpletest = simpletest[0:lastIndex + 1]
            simpletest = sanitizeFeedback(simpletest)
            complextest = self.complicatedString[0:index]
            lastIndex = complextest.rfind(">")
            complextest = complextest[0:lastIndex + 1]
            complextest = sanitizeFeedback(complextest)
            for (openTag, closedTag) in self.tags:
                self.assertNumTagsEqual(openTag, closedTag, simpletest)
                self.assertNumTagsEqual(openTag, closedTag, complextest)
            
    def assertNumTagsEqual(self, openTag, closedTag, htmlstring):
        numOpen = htmlstring.count(openTag)
        numClosed = htmlstring.count(closedTag)
        self.assertEqual(numOpen, numClosed)


            
        
        

    
        


    
