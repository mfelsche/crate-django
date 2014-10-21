# -*- coding: utf-8 -*-
from crate.django.models.fields import *
from crate.django.models.model import CrateModel
from crate.django.models.manager import CrateManager


class User(CrateModel):
    id = IntegerField(primary_key=True)
    username = StringField()
    slogan = StringField(fulltext_index=True, analyzer="english")

    objects = CrateManager()

    class Meta:
        number_of_replicas = 0
        number_of_shards = 4
        clustered_by = "id"
