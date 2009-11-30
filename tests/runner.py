import optparse
import os
import sys

from django.conf import settings
from django.core.management import setup_environ, call_command

import pinax
from pinax.utils.importlib import import_module


#
# thoughts on a test runner. the goal is to run all tests in Pinax.
# tests live in apps. one approach is to run each project tests. however,
# this will result in potentionally running tests more than once for an
# app. rather, we can setup a fake project for each app and then run
# their tests.
#


PINAX_ROOT = os.path.abspath(os.path.dirname(pinax.__file__))
PINAX_PROJECTS = [
    "basic_project",
    "code_project",
    "intranet_project",
    "private_beta_project",
    "sample_group_project",
    "social_project",
]

# setup sys.path for Pinax and projects
sys.path.insert(0, os.path.join(PINAX_ROOT, "apps"))
sys.path.insert(0, os.path.join(PINAX_ROOT, "projects"))


def setup_project(name):
    """
    Helper for build_app_list to prepare the process for settings of a given
    Pinax project.
    """
    settings_mod = import_module("%s.settings" % name)
    setup_environ(settings_mod)


def build_app_list(projects):
    """
    Given a list of projects return a unique list of apps.
    """
    apps = set()
    
    for project in projects:
        setup_project(project)
        settings._setup()
        apps.update(settings.INSTALLED_APPS)
    
    return list(apps)


def build_project_app_paths(projects):
    app_dirs = []
    for project in projects:
        app_dir = os.path.join(PINAX_ROOT, "projects", project, "apps")
        app_dirs.append(app_dir)
    return app_dirs


def setup_test_environment():
    apps = build_app_list(PINAX_PROJECTS)
    
    # @@@ not quite sure how to handle this yet, but basic_profiles and
    # profiles clash as one is a fork of the other. for now we can just test
    # profiles behavior
    apps.remove("basic_profiles")
    
    # setup path for all project apps/
    sys.path = build_project_app_paths(PINAX_PROJECTS) + sys.path[:]
    
    # reset settings
    settings._wrapped = None
    
    # set up settings for running tests for all apps
    settings.configure(**{
        "DATABASE_ENGINE": "sqlite3",
        "SITE_ID": 1,
        "ROOT_URLCONF": "",
        "STATIC_URL": "/site_media/static/",
        "MIDDLEWARE_CLASSES": [
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
        ],
        "INSTALLED_APPS": apps,
    })


def main():
    
    usage = "%prog [options] [app app app]"
    parser = optparse.OptionParser(usage=usage)
    
    parser.add_option("-v", "--verbosity",
        action = "store",
        dest = "verbosity",
        default = "0",
        type = "choice",
        choices = ["0", "1", "2"],
        help = "verbosity level; 0=minimal output, 1=normal output, 2=all output",
    )
    
    options, args = parser.parse_args()
    
    setup_test_environment()
    call_command("test", *args, verbosity=int(options.verbosity))


if __name__ == "__main__":
    main()
