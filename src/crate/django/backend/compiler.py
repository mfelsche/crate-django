# -*- coding: utf-8 -*-

from django.db.models.sql import compiler


class CrateParameterMixin(object):
    def as_sql(self, **kwargs):
        if kwargs:
            result = super(CrateParameterMixin, self).as_sql(**kwargs)
        else:
            result = super(CrateParameterMixin, self).as_sql()
        if isinstance(result, list):
            sql, params = result[0]
            return [(sql.replace("%s", "?"), params)]
        else:
            return result[0].replace("%s", "?"), result[1]


class SQLCompiler(CrateParameterMixin, compiler.SQLCompiler):
    pass


class SQLInsertCompiler(CrateParameterMixin, compiler.SQLInsertCompiler):
    """TODO: add _id if primary key is not given"""
    pass


class SQLDeleteCompiler(CrateParameterMixin, compiler.SQLDeleteCompiler):
    pass


class SQLUpdateCompiler(CrateParameterMixin, compiler.SQLUpdateCompiler):
    pass


class SQLAggregateCompiler(CrateParameterMixin, compiler.SQLAggregateCompiler):
    pass


class SQLDateCompiler(CrateParameterMixin, compiler.SQLDateCompiler):
    pass


class SQLDateTimeCompiler(CrateParameterMixin, compiler.SQLDateTimeCompiler):
    pass
