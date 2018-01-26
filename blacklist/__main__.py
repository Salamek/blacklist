# -*- coding: utf-8 -*-


def main():
    """Entrypoint to the ``celery`` umbrella command."""
    from blacklist.bin.blacklist import main as _main
    _main()


if __name__ == '__main__':  # pragma: no cover
    main()
