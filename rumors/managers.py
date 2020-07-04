import hashlib

from django.db.models import Manager
from django.db.models import Q


class FirstOrCreateMixin:
    def first_or_create(self, **kwargs):
        created = False
        obj = self.filter(**kwargs).first()
        if obj is None:
            obj = self.create(**kwargs)
            created = True
        return obj, created


class ImageManager(Manager, FirstOrCreateMixin):
    def similar(self, hash_str):
        words = list(map(''.join, zip(*[iter(hash_str)]*int(len(hash_str)/4))))
        c1 = Q(hash1=words[0], hash2=words[1], hash3=words[2])
        c2 = Q(hash1=words[0],  hash2=words[1], hash4=words[3])
        c3 = Q(hash1=words[0],  hash3=words[2], hash4=words[3])
        c4 = Q(hash2=words[1], hash3=words[2], hash4=words[3])
        return self.filter(c1 | c2 | c3 | c4)


class TextManager(Manager, FirstOrCreateMixin):
    def similar(self, content: str):
        return self.filter(content_md5=hashlib.md5(content.encode('utf-8')).hexdigest())
