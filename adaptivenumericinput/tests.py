"""
Module To Test AdaptiveNumericInput
"""
import json
import unittest
import ddt

from mock import MagicMock, Mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xblock.field_data import DictFieldData
from xblock.validation import ValidationMessage

from .adaptivenumericinput import AdaptiveNumericInput
from .adaptivenumericinput import FEEDBACK_LIST
from .adaptivenumericinput import _answer_error
from .adaptivenumericinput import _get_float
from .adaptivenumericinput import _read_scenario_files

from .utils import _


class TestData(object):
    # pylint: disable=too-few-public-methods
    """
    Module helper for validate_field_data
    """
    weight = 0
    max_attempts = 0


class TestRequest(object):
    # pylint: disable=too-few-public-methods
    """
    Module helper for @json_handler
    """
    method = None
    body = None
    success = None


@ddt.ddt
class AdaptiveNumericInputTestCase(unittest.TestCase):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # pylint: disable=too-many-lines
    """
    A complete suite of unit tests for the Adaptive Numeric Input XBlock
    """
    @classmethod
    def make_an_xblock(cls, **kw):
        """
        Helper method that creates a Adaptive Numeric Input XBlock
        """
        course_id = SlashSeparatedCourseKey('foo', 'bar', 'baz')
        runtime = Mock(course_id=course_id)
        scope_ids = Mock()
        field_data = DictFieldData(kw)
        xblock = AdaptiveNumericInput(runtime, field_data, scope_ids)
        xblock.xmodule_runtime = runtime
        return xblock

    def setUp(self):
        """
        Creates an xblock
        """
        self.xblock = AdaptiveNumericInputTestCase.make_an_xblock()

    @ddt.data(
        # actual_answer, answer, result(absolute_error, percent_error))
        (None, 9.0, (None, None)),
        (9.0, None, (None, None)),
        (10.0, 9.0, (1.0, 10.0)),
        (-10.0, 9.0, (19.0, 190.0)),
        (10.0, -9.0, (19.0, 190.0)),
        (-10.0, -9.0, (1.0, 10.0)),
        (0.0, 1.0, (1.0, None)),
        (0.0, 0.0, (0.0, None)),
    )
    @ddt.unpack
    def test__answer_error(
            self,
            actual_answer,
            answer,
            result,
    ):
        """
        Test _answer_error returns correct tuple
        """
        test_result = _answer_error(actual_answer, answer)
        self.assertTupleEqual(result, test_result)

    @ddt.data(
        # value to convert, result
        (None, None),
        ('asdf', None),
        ('10', 10.0),
        ('-10', -10.0),
        (10, 10.0),
        (-10, -10.0),
        ('.123987', 0.123987),
    )
    @ddt.unpack
    def test__get_float(self, value, result):
        """
        Test _get_float returns correct values
        """
        test_result = _get_float(value)
        self.assertEqual(result, test_result)

    def test__read_scenario_files(self):
        """
        Test _read_scenario_files returns correct file
        """
        test_str = '<sequence_demo><adaptivenumericinput />'
        test_result = _read_scenario_files()
        self.assertEqual(test_str, test_result[0:len(test_str)])

    def test_build_fragment(self):
        """
        Checks if fragment returned from build_fragment
        has correct elements in correct locations
        """
        fragment_js = 'AdaptiveNumericInputView'
        html_source = AdaptiveNumericInput.get_resource_string('view.html')
        public_path = '/resource/adaptivenumericinput/public'
        path_css = "{public_path}/{path}".format(
            public_path=public_path,
            path='view.less.min.css',
        )
        path_js = "{public_path}/{path}".format(
            public_path=public_path,
            path='view.js.min.js',
        )
        url_css = "{public_path}/{path}".format(
            public_path=public_path,
            path='some.fake.css',
        )
        url_js = "{public_path}/{path}".format(
            public_path=public_path,
            path='some.fake.js',
        )
        # Paths call get_resource_string that return a local_resource_url
        self.xblock.runtime.local_resource_url = MagicMock()
        self.xblock.runtime.local_resource_url.side_effect = [
            path_css,
            path_js
        ]
        test_result = self.xblock.build_fragment(
            fragment_js=fragment_js,
            html_source=html_source,
            paths_css=[path_css],
            paths_js=[path_js],
            urls_css=[url_css],
            urls_js=[url_js],
        )
        self.assertEqual(fragment_js, test_result.js_init_fn)
        self.assertEqual(html_source, test_result.content)
        self.assertEqual(4, len(test_result.resources))
        test_result_resource_data = []
        for resource in test_result.resources:
            test_result_resource_data.append(resource.data)
        self.assertIn(path_css, test_result_resource_data)
        self.assertIn(path_js, test_result_resource_data)
        self.assertIn(url_css, test_result_resource_data)
        self.assertIn(url_js, test_result_resource_data)

    def test_default_variables(self):
        """
        Checks instance variables are initialized correctly for default example
        """
        self.assertTrue(self.xblock.display_correctness)
        self.assertEquals('Adaptive Numeric Input', self.xblock.display_name)
        err_scores_list = []
        for index in range(0, 10):
            err_scores_list.append(
                {
                    'error_percent': str(index * 10),
                    'score': str(1.0 - (index / 10.0)),
                }
            )
        self.assertListEqual(err_scores_list, self.xblock.credit_list)
        self.assertEquals(
            'Answer is within %%ERROR_PERCENT%% percent.',
            self.xblock.feedback_default
        )
        self.assertListEqual([], self.xblock.hints)
        self.assertEquals(10, self.xblock.instructor_answer)
        self.assertEquals(0, self.xblock.max_attempts)
        print self.xblock.prompt
        prompt_str = '<h2>Default Example: Percent error feedback<h2>'\
            '<p><h3>This problem demonstrates how to provide specific '\
            'feedback based on the percent error away from the answer'\
            '<br><br>In this example the answer is 10.  Percent error '\
            ' ranges were added in settings Credit Dictionaries field '\
            'based on percent error away from 10.  Error dependent '\
            'feedback be displayed if the submitted answer falls '\
            'within one of the ranges.'
        self.assertEquals(prompt_str, self.xblock.prompt)
        self.assertEqual(
            'Your answers have been saved but not scoreed. '
            'Click "Submit" to score them.',
            self.xblock.saved_message
        )
        self.assertEqual(
            'Your submission has been received',
            self.xblock.submitted_message
        )
        self.assertEquals(10, self.xblock.weight)

    def test_generate_validation_message(self):
        # pylint: disable=invalid-name, protected-access
        """
        Checks classmethod _generate_validation_message
        """
        msg = u'some fake message'
        result = ValidationMessage(
            ValidationMessage.ERROR,
            _(msg)
        )
        test_result = AdaptiveNumericInput.generate_validation_message(msg)
        self.assertEquals(
            type(result),
            type(test_result),
        )
        self.assertEquals(
            result.text,
            test_result.text,
        )

    @ddt.data(
        # max_attempts, result
        (-1, ''),
        (0, ''),
        (1, 'You have used 1 of 1 submission'),
        (3, 'You have used 1 of 3 submissions'),
    )
    @ddt.unpack
    def test_get_attempts_message(self, max_attempts, result):
        """
        Test get_attempts_message based on max_attempts
        """
        self.xblock.max_attempts = max_attempts
        self.xblock.count_attempts = 1
        test_result = self.xblock.get_attempts_message()
        self.assertEquals(result, test_result)

    @ddt.data(
        # count_attempts, display_correctness, score, result
        (1, True, 0, 'incorrect'),
        (1, True, 1, 'correct'),
        (0, True, 1, 'unanswered'),
        (1, False, 1, 'unanswered'),
        (0, False, 1, 'unanswered'),
    )
    @ddt.unpack
    def test_get_css_indicator(
            self,
            count_attempts,
            display_correctness,
            score,
            result,
    ):
        """
        Test get_css_indicator based on display_correctness and count_attempts
        """
        self.xblock.count_attempts = count_attempts
        self.xblock.display_correctness = display_correctness
        self.xblock.score = score
        test_result = self.xblock.get_css_indicator()
        self.assertEquals(result, test_result)

    @ddt.data(
        # display_correctness, result
        (True, ''),
        (False, 'hidden'),
    )
    @ddt.unpack
    def test_get_css_indicator_hidden(
            self,
            display_correctness,
            result,
    ):
        """
        Test get_css_indicator_hidden based on display_correctness
        """
        self.xblock.display_correctness = display_correctness
        test_result = self.xblock.get_css_indicator_hidden()
        self.assertEquals(result, test_result)

    @ddt.data(
        # hints, result
        (['hint 1'], ''),
        (['hint 1', 'hint 2'], ''),
        ([], 'nodisplay'),
    )
    @ddt.unpack
    def test_get_css_hint_display(
            self,
            hints,
            result,
    ):
        """
        Test get_css_hint_button_display based on hints length
        """
        self.xblock.hints = hints
        test_result = self.xblock.get_css_hint_button_display()
        self.assertEquals(result, test_result)

    @ddt.data(
        # count_attempts, max_attempts, result
        (0, 0, ''),
        (1, 0, ''),
        (0, 1, ''),
        (1, 1, 'nodisplay'),
        (2, 1, 'nodisplay'),
    )
    @ddt.unpack
    def test_get_css_hide_submit(
            self,
            count_attempts,
            max_attempts,
            result,
    ):
        """
        Test get_css_hide_submit based count_attempts and max_attempts
        """
        self.xblock.count_attempts = count_attempts
        self.xblock.max_attempts = max_attempts
        test_result = self.xblock.get_css_hide_submit()
        self.assertEquals(result, test_result)

    def test_get_feedback_absolute(self):
        """
        Test get_feedback_message based on FEEDBACK_LIST for error_absolute
        """
        feedback = ' '.join(FEEDBACK_LIST)
        self.xblock.credit_dict = {
            'answer': 10.0,
            'error_absolute': 10.0,
            'feedback': feedback,
            'student_error': 1.0,
            'student_answer': '9',
        }
        result = ' '.join(
            [
                str(self.xblock.credit_dict['answer']),
                str(self.xblock.credit_dict['error_absolute']),
                '--',
                str(self.xblock.credit_dict['student_answer']),
                str(self.xblock.credit_dict['student_error']),
            ]
        )
        test_result = self.xblock.get_feedback_message()
        self.assertEquals(result, test_result)

    def test_get_feedback_default(self):
        """
        Test get_feedback_message based on FEEDBACK_LIST for default_feedback
        """
        result = 'Default Feedback'
        self.xblock.feedback_default = result
        self.xblock.credit_dict = {
            'answer': 10.0,
            'error_absolute': 10.0,
            'feedback': None,
            'student_error': 1.0,
            'student_answer': '9',
        }
        test_result = self.xblock.get_feedback_message()
        self.assertEquals(result, test_result)

    def test_get_feedback_none(self):
        """
        Test get_feedback_message based on FEEDBACK_LIST for none credit_dict
        """
        result = ''
        self.xblock.credit_dict = None
        test_result = self.xblock.get_feedback_message()
        self.assertEquals(result, test_result)

    def test_get_feedback_percent(self):
        """
        Test get_feedback_message based on FEEDBACK_LIST for error_percent
        """
        feedback = ' '.join(FEEDBACK_LIST)
        self.xblock.credit_dict = {
            'answer': 10.0,
            'error_percent': 10.0,
            'feedback': feedback,
            'student_error': 10.0,
            'student_answer': '9',
        }
        result = ' '.join(
            [
                str(self.xblock.credit_dict['answer']),
                '--',
                str(self.xblock.credit_dict['error_percent']),
                str(self.xblock.credit_dict['student_answer']),
                str(self.xblock.credit_dict['student_error']),
            ]
        )
        test_result = self.xblock.get_feedback_message()
        self.assertEquals(result, test_result)

    @ddt.data(
        # feedback_message, score, result
        (None, 0, ''),
        ('', 0, ''),
        (None, 1, ''),
        ('', 1, ''),
        ('some feedback message', 0, 'Incorrect:'),
        ('some feedback message', 0.1, 'Correct:'),
        ('some feedback message', 0.9, 'Correct:'),
        ('some feedback message', 1.0, 'Correct:'),
    )
    @ddt.unpack
    def test_get_feedback_message_label(
            self,
            feedback_message,
            score,
            result,
    ):
        """
        Test get_feedback_message_label based feedback_message and score
        """
        self.xblock.feedback_message = feedback_message
        self.xblock.score = score
        test_result = self.xblock.get_feedback_message_label()
        self.assertEquals(result, test_result)

    @ddt.data(
        # hints lists, hint_counter, result
        ([], 0, ''),
        ([], 3, ''),
        (['hint 1'], 0, 'Hint (1 of 1): hint 1'),
        (['hint 1'], 3, 'Hint (1 of 1): hint 1'),
        (['hint 1', 'hint 2', 'hint 3'], 0, 'Hint (1 of 3): hint 1'),
        (['hint 1', 'hint 2', 'hint 3'], 1, 'Hint (2 of 3): hint 2'),
        (['hint 1', 'hint 2', 'hint 3'], 2, 'Hint (3 of 3): hint 3'),
        (['hint 1', 'hint 2', 'hint 3'], 3, 'Hint (1 of 3): hint 1'),
    )
    @ddt.unpack
    def test_get_hint_message(self, hints, hint_counter, result):
        """
        Test get_hint_message returns message based on hints and hint_counter
        """
        self.xblock.hints = hints
        self.xblock.hint_counter = hint_counter
        test_result = self.xblock.get_hint_message()
        self.assertEquals(result, test_result)

    @ddt.data(
        # score, weight, result
        (0, 0, ''),
        (0.5, 0, ''),
        (0, 1, '(1 point possible)'),
        (0, 2, '(2 points possible)'),
        (0.5, 1, '(0.5/1 point)'),
        (1, 1, '(1/1 point)'),
        (1, 2, '(2/2 points)'),
    )
    @ddt.unpack
    def test_get_progress_message(self, score, weight, result):
        """
        Test get_progress_message returns message based on weight and score
        """
        self.xblock.score = score
        self.xblock.weight = weight
        test_result = self.xblock.get_progress_message()
        self.assertEquals(result, test_result)

    @ddt.data(
        # feedback_message, result
        ('', 'Your submission has been received'),
        ('some feedback message', ''),
    )
    @ddt.unpack
    def test_get_submitted_message(self, feedback_message, result):
        """
        Test get_submitted_message returns message based on feedback_message
        """
        self.xblock.feedback_message = feedback_message
        test_result = self.xblock.get_submitted_message()
        self.assertEquals(result, test_result)

    def test_get_resource_string(self):
        # pylint: disable=protected-access
        """
        Checks that get_resource_string returns the proper html
        """
        student_view_html = self.xblock.student_view().content
        test_result = AdaptiveNumericInput.get_resource_string('view.html')
        test_result = test_result.format(
            self=self,
            attempts_message=self.xblock.get_attempts_message(),
            display_name=self.xblock.display_name,
            feedback_label='',
            feedback_message='',
            hint_message='',
            hintdisplay_class=self.xblock.get_css_hint_button_display(),
            hide_submit_class=self.xblock.get_css_hide_submit(),
            indicator_class=self.xblock.get_css_indicator(),
            indicator_visibility_class=self.xblock.get_css_indicator_hidden(),
            progress_message=self.xblock.get_progress_message(),
            prompt=self.xblock.prompt,
            saved_message='',
            student_answer=self.xblock.student_answer,
            submitted_message='',
        )
        self.assertEquals(student_view_html, test_result)

    @ddt.data('view.js.min.js', 'view.less.min.css')
    def test_get_resource_url(self, path):
        """
        Checks that get_resource_url the correct url
        """
        public_path = '/resource/adaptivenumericinput/public'
        result = "{public_path}/{path}".format(
            public_path=public_path,
            path=path,
        )
        self.xblock.runtime.local_resource_url = MagicMock(
            return_value=result
        )
        test_result = self.xblock.get_resource_url(path)
        self.assertEquals(result, test_result)

    @ddt.data(
        # credit_dict, result
        (None, 0.0),
        ({'score': 0}, 0),
        ({'score': 0.5}, 0.5),
        ({'score': 0.666}, 0.6),
        ({'score': 1}, 1),
        ({'score': 2}, 0),
    )
    @ddt.unpack
    def test_set_score_publish(self, credit_dict, result):
        """
        Test set_score based on credit_dict score
        """
        self.xblock.credit_dict = credit_dict
        self.xblock.instructor_answer = 10
        self.xblock.set_score()
        self.xblock.runtime.publish.assert_called_with(
            self.xblock,
            'grade',
            {
                'value': result,
                'max_value': 1,
            },
        )

    @ddt.data(
        # credit_dict, result
        (None, 0.0),
        ({'score': -1}, 0),
        ({'score': 0}, 0),
        ({'score': 0.5}, 0.5),
        ({'score': 0.666}, 0.6),
        ({'score': 1}, 1),
        ({'score': 2}, 0),
    )
    @ddt.unpack
    def test_set_score_scores(self, credit_dict, result):
        """
        Test set_score based on credit_dict score
        """
        self.xblock.credit_dict = credit_dict
        self.xblock.set_score()
        self.assertEqual(self.xblock.score, result)

    def test_hint_response(self):
        """
        Test hint response json handler returns correct result
        """
        result = {
            'status': 'success',
            'hint_message': 'some hint message',
        }
        self.xblock.get_hint_message = MagicMock(
            return_value=result['hint_message']
        )
        data = json.dumps({})
        request = TestRequest()
        request.method = 'POST'
        request.body = data
        test_result_response = self.xblock.hint_reponse(request)
        # Added for test_result_response json_body
        # pylint: disable=no-member
        self.assertDictEqual(
            result,
            test_result_response.json_body,
        )

    @ddt.data(
        # count_attempts, max_attempts, student answer, result
        (0, 0, 'some student answer'),
        (1, 0, 'some student answer'),
        (0, 1, 'some student answer'),
        (1, 2, 'some student answer'),
        (1, 1, ''),
        (2, 1, ''),
    )
    @ddt.unpack
    def test_save_response(
            self,
            count_attempts,
            max_attempts,
            result_student_answer,
    ):
        """
        Test save response handler returns result based on max/count attempts
        """
        result = {
            'status': 'success',
            'hide_submit_class': 'some hide class',
            'progress_message': 'some progress message',
            'saved_message': 'some save message',
            'submitted_message': '',
        }
        self.xblock.count_attempts = count_attempts
        self.xblock.get_progress_message = MagicMock(
            return_value=result['progress_message'],
        )
        self.xblock.get_css_hide_submit = MagicMock(
            return_value=result['hide_submit_class'],
        )
        self.xblock.max_attempts = max_attempts
        self.xblock.saved_message = result['saved_message']
        data = json.dumps({'student_answer': 'some student answer'})
        request = TestRequest()
        request.method = 'POST'
        request.body = data
        test_result_response = self.xblock.save_response(request)
        self.assertEquals(result_student_answer, self.xblock.student_answer)
        # Added for test_result_response json_body
        # pylint: disable=no-member
        self.assertDictEqual(
            result,
            test_result_response.json_body,
        )

    def test_student_view(self):
        # pylint: disable=protected-access
        """
        Checks the student view for student specific instance variables.
        """
        student_view = self.xblock.student_view()
        student_view_html = student_view.content
        self.assertIn(self.xblock.get_attempts_message(), student_view_html)
        self.assertIn(self.xblock.display_name, student_view_html)
        self.assertIn(
            self.xblock.get_css_hint_button_display(),
            student_view_html
        )
        self.assertIn(self.xblock.get_css_hide_submit(), student_view_html)
        self.assertIn(self.xblock.get_css_indicator(), student_view_html)
        self.assertIn(
            self.xblock.get_css_indicator_hidden(),
            student_view_html
        )
        self.assertIn(self.xblock.get_progress_message(), student_view_html)
        self.assertIn(self.xblock.prompt, student_view_html)
        self.assertIn(self.xblock.student_answer, student_view_html)

    def test_submit_non_numeric(self):
        """
        Test submit handler returns bad result for non numeric submission
        """
        result = {'status': 'success'}
        data = json.dumps({'student_answer': 'ABC'})
        request = TestRequest()
        request.method = 'POST'
        request.body = data
        test_result_response = self.xblock.submit(request)
        # Added for test_result_response json_body
        # pylint: disable=no-member
        self.assertDictEqual(
            result,
            test_result_response.json_body,
        )

    @ddt.data(
        # count_attempts, max_attempts, feedback_message
        (0, 0, u'Answer is within -- percent.'),
        (1, 0, u'Answer is within -- percent.'),
        (0, 1, u'Answer is within -- percent.'),
        (1, 2, u'Answer is within -- percent.'),
        (1, 1, u''),
        (2, 1, u''),
    )
    @ddt.unpack
    def test_submit(
            self,
            count_attempts,
            max_attempts,
            feedback_message,
    ):
        """
        Test submit response handler returns result based on max/count attempts
        """
        self.xblock.count_attempts = count_attempts
        self.xblock.max_attempts = max_attempts
        result = {
            u'status': u'success',
            u'attempts_message': u'some attempts message',
            u'feedback_label': u'some feedback label',
            u'feedback_message': feedback_message,
            u'indicator_class': u'some css indicator class',
            u'indicator_visibility_class': u'some css indicator hidden',
            u'hide_submit_class': u'some css hide submit',
            u'progress_message': u'some progress message',
            u'saved_message': u'',
            u'submitted_message': u'some submitted message',
        }
        self.xblock.get_best_match_credit_dict = MagicMock(
            return_value={'score': 1},
        )
        self.xblock.get_attempts_message = MagicMock(
            return_value=result['attempts_message'],
        )
        self.xblock.get_feedback_message_label = MagicMock(
            return_value=result['feedback_label'],
        )
        self.xblock.get_css_indicator = MagicMock(
            return_value=result['indicator_class'],
        )
        self.xblock.get_css_indicator_hidden = MagicMock(
            return_value=result['indicator_visibility_class'],
        )
        self.xblock.get_css_hide_submit = MagicMock(
            return_value=result['hide_submit_class'],
        )
        self.xblock.get_progress_message = MagicMock(
            return_value=result['progress_message'],
        )
        self.xblock.get_submitted_message = MagicMock(
            return_value=result['submitted_message'],
        )
        data = json.dumps({'student_answer': 1234})
        request = TestRequest()
        request.method = 'POST'
        request.body = data
        test_result_response = self.xblock.submit(request)
        # Added for test_result_response json_body
        # pylint: disable=no-member
        self.assertDictEqual(
            result,
            test_result_response.json_body,
        )

    @ddt.file_data('./test_data/validate_field_data.json')
    def test_validate_field_data(self, **test_dict):
        """
        Checks classmethod validate_field_data
        tests the instuctor values set in edit
        """
        test_data = TestData()
        test_data.weight = test_dict['weight']
        test_data.max_attempts = test_dict['max_attempts']
        validation = set()
        self.xblock.validate_field_data(validation, test_data)
        validation_list = list(validation)
        # Only one validation error should be in set
        self.assertEquals(1, len(validation_list))
        self.assertEquals(
            test_dict['result'],
            validation_list[0].text,
        )

    # Credit Dict
    def test_copy_credit_no_answer(self):
        """
        Test copy_credit_dict returns answer with no answer given
        """
        self.xblock.instructor_answer = 10
        credit_dict = {}
        test_result = self.xblock.copy_credit_dict(credit_dict)
        self.assertIsNotNone(test_result.get('answer'))
        self.assertEqual(self.xblock.instructor_answer, test_result['answer'])

    @ddt.data(
        # instructor_answer, answer, answer_result
        (5, None, 5),
        (5, 'asdf', 5),
        (5, 8, 8),
    )
    @ddt.unpack
    def test_copy_credit_answer(
            self,
            instructor_answer,
            answer,
            answer_result,
    ):
        """
        Test copy_credit_dict returns proper answer
        """
        self.xblock.instructor_answer = instructor_answer
        credit_dict = {'answer': answer}
        test_result = self.xblock.copy_credit_dict(credit_dict)
        self.assertIsNotNone(test_result.get('answer'))
        self.assertEqual(answer_result, test_result['answer'])

    def test_copy_credit_no_err_percent(self):
        """
        Test copy_credit_dict returns error_percent with no error_percent given
        """
        credit_dict = {}
        test_result = self.xblock.copy_credit_dict(credit_dict)
        self.assertIsNotNone(test_result.get('error_percent'))
        self.assertEqual(0, test_result['error_percent'])

    @ddt.data(
        # error_percent, error_percent_result,
        (10, 10),
        (None, 0),
    )
    @ddt.unpack
    def test_copy_credit_err_percent(
            self,
            error_percent,
            error_percent_result,
    ):
        """
        Test copy_credit_dict returns proper error_percent
        """
        credit_dict = {
            'error_percent': error_percent,
        }
        test_result = self.xblock.copy_credit_dict(credit_dict)
        self.assertIsNotNone(test_result.get('error_percent'))
        self.assertEqual(error_percent_result, test_result['error_percent'])

    @ddt.data(
        # error_absolute, error_absolute_result, error_percent_result
        (10, 10, None),
        (None, None, 0),
    )
    @ddt.unpack
    def test_copy_credit_err_absolute(
            self,
            error_absolute,
            error_absolute_result,
            error_percent_result,
    ):
        """
        Test copy_credit_dict returns proper error_absolute
        """
        credit_dict = {
            'error_absolute': error_absolute,
        }
        test_result = self.xblock.copy_credit_dict(credit_dict)
        if error_absolute:
            self.assertIsNotNone(test_result.get('error_absolute'))
        else:
            self.assertIsNotNone(test_result.get('error_percent'))
        self.assertEqual(error_percent_result, test_result['error_percent'])
        self.assertEqual(error_absolute_result, test_result['error_absolute'])

    def test_copy_credit_no_score(self):
        """
        Test copy_credit_dict returns score with no score given
        """
        credit_dict = {}
        test_result = self.xblock.copy_credit_dict(credit_dict)
        self.assertIsNotNone(test_result.get('score'))
        self.assertEqual(1.0, test_result['score'])

    @ddt.data(
        (0, 0),
        (1, 1),
        (0.5, 0.5),
        (None, 0),
        (2, 1),
        (-1, 0),
    )
    @ddt.unpack
    def test_copy_credit_score(self, score, score_result):
        """
        Test copy_credit_dict returns proper score
        """
        credit_dict = {
            'score': score,
        }
        test_result = self.xblock.copy_credit_dict(credit_dict)
        self.assertIsNotNone(test_result.get('score'))
        self.assertEqual(score_result, test_result['score'])

    def test_copy_credit_keys(self):
        """
        Test copy_credit_dict returns needed keys
        """
        keys = [
            'answer',
            'credit_score',
            'error_absolute',
            'error_percent',
            'feedback',
            'score',
            'student_answer',
            'student_error',
        ]
        test_result = self.xblock.copy_credit_dict({})
        self.assertSetEqual(set(keys), set(test_result.keys()))

    def test_get_best_credit_empty(self):
        """
        Test get_best_match_credit_dict returns none for empty high_score_list
        """
        self.xblock.get_credit_dicts_score_list = MagicMock(
            return_value=[],
        )
        test_result = self.xblock.get_best_match_credit_dict()
        self.assertFalse(test_result)

    @ddt.data(
        [],
        [{'error_absolute': 10.0, 'error_percent': 1.0}],
        [{'score': 0.5, 'error_absolute': 10.0, 'error_percent': 1.0}],
        [
            {'score': 0.5, 'error_absolute': 10.0, 'error_percent': 1.0},
            {'score': 0.5, 'error_absolute': 20.0, 'error_percent': 2.0},
        ],
    )
    def test_get_best_credit_answer(self, score_list):
        """
        Test get_best_match_credit_dict returns score of 1.0 for answer match
        """
        self.xblock.instructor_answer = 10.0
        self.xblock.student_answer_float = 10.0
        self.xblock.get_credit_dicts_score_list = MagicMock(
            return_value=score_list,
        )
        test_result = self.xblock.get_best_match_credit_dict()
        self.assertTrue(test_result.get('score'))
        self.assertEqual(test_result['score'], 1.0)

    @ddt.data(
        (
            [(10.0, 1.0, 1.0)],
            {
                'error_percent': 10.0,
                'error_absolute': 1.0,
                'score': 1.0,
            },
        ),
        (
            [
                (11.0, 1.0, 0.5),
                (12.0, 1.0, 0.5),
                (13.0, 1.0, 0.5),
            ],
            {
                'error_percent': 11.0,
                'error_absolute': 1.0,
                'score': 0.5,
            },
        ),
        (
            [
                (11.0, 3.0, 0.7),
                (12.0, 2.0, 0.7),
                (13.0, 1.0, 0.7),
            ],
            {
                'error_percent': 11.0,
                'error_absolute': 3.0,
                'score': 0.7,
            },
        ),
        (
            [
                (12.0, 5.0, 0.6),
                (12.0, 4.0, 0.6),
                (12.0, 3.0, 0.6),
            ],
            {
                'error_percent': 12.0,
                'error_absolute': 3.0,
                'score': 0.6,
            },
        ),
    )
    @ddt.unpack
    def test_get_best_credit(self, score_args_list, result_dict):
        """
        Test get_best_match_credit_dict returns best dict in list
        """
        def get_score_dict(*args):
            """
            Helper function to build mock dict list
            """
            score_dict = {
                'error_percent': args[0],
                'error_absolute': args[1],
                'score':  args[2],
            }
            return score_dict
        score_dict_list = []
        for score_args in score_args_list:
            score_dict_list.append(get_score_dict(*score_args))
        self.xblock.get_credit_dicts_score_list = MagicMock(
            return_value=score_dict_list,
        )
        self.xblock.student_answer_float = 9.0
        self.xblock.instructor_answer = 10.0
        test_result = self.xblock.get_best_match_credit_dict()
        self.assertDictEqual(result_dict, test_result)

    @ddt.data(
        # the_answer, err%, err abs, score, score result, err result(%,abs)
        (None, None, None, None, None, None),
        (10.0, None, None, None, None, None),
        (10.0, 10.0, None, None, None, 10.0),
        (10.0, None, 1.0, None, None, 1.0),
        (10.0, 10.0, None, 1.0, 1.0, 10.0),
        (10.0, None, 1.0, 1.0, 1.0, 1.0),
        (10.0, 10.0, 2.0, 1.0, 1.0, 10.0),
        (10.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        (10.0, 10.0, 1.0, 1.0, 1.0, 10.0),
    )
    @ddt.unpack
    def test_get_credit_score_error(
            self,
            the_answer,
            error_percent,
            error_absolute,
            score,
            credit_score_result,
            student_error_result,
    ):
        # pylint: disable-msg=too-many-arguments
        """
        Test get_credit_dict_score_and_error returns proper tuple
        """
        self.xblock.student_answer_float = 9.0
        (credit_score,
         student_error) = self.xblock.get_credit_dict_score_and_error(
             the_answer,
             error_percent,
             error_absolute,
             score,
         )
        self.assertEqual(credit_score, credit_score_result)
        self.assertEqual(student_error, student_error_result)

    @ddt.data(
        # student_error artificially used for sorting to aid in testing
        ([(None, None, )], []),
        ([(0.4, 1.0, )], [{'credit_score': 0.4, 'student_error': 1.0}]),
        (
            [
                (0.75, 1.0),
                (1.0, 2.0),
                (0.5, 3.0),
            ],
            [{'credit_score': 1.0, 'student_error': 2.0}],
        ),
        (
            [
                (0.8, 1.0),
                (0.8, 2.0),
                (0.5, 3.0),
                (0.7, 4.0),
                (0.8, 5.0),
            ],
            [
                {'credit_score': 0.8, 'student_error': 1.0},
                {'credit_score': 0.8, 'student_error': 2.0},
                {'credit_score': 0.8, 'student_error': 5.0},
            ],
        ),
    )
    @ddt.unpack
    def test_get_credit_score_list(self, score_error_tuples, result_list):
        """
        Test get_credit_dicts_score_list returns best credit dicts
        """
        def mock_copy_credit_dict(*args):
            """
            Helper to mock credit dicts
            """
            # pylint: disable=unused-argument
            return {
                'answer': 99,
                'error_percent': 99,
                'error_absolute': 99,
                'score': 99,
            }

        # Values in list are mocked, this is only needed to iterate
        self.xblock.credit_list = score_error_tuples
        self.xblock.copy_credit_dict = MagicMock(
            side_effect=mock_copy_credit_dict,
        )
        self.xblock.get_credit_dict_score_and_error = MagicMock(
            side_effect=score_error_tuples,
        )
        result_score_error_list = self.xblock.get_credit_dicts_score_list()
        self.assertEqual(len(result_list), len(result_score_error_list))
        # Remove unused keys to help test the lists
        for credit_dict in result_score_error_list:
            del credit_dict['answer']
            del credit_dict['error_percent']
            del credit_dict['error_absolute']
            del credit_dict['score']
        result_score_error_list.sort(key=lambda x: x['student_error'])
        self.assertListEqual(result_list, result_score_error_list)

    def test_workbench_scenarios(self):
        """
        Checks workbench scenarios for a default scenario
        """
        result_title = 'Adaptive Numeric Input XBlock'
        basic_scenario = "<adaptivenumericinput />"
        test_result = self.xblock.workbench_scenarios()
        self.assertEquals(result_title, test_result[0][0])
        self.assertIn(basic_scenario, test_result[0][1])
