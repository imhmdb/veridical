import hashlib
from contextlib import contextmanager

import imagehash
from PIL import Image as PImage
from django.utils import translation

HASH_SIZE = 16
HIGHFREQ_FACTOR = 4


def similar(a, b, t=0.88):
    l = min(len(a), len(b))
    t = int(0.5 + l*(1 - t))
    n = 0
    for a1, b1 in zip(a, b):
        if a1 != b1:
            n += 1
        if n > t:
            return False
    return True


def get_image_hash(file):
    return str(imagehash.phash(
        image=PImage.open(file),
        hash_size=HASH_SIZE,
        highfreq_factor=HIGHFREQ_FACTOR
    ))


def check_if_image_exists_and_is_rumor(file):
    from rumors.models import Image, TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE

    img_hash = get_image_hash(file)
    if Image.objects.filter(
            original_hash=img_hash,
            truthfulness_points__lt=TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE
    ).exists():
        return Image(truthfulness_points=-1)
    for i in Image.objects.similar(img_hash).filter(
            truthfulness_points__lt=TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE
    ).all().iterator():
        if similar(img_hash, i.original_hash):
            return Image(truthfulness_points=-1)
    return Image(truthfulness_points=0)


def get_similar_images(img_hash):
    from rumors.models import Image

    imgs = []
    for i in Image.objects.similar(img_hash).all().iterator():
        if similar(img_hash, i.original_hash):
            imgs.append(i)
    return imgs


def get_similar_texts(text: str) -> list:
    from rumors.models import Text
    texts = []
    for i in Text.objects.similar(text).all().iterator():
        texts.append(i)
    return texts


def process_image_hash(img_hash):
    from rumors.models import Image

    obj, created = Image.objects.first_or_create(original_hash=img_hash)
    similar_images_list = get_similar_images(img_hash)
    if created and len(similar_images_list) > 0:
        obj.truthfulness_points = similar_images_list[0].truthfulness_points
        obj.save()
    return [str(img.id) for img in similar_images_list], obj


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def process_text(text: str) -> tuple:
    from rumors.models import Text
    return Text.objects.first_or_create(content=text, content_md5=hash_text(text))


def check_text(text: str):
    from rumors.models import Text
    obj = Text.objects.filter(content=text, content_md5=hash_text(text)).first()
    if not obj:
        obj = Text(truthfulness_points=0)
    return obj


@contextmanager
def respect_language(language):
    if language:
        prev = translation.get_language()
        translation.activate(language)
        try:
            yield
        finally:
            translation.activate(prev)
    else:
        yield
