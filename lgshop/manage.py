#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    # django默认的配置文件。这是上线后使用它
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lgshop.settings')
    # 开发环境的配置文件。这是开发时使用它
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lgshop.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
