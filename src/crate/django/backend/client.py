# -*- coding: utf-8 -*-
from django.db.backends import BaseDatabaseClient
from crate.crash.command import main as crash_main


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'crash'

    def runshell(self):
        """TODO: run shell"""
        settings_dict = self.connection.settings_dict

        import sys
        sys.argv = [sys.argv[0], "--hosts"]
        for server in settings_dict['SERVERS']:
            sys.argv.extend(("--hosts", server))
        crash_main()
