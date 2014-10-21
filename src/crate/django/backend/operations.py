# -*- coding: utf-8 -*-
from django.db.backends import BaseDatabaseOperations
from datetime import datetime, time, date


class DatabaseOperations(BaseDatabaseOperations):

    compiler_module = "crate.django.backend.compiler"

    def cache_key_culling_sql(self):
        """not implemented"""
        return None

    def distinct_sql(self, fields):
        if fields:
            return 'DISTINCT {0}'.format(', '.join(fields))
        else:
            return 'DISTINCT'

    def date_trunc_sql(self, lookup_type, field_name):
        return "DATE_TRUNC('%s', %s)" % (lookup_type, field_name)

    datetime_trunc_sql = date_trunc_sql

    def datetime_cast_sql(self):
        """TODO: ?"""
        return super(DatabaseOperations, self).datetime_cast_sql()

    def drop_foreignkey_sql(self):
        """not supported"""
        return ''

    def drop_sequence_sql(self, table):
        """not supported"""
        return ''

    def for_update_sql(self, nowait=False):
        return ''

    def fulltext_search_sql(self, field_name):
        """TODO: support new extended match predicate"""
        return 'match(%s, %%s)' % field_name

    def no_limit_value(self):
        return None

    def regex_lookup(self, lookup_type):
        return '%%s ~ %%s'

    def quote_name(self, name):
        if name.startswith('"') and name.endswith('"'):
            return name  # Quoting once is enough.
        return '"%s"' % name

    def sql_flush(self, style, tables, sequences, allow_cascade=False):
        return [
            'DELETE FROM {0}'.format(table) for table in tables
        ]

    def value_to_db_date(self, value):
        """transform a date or time value to milliseconds since epoque"""
        if isinstance(value, (datetime, time, date)):
            return int(value.timestamp() * 1000)
        return value

    value_to_db_datetime = value_to_db_time = value_to_db_date

    def start_transaction_sql(self):
        """not supported"""
        return ''

    def end_transaction_sql(self, success=True):
        """not supported"""
        return ''
