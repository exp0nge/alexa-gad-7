from __future__ import print_function


GAD_QUESTIONS = {
    1: "How often are you feeling nervous, anxious, or on edge?",
    2: "How often are you not being able to stop or control worrying?",
    3: "How often are you worrying too much about different things?",
    4: "How often are you trouble relaxing?",
    5: "How often are you being so restless that it's hard to sit still?",
    6: "How often are you becoming easily annoyed or irritable?",
    7: "How often are you feeling afraid as if something awful might happen?"
}

ACCEPTED_NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3
}

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.3d97a668-6cd3-449f-9c6d-a35eac07552d"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

    if 'attributes' not in session:
        session['attributes'] = {}
    set_question(session['attributes'], 1)
    session['attributes']['sum'] = 0


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch

    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "AnswerIntent":
        return set_response(session['attributes'], intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response(session['attributes'])
    elif intent_name == "AMAZON.YesIntent":
        return get_yes_response(session['attributes'])
    elif (intent_name == "AMAZON.StopIntent" or
          intent_name == "AMAZON.CancelIntent" or
          intent_name == "AMAZON.NoIntent"):
        return get_halt_response()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    set_question(session['attributes'], 1)
    session['attributes']['sum'] = 0

# --------------- Functions that control the skill's behavior ------------------


def set_question(session_attributes, question_number):
    session_attributes['question'] = question_number
    return session_attributes


def get_question_number(session_attributes):
    return session_attributes['question']


def set_response(session_attributes, intent):
    if ('Number' in intent['slots'] and
            'value' in intent['slots']['Number'] and
            intent['slots']['Number']['value'].lower() in ACCEPTED_NUMBERS.keys()):

        session_attributes['sum'] += ACCEPTED_NUMBERS[intent['slots']['Number']['value']]
        if get_question_number(session_attributes) == 7:
            # done
            set_question(session_attributes, -1)
            if session_attributes['sum'] <= 5:
                speech_output = "You don't show any signs of anxiety disorder."
            elif session_attributes['sum'] <= 10:
                speech_output = "You show signs of mild anxiety."
            elif session_attributes['sum'] <= 15:
                speech_output = "You show signs of moderately severe anxiety."
            elif session_attributes['sum'] <= 21:
                speech_output = "You show signs of severe anxiety."
            else:
                speech_output = "There seems to be an error."

            card_title = "You scored " + str(session_attributes['sum'])

            speech_output += " These results should be confirmed by a professional psychiatrist."
            session_attributes['sum'] = 0
            set_question(session_attributes, 1)
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, "", True))
        else:
            set_question(session_attributes, get_question_number(session_attributes) + 1)
            next_question = GAD_QUESTIONS[get_question_number(session_attributes)]
            card_title = "Question number " + str(get_question_number(session_attributes))
            return build_response(session_attributes, build_speechlet_response(
                card_title, next_question, next_question, False))
    else:
        test_prompt = ("Please answer with a numeric response from zero to three where " +
                       "0: Not at all sure, 1: Several days, 2: Over half the days " +
                       "3: Nearly every day. ")
        test_prompt += GAD_QUESTIONS[get_question_number(session_attributes)]

        card_title = "Question number " + str(get_question_number(session_attributes))
        return build_response(session_attributes, build_speechlet_response(
            card_title, test_prompt, test_prompt, False))

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {'sum': 0}
    set_question(session_attributes, 1)

    card_title = "Starting test"
    test_prompt = ("Please answer with a numeric response from zero to three where " +
                   "0: Not at all sure, 1: Several days, 2: Over half the days " +
                   "3: Nearly every day. " +
                   "Over the last 2 weeks, how often have you been " +
                   "bothered by the following problems?")
    speech_output = ("The results of these tests should be verified with a " +
                     "professional psychiatrist. " + test_prompt)

    speech_output += GAD_QUESTIONS[1]
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, test_prompt, should_end_session))


def get_help_response(session_attributes):
    """Handles when user asks Help"""
    card_title = "Help"
    speech_output = ("The Generalized Anxiety Disorder 7 is a " +
                     "questionnaire for both screening and measuring generalized " +
                     "anxiety disorder over the last two weeks. " +
                     "The results of the test from the seven questions " +
                     "are tallied up to form a score. " +
                     "The score system per question is as follows: Not at all (0 points), " +
                     "Several days (1 point), More than half the days (2 points), " +
                     "Nearly every day (3 points). To stop the test at " +
                     "any time, simply say cancel or stop. The test results will be " +
                     "deleted. Would you like to continue with the test?")

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, False))

def get_halt_response():
    """Stops test"""
    return build_response({}, build_speechlet_response(
        "Test has been canceled", "", "", True))

def get_yes_response(session_attributes):
    """Asks the question"""
    question = GAD_QUESTIONS[get_question_number(session_attributes)]
    card_title = "Question number " + str(get_question_number(session_attributes))
    return build_response(session_attributes, build_speechlet_response(
        card_title, question, question, False))

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }