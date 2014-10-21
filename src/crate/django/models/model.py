# -*- coding: utf-8; -*-
#
# Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.
from django.db.models import Model
from django.db.models.base import ModelBase, subclass_exception

from django.apps import apps
from django.apps.config import MODELS_MODULE_NAME
from django.core.exceptions import (ObjectDoesNotExist,
    MultipleObjectsReturned, FieldError)
from django.db.models.fields.related import OneToOneField
from django.db.models.options import Options
from django.utils import six
from django.utils.deprecation import RemovedInDjango19Warning

import warnings
import sys


from crate.django.models.manager import CrateManager


class CrateOptions(Options):

    DEFAULT_NUMBER_OF_SHARDS = 5
    DEFAULT_NUMBER_OF_REPLICAS = '0-all'
    DEFAULT_CLUSTERED_BY_COLUMN = None
    DEFAULT_PARTITIONED_BY = []
    DEFAULT_REFRESH_INTERVAL = None

    def __init__(self, meta, app_label=None):
        super(CrateOptions, self).__init__(meta, app_label=app_label)

        self.number_of_shards = self.get_and_del_attr(self.meta, "number_of_shards", self.DEFAULT_NUMBER_OF_SHARDS)
        self.number_of_replicas = self.get_and_del_attr(self.meta, "number_of_replicas", self.DEFAULT_NUMBER_OF_REPLICAS)
        self.clustered_by = self.get_and_del_attr(self.meta, "clustered_by", self.DEFAULT_CLUSTERED_BY_COLUMN)
        self.partitioned_by = self.get_and_del_attr(self.meta, "partitioned_by", self.DEFAULT_PARTITIONED_BY)
        self.refresh_interval = self.get_and_del_attr(self.meta, "refresh_interval", self.DEFAULT_REFRESH_INTERVAL)

    def get_and_del_attr(self, obj, attr_name, default=None):
        attr = getattr(obj, attr_name, None)
        try:
            delattr(obj, attr_name)
        except AttributeError:
            pass # not there, that's ok
        return attr


class CrateModelBase(ModelBase):

    def __new__(cls, name, bases, attrs):
        """
        HACK: had to copy the whole method in order to change the Options implementation
        to support Crate options - WTF!!!
        """

        super_new = super(ModelBase, cls).__new__

        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents or name == 'CrateModel':
            return super_new(cls, name, bases, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        attr_meta = attrs.pop('Meta', None)
        abstract = getattr(attr_meta, 'abstract', False)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        # Look for an application configuration to attach the model to.
        app_config = apps.get_containing_app_config(module)

        if getattr(meta, 'app_label', None) is None:

            if app_config is None:
                # If the model is imported before the configuration for its
                # application is created (#21719), or isn't in an installed
                # application (#21680), use the legacy logic to figure out the
                # app_label by looking one level up from the package or module
                # named 'models'. If no such package or module exists, fall
                # back to looking one level up from the module this model is
                # defined in.

                # For 'django.contrib.sites.models', this would be 'sites'.
                # For 'geo.models.places' this would be 'geo'.

                msg = (
                    "Model class %s.%s doesn't declare an explicit app_label "
                    "and either isn't in an application in INSTALLED_APPS or "
                    "else was imported before its application was loaded. " %
                    (module, name))
                if abstract:
                    msg += "Its app_label will be set to None in Django 1.9."
                else:
                    msg += "This will no longer be supported in Django 1.9."
                warnings.warn(msg, RemovedInDjango19Warning, stacklevel=2)

                model_module = sys.modules[new_class.__module__]
                package_components = model_module.__name__.split('.')
                package_components.reverse()  # find the last occurrence of 'models'
                try:
                    app_label_index = package_components.index(MODELS_MODULE_NAME) + 1
                except ValueError:
                    app_label_index = 1
                kwargs = {"app_label": package_components[app_label_index]}

            else:
                kwargs = {"app_label": app_config.label}

        else:
            kwargs = {}

        # THIS IS OUR CHANGE
        new_class.add_to_class('_meta', CrateOptions(meta, **kwargs))
        if not abstract:
            new_class.add_to_class(
                'DoesNotExist',
                subclass_exception(
                    str('DoesNotExist'),
                    tuple(x.DoesNotExist for x in parents if hasattr(x, '_meta') and not x._meta.abstract) or (ObjectDoesNotExist,),
                    module,
                    attached_to=new_class))
            new_class.add_to_class(
                'MultipleObjectsReturned',
                subclass_exception(
                    str('MultipleObjectsReturned'),
                    tuple(x.MultipleObjectsReturned for x in parents if hasattr(x, '_meta') and not x._meta.abstract) or (MultipleObjectsReturned,),
                    module,
                    attached_to=new_class))
            if base_meta and not base_meta.abstract:
                # Non-abstract child classes inherit some attributes from their
                # non-abstract parent (unless an ABC comes before it in the
                # method resolution order).
                if not hasattr(meta, 'ordering'):
                    new_class._meta.ordering = base_meta.ordering
                if not hasattr(meta, 'get_latest_by'):
                    new_class._meta.get_latest_by = base_meta.get_latest_by

        is_proxy = new_class._meta.proxy

        # If the model is a proxy, ensure that the base class
        # hasn't been swapped out.
        if is_proxy and base_meta and base_meta.swapped:
            raise TypeError("%s cannot proxy the swapped model '%s'." % (name, base_meta.swapped))

        if getattr(new_class, '_default_manager', None):
            if not is_proxy:
                # Multi-table inheritance doesn't inherit default manager from
                # parents.
                new_class._default_manager = None
                new_class._base_manager = None
            else:
                # Proxy classes do inherit parent's default manager, if none is
                # set explicitly.
                new_class._default_manager = new_class._default_manager._copy_to_model(new_class)
                new_class._base_manager = new_class._base_manager._copy_to_model(new_class)

        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        # All the fields of any type declared on this model
        new_fields = (
            new_class._meta.local_fields +
            new_class._meta.local_many_to_many +
            new_class._meta.virtual_fields
        )
        field_names = set(f.name for f in new_fields)

        # Basic setup for proxy models.
        if is_proxy:
            base = None
            for parent in [kls for kls in parents if hasattr(kls, '_meta')]:
                if parent._meta.abstract:
                    if parent._meta.fields:
                        raise TypeError("Abstract base class containing model fields not permitted for proxy model '%s'." % name)
                    else:
                        continue
                if base is not None:
                    raise TypeError("Proxy model '%s' has more than one non-abstract model base class." % name)
                else:
                    base = parent
            if base is None:
                raise TypeError("Proxy model '%s' has no non-abstract model base class." % name)
            new_class._meta.setup_proxy(base)
            new_class._meta.concrete_model = base._meta.concrete_model
        else:
            new_class._meta.concrete_model = new_class

        # Collect the parent links for multi-table inheritance.
        parent_links = {}
        for base in reversed([new_class] + parents):
            # Conceptually equivalent to `if base is Model`.
            if not hasattr(base, '_meta'):
                continue
            # Skip concrete parent classes.
            if base != new_class and not base._meta.abstract:
                continue
            # Locate OneToOneField instances.
            for field in base._meta.local_fields:
                if isinstance(field, OneToOneField):
                    parent_links[field.rel.to] = field

        # Do the appropriate setup for any model parents.
        for base in parents:
            original_base = base
            if not hasattr(base, '_meta'):
                # Things without _meta aren't functional models, so they're
                # uninteresting parents.
                continue

            parent_fields = base._meta.local_fields + base._meta.local_many_to_many
            # Check for clashes between locally declared fields and those
            # on the base classes (we cannot handle shadowed fields at the
            # moment).
            for field in parent_fields:
                if field.name in field_names:
                    raise FieldError(
                        'Local field %r in class %r clashes '
                        'with field of similar name from '
                        'base class %r' % (field.name, name, base.__name__)
                    )
            if not base._meta.abstract:
                # Concrete classes...
                base = base._meta.concrete_model
                if base in parent_links:
                    field = parent_links[base]
                elif not is_proxy:
                    attr_name = '%s_ptr' % base._meta.model_name
                    field = OneToOneField(base, name=attr_name,
                            auto_created=True, parent_link=True)
                    # Only add the ptr field if it's not already present;
                    # e.g. migrations will already have it specified
                    if not hasattr(new_class, attr_name):
                        new_class.add_to_class(attr_name, field)
                else:
                    field = None
                new_class._meta.parents[base] = field
            else:
                # .. and abstract ones.
                for field in parent_fields:
                    new_class.add_to_class(field.name, copy.deepcopy(field))

                # Pass any non-abstract parent classes onto child.
                new_class._meta.parents.update(base._meta.parents)

            # Inherit managers from the abstract base classes.
            new_class.copy_managers(base._meta.abstract_managers)

            # Proxy models inherit the non-abstract managers from their base,
            # unless they have redefined any of them.
            if is_proxy:
                new_class.copy_managers(original_base._meta.concrete_managers)

            # Inherit virtual fields (like GenericForeignKey) from the parent
            # class
            for field in base._meta.virtual_fields:
                if base._meta.abstract and field.name in field_names:
                    raise FieldError(
                        'Local field %r in class %r clashes '
                        'with field of similar name from '
                        'abstract base class %r' % (field.name, name, base.__name__)
                    )
                new_class.add_to_class(field.name, copy.deepcopy(field))

        if abstract:
            # Abstract base models can't be instantiated and don't appear in
            # the list of models for an app. We do the final setup for them a
            # little differently from normal models.
            attr_meta.abstract = False
            new_class.Meta = attr_meta
            return new_class

        new_class._prepare()
        new_class._meta.apps.register_model(new_class._meta.app_label, new_class)
        return new_class


class CrateModel(six.with_metaclass(CrateModelBase, Model)):
    """
    the model to use when storing stuff in crate
    it allows us to specify options in Meta we otherwise couldn't use
    """
