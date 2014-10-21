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
from django.db.backends.schema import BaseDatabaseSchemaEditor
from django.utils import six
from django.utils.text import force_text
import time

class CrateSchemaEditor(BaseDatabaseSchemaEditor):
    """TODO"""

    sql_delete_table = "DROP TABLE %(table)s"
    sql_create_table = "CREATE TABLE %(table)s (%(definition)s) %(partitioned)s %(clustering)s %(table_settings)s"

    def column_sql(self, model, field, include_default=False):
        # Get the column's type and use that as the basis of the SQL
        db_params = field.db_parameters(connection=self.connection)
        sql = db_params['type']
        params = []
        # Check for fields that aren't actually columns (e.g. M2M)
        if sql is None:
            # TODO: handle compound indices here?
            return None, None

        fulltext_index = getattr(field, 'fulltext_index', None)
        analyzer = getattr(field, 'analyzer', None)

        if field.primary_key:
           sql += " PRIMARY KEY"
        elif fulltext_index:
            if fulltext_index.lower() == 'off':
                sql += " INDEX OFF"
            elif fulltext_index.lower() == "fulltext":
                sql += " INDEX USING %s".format(fulltext_index.lower())
                if analyzer is not None:
                    sql += " with (analyzer=%s)"
                    params.append(analyzer)
            else:
                # can only be 'plain'
                sql += " INDEX USING %s" % fulltext_index.lower()

        return sql, params

    def skip_default(self, field):
        """
        crate does not support default values yet
        """
        return True

    def quote_value(self, value):
        if isinstance(value, six.string_types):
            return "'%s'" % self.escape_string(value)
        if isinstance(value, six.buffer_types):
            return "'%s'" % self.escape_string(force_text(value))
        return str(value)

    def escape_string(self, value):
        """
        escape single ' inside a string with ''
        """
        return value.replace("'", "''")

    def create_model(self, model):
        column_sqls = []
        params = []

        for field in model._meta.local_fields:
            # SQL
            definition, extra_params = self.column_sql(model, field)
            if definition is None:
                continue
            # Check constraints can go on the column SQL here
            db_params = field.db_parameters(connection=self.connection)
            if db_params['check']:
                definition += " CHECK (%s)" % db_params['check']

            # Autoincrement SQL (for backends with inline variant)
            col_type_suffix = field.db_type_suffix(connection=self.connection)
            if col_type_suffix:
                definition += " %s" % col_type_suffix
            params.extend(extra_params)
            # Indexes
            if field.db_index and not field.unique:
                self.deferred_sql.append(
                    self.sql_create_index % {
                        "name": self._create_index_name(model, [field.column], suffix=""),
                        "table": self.quote_name(model._meta.db_table),
                        "columns": self.quote_name(field.column),
                        "extra": "",
                    }
                )
            # FK
            """NOT SUPPORTED

            if field.rel and field.db_constraint:
                to_table = field.rel.to._meta.db_table
                to_column = field.rel.to._meta.get_field(field.rel.field_name).column
                if self.connection.features.supports_foreign_keys:
                    self.deferred_sql.append(
                        self.sql_create_fk % {
                            "name": self._create_index_name(model, [field.column], suffix="_fk_%s_%s" % (to_table, to_column)),
                            "table": self.quote_name(model._meta.db_table),
                            "column": self.quote_name(field.column),
                            "to_table": self.quote_name(to_table),
                            "to_column": self.quote_name(to_column),
                        }
                    )
                elif self.sql_create_inline_fk:
                    definition += " " + self.sql_create_inline_fk % {
                        "to_table": self.quote_name(to_table),
                        "to_column": self.quote_name(to_column),
                    }
            """
            # Add the SQL to our big list
            column_sqls.append("%s %s" % (
                self.quote_name(field.column),
                definition,
            ))
            """NOT SUPPORTED
            # Autoincrement SQL (for backends with post table definition variant)
            if field.get_internal_type() == "AutoField":
                autoinc_sql = self.connection.ops.autoinc_sql(model._meta.db_table, field.column)
                if autoinc_sql:
                    self.deferred_sql.extend(autoinc_sql)
            """

        # CRATE OPTIONS
        clustered_by = getattr(model._meta, "clustered_by", None)
        number_of_shards = getattr(model._meta, "number_of_shards", None)
        clustering = ""
        if clustered_by or number_of_shards:
            clustering = " CLUSTERED"
            if clustered_by:
                clustering += " BY ({0})".format(self.quote_name(clustered_by))
            if number_of_shards:
                clustering += " INTO {0} SHARDS".format(number_of_shards)

        partitioned = ""
        partitioned_by = getattr(model._meta, "partitioned_by", [])
        if partitioned_by:
            partitioned = " PARTITIONED BY ({0})".format(
                ", ".join((self.quote_name(partition) for partition in partitioned_by))
            )

        number_of_replicas = getattr(model._meta, "number_of_replicas", None)  # TODO: move to global default
        refresh_interval = getattr(model._meta, "refresh_interval", None)
        table_settings = ""
        if number_of_replicas or refresh_interval:
            table_settings = "WITH ("
            table_settings += "number_of_replicas=?"
            params.append(number_of_replicas)
            table_settings += ", refresh_interval=?"
            params.append(refresh_interval)
            table_settings += ")"


        sql = self.sql_create_table % {
            "table": self.quote_name(model._meta.db_table),
            "definition": ", ".join(column_sqls),
            "clustering": clustering,
            "partitioned": partitioned,
            "table_settings": table_settings
        }

        self.execute(sql, params)

        retries = 5
        while retries > 0:
            # wait for table to be ready
            try:
                self.execute("select * from %s " % self.quote_name(model._meta.db_table))
            except Exception as e:
                time.sleep(.5)
                retries -= 1
            else:
                break
        """NOT SUPPORTED
        # Add any index_togethers
        for fields in model._meta.index_together:
            columns = [model._meta.get_field_by_name(field)[0].column for field in fields]
            self.execute(self.sql_create_index % {
                "table": self.quote_name(model._meta.db_table),
                "name": self._create_index_name(model, columns, suffix="_idx"),
                "columns": ", ".join(self.quote_name(column) for column in columns),
                "extra": "",
            })
        # Make M2M tables
        for field in model._meta.local^_many_to_many:
            if field.rel.through._meta.auto_created:
                self.create_model(field.rel.through)
        """

    def delete_model(self, model):
        super(CrateSchemaEditor, self).delete_model(model)

    def alter_db_table(self, model, old_db_table, new_db_table):
        raise NotImplementedError("cannot change the table name")

    def alter_db_tablespace(self, model, old_db_tablespace, new_db_tablespace):
        raise NotImplementedError("no tablespace support in crate")

    def add_field(self, model, field):
        return super(CrateSchemaEditor, self).add_field(model, field)

    def remove_field(self, model, field):
        raise NotImplementedError("removing fields is not implemented")

    def alter_field(self, model, old_field, new_field, strict=False):
        raise NotImplementedError("changing a field is not supported")

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        pass
