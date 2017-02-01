function AdaptiveNumericInputView(runtime, element) {
    'use strict';
    
    var $ = window.jQuery;
    var $element = $(element);
    
    var buttonHint = $element.find('.hint');
    var buttonSave = $element.find('.save');
    var buttonSubmit = $element.find('.check.Submit');
    
    var attemptsMessage = $element.find('.action .attempts-message');
    var progressMessage = $element.find('.progress-message');
    var submissionReceivedMessage = $element.find('.submission-received');
    var savedMessage = $element.find('.saved-message');

    var feedback = $element.find('.feedback');
    var feedbackLabel = $element.find('.feedback-label');
    var feedbackText = $element.find('.feedback-text');
    var hintText = $element.find('.hint-text');
  
    var studentAnswer = $element.find('.student_answer');
    var capaInputType = $element.find('.capa_inputtype');

    var urlHint = runtime.handlerUrl(element, 'hint_reponse');
    var urlSave = runtime.handlerUrl(element, 'save_response');
    var urlSubmit = runtime.handlerUrl(element, 'submit');


    // POLYFILL notify if it does not exist. Like in the xblock workbench.
    runtime.notify = runtime.notify || function () {
        console.log('POLYFILL runtime.notify', arguments);
    };

    function setClassForStudentAnswerParent(new_class) {
        capaInputType.removeClass('correct');
        capaInputType.removeClass('incorrect');
        capaInputType.removeClass('unanswered');
        capaInputType.addClass(new_class); 
    }

    buttonSubmit.on('click', function () {
        buttonSubmit.text('Checking...');
        runtime.notify('submit', {
            message: 'Submitting...',
            state: 'start'
        });
        $.ajax(urlSubmit, {
            type: 'POST',
            data: JSON.stringify({
                'student_answer': $element.find('.student_answer').val()
            }),
            success: function buttonSubmitOnSuccess(response) {
                buttonSubmit.text('Checkingvjjasldfk;as');
                
                buttonSave.addClass(response.hide_submit_class);
                buttonSubmit.addClass(response.hide_submit_class);
                buttonSubmit.text('Submit');
                
                attemptsMessage.text(response.attempts_message);
                feedbackLabel.text(response.feedback_label);
                feedbackText.text(response.feedback_message);
                hintText.text('');
                progressMessage.text(response.progress_message);
                savedMessage.text('');
                submissionReceivedMessage.text(response.submitted_message);
                
                setClassForStudentAnswerParent(response.indicator_class); 

                runtime.notify('submit', {
                    state: 'end'
                });
            },
            error: function buttonSubmitOnError() {
                runtime.notify('error', {});
            }
        });
        return false;
    });

    buttonSave.on('click', function () {
        buttonSave.text('Checking...');
        runtime.notify('save', {
            message: 'Saving...',
            state: 'start'
        });
        $.ajax(urlSave, {
            type: 'POST',
            data: JSON.stringify({
                'student_answer': $element.find('.student_answer').val()
            }),
            success: function buttonSaveOnSuccess(response) {
                buttonSave.addClass(response.hide_submit_class);
                buttonSave.text('Save');
                buttonSubmit.addClass(response.hide_submit_class);
                savedMessage.text(response.saved_message);
                runtime.notify('save', {
                    state: 'end'
                });
            },
            error: function buttonSaveOnError() {
                runtime.notify('error', {});
            }
        });
        return false;
    });

    buttonHint.on('click', function () {
        runtime.notify('hint', {
            message: 'Hint',
            state: 'start'
        });
        $.ajax(urlHint, {
            type: 'POST',
            data: JSON.stringify({}),
            success: function buttonHintOnSuccess(response) {
                hintText.text(response.hint_message);
                runtime.notify('hint', {
                    state: 'end'
                });
            },
            error: function buttonHintOnError() {
                runtime.notify('error', {});
            }
        });
        return false;
    });

    studentAnswer.on('keydown', function() {
        // Reset Messages
        feedbackLabel.text('');
        feedbackText.text('');
        savedMessage.text('');
        submissionReceivedMessage.text('');
        setClassForStudentAnswerParent('unanswered');
    });
}

