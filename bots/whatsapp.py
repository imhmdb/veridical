import io

import requests
from twilio.twiml.messaging_response import MessagingResponse

from bots.decorators import arabic_only
from rumors.models import (
    TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE,
    TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE,
)
from django.utils.translation import gettext as _
from rumors.utils import (
    check_if_image_exists_and_is_rumor,
    check_text,
)


def get_response_message(content, content_type):
    if 0 < content.truthfulness_points <= TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE:
        return _(
            "we're still not sure about this, some people say it's true,"
            " but we're not confident about this information yet."
        )
    elif content.truthfulness_points == 0:
        return _(
                "We have no information about the truthfulness of this {content_type},"
                " so we classify it as unknown."
        ).format(content_type=_(content_type))

    elif content.truthfulness_points < TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE:
        return _(
              "Our data set shows that this {content_type} has"
              " no truthfulness, hence it's a rumor."
        ).format(content_type=_(content_type))
    elif content.truthfulness_points > TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE:
        return _(
            "Our data set shows that this {content_type} is"
            " truthful, hence it's not a rumor.").format(content_type=_(content_type))
    else:
        return "error"


@arabic_only
def process_request_data(data):
    resp = MessagingResponse()
    if int(data['NumMedia']) > 0 and 'image' in data.get('MediaContentType0'):
        response = requests.get(data['MediaUrl0'])
        imag_file = io.BytesIO(response.content)
        image = check_if_image_exists_and_is_rumor(imag_file)
        content_type = _('Image')
        resp.message(get_response_message(image, content_type))
    if data['Body']:
        text = check_text(data['Body'])
        content_type = _('text')
        resp.message(get_response_message(text, content_type))
    return resp.to_xml()
