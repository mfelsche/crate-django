# -*- coding: utf-8 -*-
from django.db.backends import BaseDatabaseIntrospection


class DatabaseIntrospection(BaseDatabaseIntrospection):
    data_types_reverse = {
        "boolean": "BooleanField",
        "byte": "SmallIntegerField",
        "short": "SmallIntegerField",
        "integer": "IntegerField",
        "long": "BigIntegerField",
        "float": "FloatField",
        "double": "FloatField",  # no double type in python
        "timestamp": "DateTimeField",
        "ip": "CharField",
        "string": "CharField",
        # TODO: object and array
    }

    def get_table_list(self, cursor):
        tables = []
        cursor.execute(
            "select table_name from information_schema.tables "
            "where schema_name='doc' order by table_name")
        for table_name in cursor.fetchall():
            if isinstance(table_name, list):
                table_name = table_name[0]
            tables.append(table_name)
        return tables

    def sequence_list(self):
        """sequences not supported"""
        return []

    def get_key_columns(self, cursor, table_name):
        return []

    def get_indexes(self, cursor, table_name):
        indexes = {}
        cursor.execute(
            "select constraint_name from information_schema.table_constraints "
            "where schema_name='doc' and table_name='{}'".format(table_name)
        )
        for constraints in cursor.fetchall():
            # only handle single column indices
            if len(constraints) == 1:
                colname = constraints[0]
                indexes[colname] = {
                    'primary_key': True,
                    'unique': True
                }
        return indexes

    def get_constraints(self, cursor, table_name):
        result = {}
        cursor.execute(
            "select constraint_name from information_schema.table_constraints "
            "where schema_name='doc' and table_name='{}'".format(table_name)
        )
        for constraints in cursor.fetchall():
            constraint_name = "__".join([table_name] + constraints[0])
            result[constraint_name] = {
                "columns": constraints[0],
                "primary_key": True,
                "unique": True,
                "foreign_key": None,
                "check": False,
                "index": False
            }
        return result
