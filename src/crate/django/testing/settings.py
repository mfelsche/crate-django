# -*- coding: utf-8 -*-
from django.conf.global_settings import MIDDLEWARE_CLASSES
DATABASES = {
    'default': {
        'ENGINE': 'crate.django.backend',
        'SERVERS': ['127.0.0.1:44218', ]
    },
    'other': {
        'ENGINE': 'crate.django.backend',
        'SERVERS': ['127.0.0.1:44218', ]
    }
}

SECRET_KEY = "0"*32

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

INSTALLED_APPS = [
    "crate.django.testing"
]

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)6s %(asctime)10s %(module)10s %(lineno)3d ] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': [
                'console',
            ],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}
