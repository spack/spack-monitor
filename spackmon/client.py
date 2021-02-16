#!/usr/bin/env python

# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.logger import setup_logger
from django.core.wsgi import get_wsgi_application
from django.core import management
from spackmon.version import __version__
import argparse
import sys
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spackmon.settings")


def get_parser():
    parser = argparse.ArgumentParser(description="Spackmon: Spack Monitor.")

    parser.add_argument(
        "--version",
        dest="version",
        help="print the version and exit.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--noreload",
        dest="noreload",
        help="Tells Django to NOT use the auto-reloader.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--verbosity",
        dest="verbosity",
        help="Verbosity (0, 1, 2, 3).",
        choices=list(range(0, 4)),
        default=0,
    )

    network_group = parser.add_argument_group("NETWORKING")
    network_group.add_argument(
        "--port", dest="port", help="Port to serve application on.", default=5000
    )

    # Logging
    logging_group = parser.add_argument_group("LOGGING")

    logging_group.add_argument(
        "--quiet",
        dest="quiet",
        help="suppress logging.",
        default=False,
        action="store_true",
    )

    logging_group.add_argument(
        "--verbose",
        dest="verbose",
        help="verbose output for logging.",
        default=False,
        action="store_true",
    )

    logging_group.add_argument(
        "--log-disable-color",
        dest="disable_color",
        default=False,
        help="Disable color for spackmon logging.",
        action="store_true",
    )

    logging_group.add_argument(
        "--log-use-threads",
        dest="use_threads",
        action="store_true",
        help="Force threads rather than processes.",
    )

    description = "subparsers for Spackmon"
    subparsers = parser.add_subparsers(
        help="spackmon actions",
        title="actions",
        description=description,
        dest="command",
    )

    subparsers.add_parser("query", help="query the spackmon database")

    return parser


def main():
    """main entrypoint for spackmon"""
    parser = get_parser()

    def help(return_code=0):
        """print help, including the software version and active client
        and exit with return code.
        """
        print("\nSpackmon Interface v%s" % __version__)
        parser.print_help()
        sys.exit(return_code)

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show the version and exit
    if args.version:
        print(__version__)
        sys.exit(0)

    application = get_wsgi_application()

    # customize django logging
    setup_logger(
        quiet=args.quiet,
        nocolor=args.disable_color,
        debug=args.verbose,
        use_threads=args.use_threads,
    )

    # Migrations
    management.call_command("makemigrations", verbosity=args.verbosity)
    for app in ["users", "main", "base"]:
        management.call_command("makemigrations", app, verbosity=args.verbosity)
    management.call_command("migrate", verbosity=args.verbosity)

    # management.call_command("qcluster", verbosity=args.verbosity)
    management.call_command(
        "collectstatic", verbosity=args.verbosity, interactive=False
    )
    management.call_command(
        "runserver", args.port, verbosity=args.verbosity, noreload=not args.noreload
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
