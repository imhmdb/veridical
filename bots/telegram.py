import io
import json
import time

import telebot
from django.conf import settings
from django.db.models import F
from django.utils.translation import gettext as _
from redis import Redis
from telebot import types
from telebot.handler_backends import RedisHandlerBackend
from telebot.types import Update

from bots.decorators import bot_respects_user_language
from rumors.models import (
    Image,
    Review,
    Text,
    TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE,
    TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE,
)
from rumors.utils import get_image_hash, process_image_hash, process_text

redis = Redis.from_url(settings.REDIS_URL)
__redis_handler = RedisHandlerBackend()
__redis_handler.redis = redis
bot = telebot.TeleBot(
    settings.TELEGRAM_BOT_TOKEN,
    next_step_backend=__redis_handler
)


@bot.message_handler(commands=['help', 'start'])
@bot_respects_user_language
def send_welcome(message):
    bot.reply_to(
        message=message,
        text=_(
            "Hi there, I am Veridical BOT.\n"
            "I am here to eliminate the rumors around you. 😌\n"
            "If you send or forward a message or an image to me, "
            "I will check if it is a rumor based on the data I have collected. \n"
            "you can also vote on the validity of the judgment I provide. \n"
            "This way you'll be able to help build a world with no rumors! ❤️"
        ),
    )


def validate_points(message, content, content_type):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(_('cancel'), _("vote"))

    if 0 < content.truthfulness_points <= TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE:
        bot.reply_to(
            message,
            _(
                "we're still not sure about this, some people say it's true,"
                " but we're not confident about this information yet."
            )
        )
    elif content.truthfulness_points == 0:
        bot.reply_to(
            message,
            _(
                "We have no information about the truthfulness of this {content_type},"
                " so we classify it as unknown."
            ).format(content_type=_(content_type))
        )
    elif content.truthfulness_points < TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE:
        bot.reply_to(
            message,
            _("Our data set shows that this {content_type} has"
              " no truthfulness, hence it's a rumor.").format(content_type=_(content_type))
        )
    elif content.truthfulness_points > TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE:
        bot.reply_to(
            message,
            _("Our data set shows that this {content_type} is truthful,"
              " hence it's not a rumor.").format(content_type=_(content_type))
        )
    msg = bot.send_message(
        chat_id=message.chat.id,
        text=_('if you wish to vote on the validity of this {content_type},'
               ' choose "vote".').format(content_type=_(content_type)),
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, process_option_step, content_type=content_type)


@bot.message_handler(func=lambda message: True, content_types=['text'])
@bot_respects_user_language
def check_text(message):
    chat_id = message.chat.id
    text, _ = process_text(message.text)
    redis.set(name=str(chat_id) + 'text', value=str(text.id), ex=7200)
    validate_points(message, text, 'text')


@bot.message_handler(func=lambda message: True, content_types=['photo'])
@bot_respects_user_language
def check_image(message):
    file_path = bot.get_file(message.photo[-1].file_id).file_path
    chat_id = message.chat.id
    downloaded_img = bot.download_file(file_path)
    imag_file = io.BytesIO(downloaded_img)
    img_hash = get_image_hash(imag_file)
    ids, image = process_image_hash(img_hash)
    redis.set(name=str(chat_id) + 'ids', value=json.dumps(ids), ex=7200)
    redis.set(name=str(chat_id) + 'image', value=str(image.id), ex=7200)
    validate_points(message, image, 'image')


@bot_respects_user_language
def process_option_step(message, content_type):
    from django.utils.translation import gettext as _
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(_('Lies'), _('Truth'))
    try:
        chat_id = message.chat.id
        option = message.text
        if option in [_("vote"), _(u'cancel')]:
            if option == _("vote"):
                msg = bot.reply_to(
                    message,
                    _(
                        "choose 'Truth' if you think that the {content_type} is truthful,"
                        " or choose 'Lies' if you think it's a rumor. 🧐"
                    ).format(content_type=_(content_type)),
                    reply_markup=markup
                )
                bot.register_next_step_handler(msg, process_vote, content_type=content_type)
            elif option == _('cancel'):
                markup = types.ReplyKeyboardRemove(selective=False)
                bot.reply_to(message, _('Thank you for using Veridical!'), reply_markup=markup)
                bot.clear_step_handler_by_chat_id(chat_id)
        else:
            raise Exception()
    except Exception as e:
        bot.reply_to(message, _('oooops, we had an error processing your request.'), reply_markup=markup)


@bot_respects_user_language
def process_vote(message, content_type):
    from django.utils.translation import gettext as _

    markup = types.ReplyKeyboardRemove(selective=False)
    try:
        chat_id = message.chat.id
        option = message.text
        content_id = redis.get(str(chat_id) + content_type)
        if content_type == 'image':
            model = Image
            ids = json.loads(redis.get(str(chat_id) + 'ids'))
        elif content_type == 'text':
            ids = [content_id.decode()]
            model = Text
        else:
            raise Exception()
        content = model.objects.filter(id=content_id.decode()).first()

        if option in [_("Truth"), _("Lies")]:
            if Review.objects.filter(object_id__in=ids, chat_id=chat_id).exists():
                bot.reply_to(
                    message,
                    _(
                        "it seems like you've voted on this {content_type} before,"
                        " you can only vote on an {content_type} once. 🧐"
                    ).format(content_type=_(content_type)),
                    reply_markup=markup
                )
                bot.clear_step_handler_by_chat_id(chat_id)
                return

            if option == _("Truth"):
                content.reviews.create(is_truthful=True, chat_id=chat_id)
                model.objects.filter(pk__in=ids).update(truthfulness_points=F('truthfulness_points') + 1)
            elif option == _("Lies"):
                content.reviews.create(is_truthful=False, chat_id=chat_id)
                model.objects.filter(pk__in=ids).update(truthfulness_points=F('truthfulness_points') - 1)
            bot.reply_to(
                message,
                _(
                    "Thank you for voting on this!"
                ),
                reply_markup=markup
            )
            bot.clear_step_handler_by_chat_id(chat_id)
        else:
            raise Exception()
    except Exception as e:
        bot.reply_to(message, _('oooops, we had an error processing your request.'), reply_markup=markup)
        bot.clear_step_handler_by_chat_id(message.chat.id)


def process_request_body(string: str) -> Update:
    return bot.process_new_updates([telebot.types.Update.de_json(string)])


if settings.TELEGRAM_BOT_POLLING:
    bot.remove_webhook()
    time.sleep(0.1)
    import threading
    threading.Thread(target=bot.polling, kwargs={"none_stop": True}).start()
else:
    bot.remove_webhook()
    time.sleep(0.1)
    bot.set_webhook(url='https://veridical.herokuapp.com/v1/bots/telegram/' + settings.TELEGRAM_BOT_TOKEN)
