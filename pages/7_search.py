"""Dedicated search page that reuses the feed result renderer."""

from importlib import import_module


if __name__ == '__main__':
    import_module('pages.1_feed').main(search_mode=True)
