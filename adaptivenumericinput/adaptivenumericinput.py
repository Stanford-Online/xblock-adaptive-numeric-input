"""
    An XBlock where instructors can provide adaptive feedback for numeric
    reponse problems.  Error ranges can be setup around right or wrong answer
    in Settings.  Each range can have targeted, dynamic feedback and an
    associated score.
"""
import os
import pkg_resources

from math import floor

from django.utils.translation import ungettext

from xblock.core import XBlock
from xblock.fields import Scope
from xblock.fields import Boolean, Dict, Float, Integer, List, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage

from xblockutils.studio_editable import StudioEditableXBlockMixin

from .utils import _


# List of available %%-encoded keywords that instructors can use in feedback
# They will be replaced with numeric values or '--' if they do not exist
FEEDBACK_LIST = [
    '%%ANSWER%%',
    '%%ERROR_ABSOLUTE%%',
    '%%ERROR_PERCENT%%',
    '%%STUDENT_ANSWER%%',
    '%%STUDENT_ERROR%%',
]


def _get_float(value):
    try:
        return float(value)
    except ValueError:
        return None
    except TypeError:
        return None


def _answer_error(answer, actual_answer):
    # Returns percent and absolute error of 'answer' from 'actual_answer'
    # If 'actual_answer' is zero then percent_error will be None
    # since it cannot be determined for that case.
    percent_error = None
    absolute_error = abs(answer - actual_answer)
    if actual_answer:
        percent_error = 100 * (absolute_error / actual_answer)
    return percent_error, absolute_error


def _read_scenario_files():
    # Loads preset scenario files and returns them as a quote enclosed string
    # Files are ordered based on complexity
    dir_path = os.path.dirname(os.path.realpath(__file__))
    scenario_files = [
        'absoltue_error.html',
        'default_common_mistake.html',
        'default_multi_full_credit.html',
        'range_blocking.html',
        'variables_example.html',
        'bakers_dozen.html',
        'temp_conversion.html',
    ]
    scenarios = '<adaptivenumericinput/>'
    for scenario_file in scenario_files:
        scenario = open(dir_path + '/scenarios/' + scenario_file, 'r')
        scenarios += scenario.read()
    scenarios_string = '''
        <sequence_demo>{scenarios}</sequence_demo>
        '''.format(
            scenarios=scenarios,
        )
    return scenarios_string


class AdaptiveNumericInputXBlock(StudioEditableXBlockMixin, XBlock):
    #  pylint: disable=too-many-ancestors, too-many-instance-attributes
    """
    This xblock provides a way for instrutors to give targeted feedback
    to students on numeric reponse problems.
    """
    display_correctness = Boolean(
        display_name=_('Display Correctness?'),
        help=_(
            'This is a flag that indicates if the correctness '
            'UI should be displayed after a student submits '
            'their response'
        ),
        default=True,
        scope=Scope.settings,
    )
    display_name = String(
        display_name=_('Display Name'),
        help=_(
            'This is the title for this question type'
        ),
        default=_('Adaptive Numeric Input'),
        scope=Scope.settings,
    )
    credit_list = List(
        default=[
            {'error_percent': '0', 'score': '1.0'},
            {'error_percent': '10', 'score': '0.9'},
            {'error_percent': '20', 'score': '0.8'},
            {'error_percent': '30', 'score': '0.7'},
            {'error_percent': '40', 'score': '0.6'},
            {'error_percent': '50', 'score': '0.5'},
            {'error_percent': '60', 'score': '0.4'},
            {'error_percent': '70', 'score': '0.3'},
            {'error_percent': '80', 'score': '0.2'},
            {'error_percent': '90', 'score': '0.1'},
        ],
        display_name=_('Credit Dictionaries'),
        help=_(
            'This is a list of credit object '
            'with properties that allow the instructor to '
            'specify an error_percent, score, feedback based on a provided '
            'answer'
        ),
        scope=Scope.settings,
    )
    feedback_default = String(
        feedback_default=_('Default Feedback'),
        help=_(
            'This is the default feedback used for credit dictionaries '
            'if feedback is left out.'
        ),
        default='Answer is within %%ERROR_PERCENT%% percent.',
        scope=Scope.settings,
    )
    hints = List(
        display_name=_('Hint Phrases'),
        help=_(
            'This is a list of hints to display to the user.  '
            'Example list: [ "Consider this...", "Consider that..."]'
        ),
        default=[],
        scope=Scope.settings,
    )
    instructor_answer = Float(
        display_name=_('Answer to problem'),
        help=_(
            'This is the default numeric answer to the problem.'
        ),
        default=10,
        scope=Scope.settings,
    )
    max_attempts = Integer(
        display_name=_('Maximum Number of Attempts'),
        help=_(
            'This is the maximum number of times a '
            'student is allowed to attempt the problem'
        ),
        default=0,
        values={'min': 1},
        scope=Scope.settings,
    )
    prompt = String(
        default=_(
            '<h2>Default Example: Percent error feedback<h2>'
            '<p><h3>This problem demonstrates how to provide specific '
            'feedback based on the percent error away from the answer'
            '<br><br>In this example the answer is 10.  Percent error '
            ' ranges were added in settings Credit Dictionaries field '
            'based on percent error away from 10.  Error dependent '
            'feedback be displayed if the submitted answer falls '
            'within one of the ranges.'
        ),
        display_name=_('Prompt'),
        help=_(
            'This is the prompt students will see when '
            'asked to enter their response'
        ),
        multiline_editor=True,
        scope=Scope.settings,
    )
    saved_message = String(
        display_name=_('Save Received Message'),
        help=_(
            'This is the message students will see upon '
            'submitting a draft response'
        ),
        default=_(
            'Your answers have been saved but not scoreed. '
            'Click "Submit" to score them.'
        ),
        scope=Scope.settings,
    )
    submitted_message = String(
        display_name=_('Submission Received Message'),
        help=_(
            'This is the message students will see upon '
            'submitting their response'
        ),
        default=_('Your submission has been received'),
        scope=Scope.settings,
    )
    weight = Integer(
        display_name=_('Weight'),
        help=_(
            'This assigns an integer value representing '
            'the weight of this problem'
        ),
        default=10,
        values={'min': 1},
        scope=Scope.settings,
    )

    count_attempts = Integer(
        default=0,
        scope=Scope.user_state,
    )
    credit_dict = Dict(
        default={},
        scope=Scope.user_state,
    )
    feedback_message = String(
        default='',
        scope=Scope.user_state,
    )
    hint_counter = Integer(
        default=0,
        scope=Scope.user_state,
    )
    score = Float(
        default=0.0,
        scope=Scope.user_state,
    )
    student_answer = String(
        default='',
        scope=Scope.user_state,
    )

    editable_fields = (
        'display_name',
        'prompt',
        'max_attempts',
        'instructor_answer',
        'weight',
        'feedback_default',
        'credit_list',
        'hints',
        'display_correctness',
        'submitted_message',
        'saved_message',
    )

    def build_fragment(
            self,
            html_source=None,
            paths_css=[],
            paths_js=[],
            urls_css=[],
            urls_js=[],
            fragment_js=None,
    ):
        #  pylint: disable=dangerous-default-value, too-many-arguments
        """
        Assemble the HTML, JS, and CSS for an XBlock fragment
        """
        fragment = Fragment(html_source)
        for url in urls_css:
            fragment.add_css_url(url)
        for path in paths_css:
            url = self.get_resource_url(path)
            fragment.add_css_url(url)
        for url in urls_js:
            fragment.add_javascript_url(url)
        for path in paths_js:
            url = self.get_resource_url(path)
            fragment.add_javascript_url(url)
        if fragment_js:
            fragment.initialize_js(fragment_js)
        return fragment

    @classmethod
    def generate_validation_message(cls, msg):
        """
        Helper method to generate a ValidationMessage from
        the supplied string
        """
        result = ValidationMessage(
            ValidationMessage.ERROR,
            _(unicode(msg))
        )
        return result

    def get_attempts_message(self):
        """
        Returns the text with feedback to the user about the number of attempts
        they have used if applicable
        """
        result = ''
        if self.max_attempts > 0:
            result = ungettext(
                'You have used {count_attempts} of {max_attempts} submission',
                'You have used {count_attempts} of {max_attempts} submissions',
                self.max_attempts,
            ).format(
                count_attempts=self.count_attempts,
                max_attempts=self.max_attempts,
            )
        return result

    def get_css_indicator(self):
        """
        Returns the class of the correctness indicator element
        If instructor did not turn off display correctness
        """
        result = 'unanswered'
        if self.display_correctness and self.count_attempts > 0:
            if self.score == 0:
                result = 'incorrect'
            else:
                result = 'correct'
        return result

    def get_css_indicator_visibility(self):
        """
        Returns the visibility class for the correctness indicator html element
        """
        if self.display_correctness:
            result = ''
        else:
            result = 'hidden'
        return result

    def get_css_hint_button_display(self):
        """
        Returns the css class to show the hint button
        If the instructor did not add hints in settings
        then the hint button will not display
        This is only called in student_view when
        xblock loads or is refreshed
        """
        result = 'nodisplay'
        if len(self.hints) > 0:
            result = ''
        return result

    def get_css_hide_submit(self):
        """
        Returns the css class for the submit and save buttons
        """
        result = ''
        if self.max_attempts > 0 and self.count_attempts >= self.max_attempts:
            result = 'nodisplay'
        return result

    def get_feedback_message(self):
        """
        Builds feedback_message from a credit_dict
        Replaces all %%-encoded words using FEEDBACK_LIST
        Iterates through all keywords that may be substituted and replaces
        them with the string formated field attributes in self.
        Return the modified feedback text
        """
        feedback_message = ''
        if self.credit_dict:
            feedback_message = self.feedback_default
            if self.credit_dict.get('feedback') is not None:
                feedback_message = self.credit_dict['feedback']
        if feedback_message:
            for key in FEEDBACK_LIST:
                credit_key = str(key.lower()[2:-2])
                value = self.credit_dict.get(credit_key)
                if value is None:
                    value = '--'
                feedback_message = feedback_message.replace(
                    key,
                    str(value)
                )
        return feedback_message

    def get_feedback_message_label(self):
        """
        Returns the feedback label depending self.score
        If self.feedback_message is not set then should return emtpy
        """
        feedback_label = ''
        if self.feedback_message:
            feedback_label = 'Correct:'
            if self.score == 0:
                feedback_label = 'Incorrect:'
        return feedback_label

    def get_hint_message(self):
        """
        Returns a hint message to display in the user
        if the instructor set them in settings
        """
        result = ''
        hints_total = len(self.hints)
        if hints_total > 0:
            hint_mod = self.hint_counter % hints_total
            result = _(
                "Hint ({hint_number} of {hints_total}): "
                "{hint}",
            ).format(
                hint_number=hint_mod + 1,
                hints_total=hints_total,
                hint=self.hints[hint_mod],
            )
            self.hint_counter += 1
        return result

    def get_progress_message(self):
        """
        Returns a statement of progress for the XBlock, which depends
        on the user's current score
        No weight means no progress, blank messages are not displayed
        via css
        """
        if self.weight == 0:
            result = ''
        elif self.score == 0:
            result = "({})".format(
                ungettext(
                    "{weight} point possible",
                    "{weight} points possible",
                    self.weight,
                ).format(
                    weight=self.weight,
                )
            )
        else:
            scaled_score = self.score * self.weight
            score_string = '{0:g}'.format(scaled_score)
            result = "({})".format(
                ungettext(
                    "{score_string}/{weight} point",
                    "{score_string}/{weight} points",
                    self.weight,
                ).format(
                    score_string=score_string,
                    weight=self.weight,
                )
            )
        return result

    def get_submitted_message(self):
        """
        Returns the text for self.submitted_message
        if instructor did not clear that field in settings.
        Will return empty(and not display) if feedback was
        found for the answer.
        """
        result = self.submitted_message
        if self.feedback_message:
            result = ''
        return result

    @classmethod
    def get_resource_string(cls, path):
        """
        Retrieve string contents for the file path
        """
        path = os.path.join('public', path)
        resource_string = pkg_resources.resource_string(__name__, path)
        return resource_string.decode('utf8')

    def get_resource_url(self, path):
        """
        Retrieve a public URL for the file path
        """
        path = os.path.join('public', path)
        resource_url = self.runtime.local_resource_url(self, path)
        return resource_url

    def set_credit_dict(self):
        self.credit_dict = None
        # Build a list of scored credit_dicts
        score_list = []
        high_score = 0
        for credit_dict in self.credit_list:
            # self.credit_list items cannot be modifed
            # so the return credit_dicts are not original.
            # Modifed credit_dicts are used to create adaptive feedback
            # and set the score
            tmp_credit = self.set_credit_dict_score(credit_dict)
            if tmp_credit.get('credit_score') == high_score:
                score_list.append(tmp_credit)
            elif tmp_credit.get('credit_score') > high_score:
                score_list = [tmp_credit]
                high_score = tmp_credit['credit_score']
        # Find best credit_dict
        if score_list:
            score_list.sort(key=lambda x: x['error_absolute'])
            score_list.sort(key=lambda x: x['error_percent'])
            # Check for exact answer and force full credit
            if self.student_answer_float == self.instructor_answer:
                score_list[0]['score'] = 1.0
            self.credit_dict = score_list[0]
        # No credit dicts found but exact answer
        elif self.student_answer_float == self.instructor_answer:
            # Minimum credit dict for scoring
            self.credit_dict = {'score': 1.0}

    def set_credit_dict_score(self, credit_dict):
        # Credit Answer, default to instructor_answer
        credit_answer = _get_float(
            credit_dict.get('answer', self.instructor_answer)
        )
        # Score, default to 0 and in range [0, 1]
        score = _get_float(credit_dict.get('score', 0.0))
        score = max(min(1.0, score), 0.0)
        tmp_credit = {
            'answer': credit_answer,
            # 'credit_score' is the evaluated score
            'credit_score': None,
            'error_percent': _get_float(credit_dict.get('error_percent')),
            'error_absolute': _get_float(credit_dict.get('error_absolute')),
            'feedback': credit_dict.get('feedback'),
            # 'score' is the instructor defined score
            'score':  score,
            'student_answer': self.student_answer,
            'student_error': None,
        }
        # Find error, percent has precedence over absolute
        percent_error, absolute_error = _answer_error(
            self.student_answer_float,
            tmp_credit['answer'],
        )
        credit_percent_error = tmp_credit.get('error_percent')
        credit_absolute_error = tmp_credit.get('error_absolute')
        if (credit_percent_error is None and
                credit_absolute_error is None):
            credit_percent_error = 0
        if (credit_percent_error is not None and
                percent_error is not None and
                round(credit_percent_error, 6) >= round(percent_error, 6)):
            tmp_credit['credit_score'] = score
            tmp_credit['student_error'] = percent_error
        if credit_absolute_error is not None and absolute_error is not None:
            if round(credit_absolute_error, 6) >= round(absolute_error, 6):
                tmp_credit['credit_score'] = score
                tmp_credit['student_error'] = absolute_error
        return tmp_credit

    def set_score(self):
        """
        Determines score and publishes the user's score for the XBlock
        based on their answer.
        Also sets the feedback text if found in credit dictionary.
        """
        score = 0.0
        if self.credit_dict and self.credit_dict.get('score') is not None:
            final_score = self.credit_dict.get('score')
            if 0 <= final_score and 1 >= final_score:
                score = floor(10 * final_score) / 10
        self.score = score
        self.runtime.publish(
            self,
            'grade',
            {
                'value': self.score,
                'max_value': 1,
            }
        )

    @XBlock.json_handler
    def hint_reponse(self, data, suffix=''):
        # pylint: disable=unused-argument
        """
        Processes the user's hint request
        Does not impact any other UI elements
        """
        result = {
            'status': 'success',
            'hint_message': self.get_hint_message(),
        }
        return result

    @XBlock.json_handler
    def save_response(self, data, suffix=''):
        # pylint: disable=unused-argument
        """
        Processes the user's save
        """
        if self.max_attempts == 0 or self.count_attempts < self.max_attempts:
            self.student_answer = data['student_answer']
        result = {
            'status': 'success',
            'progress_message': self.get_progress_message(),
            'submitted_message': '',
            'hide_submit_class': self._get_hide_submit_class(),
            'saved_message': self.saved_message,
        }
        return result

    def student_view(self, context=None):
        # pylint: disable=unused-argument
        """
        The primary view of the AdaptiveNumericInputXBlock,
        shown to students when viewing courses.
        """
        view_html = AdaptiveNumericInputXBlock.get_resource_string('view.html')
        view_html = view_html.format(
            self=self,
            # Message/Labels
            attempts_message=self.get_attempts_message(),
            display_name=self.display_name,
            feedback_label='',
            feedback_message='',
            hint_message='',
            hintdisplay_class=self.get_css_hint_button_display(),
            hide_submit_class=self.get_css_hide_submit(),
            indicator_class=self.get_css_indicator(),
            indicator_visibility_class=self.get_css_indicator_visibility(),
            progress_message=self.get_progress_message(),
            prompt=self.prompt,
            saved_message='',
            student_answer=self.student_answer,
            submitted_message='',
        )
        fragment = self.build_fragment(
            html_source=view_html,
            paths_css=[
                'view.less.min.css',
            ],
            paths_js=[
                'view.js.min.js',
            ],
            fragment_js='AdaptiveNumericInputView',
        )
        return fragment

    # Handlers to perform actions
    @XBlock.json_handler
    def submit(self, data, suffix=''):
        # pylint: disable=unused-argument
        """
        Processes the user's submission
        If submitted student_answer is not numeric
        then function returns as if no submission occured.
        Non numeric submissions are consider malicious.
        Blank submissions are self evident user errors.
        """
        # Return immediatly without negative impact
        # for non numeric student_answer
        # Allowing for answers equal to zero
        self.student_answer = data['student_answer']
        self.student_answer_float = _get_float(self.student_answer)
        if self.student_answer_float is None:
            return {'status': 'success'}
        # If max was not set or max already reached then do not count score
        if self.max_attempts == 0 or self.count_attempts < self.max_attempts:
            self.count_attempts += 1
            # self.credit_dict, if found is used for the feedback message
            # and to set score.
            self.set_credit_dict()
            self.feedback_message = self.get_feedback_message()
            self.set_score()
        result = {
            'status': 'success',
            # Used attempts 'out of' message in settings
            # 'self.max_attempts' > 0
            'attempts_message': self.get_attempts_message(),
            # Feedback label, empty if 'self.feedback_message' is empty
            'feedback_label': self.get_feedback_message_label(),
            # Feedback message found in credit lists while computing score
            'feedback_message': self.feedback_message,
            # CSS Class to indicate correctness UI
            'indicator_class': self.get_css_indicator(),
            # CSS Class to indicate if correctness UI is shown in settings
            # 'self.display_correctness'
            'indicator_visibility_class':
                self.get_css_indicator_visibility(),
            # CSS Class to hide submit UI because max attempts reached
            'hide_submit_class': self.get_css_hide_submit(),
            # Score 'out of' message in settings, 'self.weight' > 0
            'progress_message': self.get_progress_message(),
            # Instructor set message to indicated answer saved
            'saved_message': '',
            #  Submission received message in settings 'self.submitted_message'
            # Returns blank if answer feedback was found in compute score
            'submitted_message': self.get_submitted_message(),
        }
        return result

    def validate_field_data(self, validation, data):
        """
        Validates settings entered by the instructor.
        """
        # TODO: Check which need validation.
        # 'display_name',
        # 'prompt',
        # 'weight',
        # 'max_attempts',
        # 'display_correctness',
        # 'credit_list',
        # 'hints',
        # 'submitted_message',
        if data.weight < 0:
            msg = AdaptiveNumericInputXBlock.generate_validation_message(
                'Weight Attempts cannot be negative'
            )
            validation.add(msg)
        if data.max_attempts < 0:
            msg = AdaptiveNumericInputXBlock.generate_validation_message(
                'Maximum Attempts cannot be negative'
            )
            validation.add(msg)
        if not data.submitted_message:
            msg = AdaptiveNumericInputXBlock.generate_validation_message(
                'Submission Received Message cannot be blank'
            )
            validation.add(msg)

    # Scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        scenarios = _read_scenario_files()
        scenarios_block = [
            (
                'Adaptive Numeric Input XBlock',
                scenarios
            ),
            ("Multiple AdaptiveNumericInputXBlock",
             """<vertical_demo>
                <adaptivenumericinput/>
                <adaptivenumericinput/>
                <adaptivenumericinput/>
                </vertical_demo>
             """),
        ]
        return scenarios_block
