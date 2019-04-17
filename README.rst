====
dlhn
====


.. image:: https://img.shields.io/pypi/v/dlhn.svg
        :target: https://pypi.python.org/pypi/dlhn

.. image:: https://img.shields.io/travis/westurner/dlhn.svg
        :target: https://travis-ci.org/westurner/dlhn

.. .. image:: https://readthedocs.org/projects/dlhn/badge/?version=latest
..        :target: https://dlhn.readthedocs.io/en/latest/?badge=latest
..        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/westurner/dlhn/shield.svg
     :target: https://pyup.io/repos/github/westurner/dlhn/
     :alt: Updates



dlhn is a a Python CLI script to download my comments and submissions
from the Firebase HackerNews API
and generate a static HTML archive with a Jinja2 template


* Free software: BSD license


Features
--------

* Download comments and submissions from the Firebase HackerNews API
* Archive comment trees and submissions as JSON
* Archive comment trees and submissions as static HTML 
  with a Jinja2 HTML template
* Aggressively cache entries that couldn't have changed
  with a two-layer caching system that includes requests_cache
  and a sqlite database

Credits
-------

* `@westurner <https://github.com/westurner>`_
