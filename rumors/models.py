import uuid

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from rumors.managers import ImageManager, TextManager
from rumors.utils import hash_text

TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE = 15
TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE = 0


class Model(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Review(Model):
    is_truthful = models.BooleanField(default=True)
    chat_id = models.CharField(max_length=255, null=True, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    owner = GenericForeignKey()


class TruthFullnessMixin(models.Model):
    # truthfulness_points will determine how truthful is the content image
    # -infinity to 0 is considered a rumor
    # 0 to 15 is considered unknown
    # 15 to infinity is considered as truthful news
    truthfulness_points = models.BigIntegerField(default=0)
    reviews = GenericRelation(Review)

    class Meta:
        abstract = True


class Image(Model, TruthFullnessMixin):
    original_hash = models.TextField(_('original hash'))
    hash1 = models.TextField(_('1st part of the hash'))
    hash2 = models.TextField(_('2nd part of the hash'))
    hash3 = models.TextField(_('3rd part of the hash'))
    hash4 = models.TextField(_('4th part of the hash'))
    objects = ImageManager()

    def __str__(self):
        return self.original_hash

    def save(self, *args, **kwargs):
        words = list(map(''.join, zip(*[iter(self.original_hash)]*int(len(self.original_hash)/4))))
        self.hash1 = words[0]
        self.hash2 = words[1]
        self.hash3 = words[2]
        self.hash4 = words[3]
        super().save(*args, **kwargs)

    class Meta:
        index_together = [
            ["hash1", "hash2", "hash3"],
            ["hash1", "hash2", "hash4"],
            ["hash1", "hash3", "hash4"],
            ["hash2", "hash3", "hash4"],
        ]


class Text(Model, TruthFullnessMixin):
    content = models.TextField(_('Text Content'), null=True, blank=True)
    content_md5 = models.UUIDField(editable=False, unique=True)
    objects = TextManager()

    def save(self, *args, **kwargs):
        self.content_md5 = hash_text(self.content)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.content[:100]
