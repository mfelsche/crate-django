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

    def as_sql(self):
        # We don't need quote_name_unless_alias() here, since these are all
        # going to be column names (so we can avoid the extra overhead).
        qn = self.connection.ops.quote_name
        opts = self.query.get_meta()
        result = ['INSERT INTO %s' % qn(opts.db_table)]

        has_fields = bool(self.query.fields)
        fields = self.query.fields if has_fields else [opts.pk]
        result.append('(%s)' % ', '.join(qn(f.column) for f in fields))

        if has_fields:
            params = values = [
                [
                    f.get_db_prep_save(getattr(obj, f.attname) if self.query.raw else f.pre_save(obj, True), connection=self.connection)
                    for f in fields
                ]
                for obj in self.query.objs
            ]
        else:
            values = [[self.connection.ops.pk_default_value()] for obj in self.query.objs]
            params = [[]]
            fields = [None]
        can_bulk = (not any(hasattr(field, "get_placeholder") for field in fields) and
            not self.return_id and self.connection.features.has_bulk_insert)

        if can_bulk:
            placeholders = [["%s"] * len(fields)]
        else:
            placeholders = [
                [self.placeholder(field, v) for field, v in zip(fields, val)]
                for val in values
            ]
            # Oracle Spatial needs to remove some values due to #10888
            params = self.connection.ops.modify_insert_params(placeholders, params)
        if self.return_id and self.connection.features.can_return_id_from_insert:
            params = params[0]
            col = "%s.%s" % (qn(opts.db_table), qn(opts.pk.column))
            result.append("VALUES (%s)" % ", ".join(placeholders[0]))
            r_fmt, r_params = self.connection.ops.return_insert_id()
            # Skip empty r_fmt to allow subclasses to customize behavior for
            # 3rd party backends. Refs #19096.
            if r_fmt:
                result.append(r_fmt % col)
                params += r_params
            return [(" ".join(result), tuple(params))]
        if can_bulk:
            result.append(self.connection.ops.bulk_insert_sql(fields, len(values)))
            return [(" ".join(result), tuple(v for val in values for v in val))]
        else:
            return [
                (" ".join(result + ["VALUES (%s)" % ", ".join(p)]), vals)
                for p, vals in zip(placeholders, params)
            ]


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
