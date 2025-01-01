====
dlhn
====


.. image:: https://img.shields.io/pypi/v/dlhn.svg
        :target: https://pypi.python.org/pypi/dlhn

.. .. image:: https://img.shields.io/travis/westurner/dlhn.svg
..        :target: https://travis-ci.org/westurner/dlhn

.. .. image:: https://readthedocs.org/projects/dlhn/badge/?version=latest
..        :target: https://dlhn.readthedocs.io/en/latest/?badge=latest
..        :alt: Documentation Status


.. .. image:: https://pyup.io/repos/github/westurner/dlhn/shield.svg
..     :target: https://pyup.io/repos/github/westurner/dlhn/
..     :alt: Updates



dlhn is a Python CLI script to archive my comments and submissions
from the Hacker News API
and generate a static HTML archive with a Jinja2 template;
to create a one-page archive that's `Ctrl-F`-able.


Features
--------

* Download comments and submissions from the Hacker News API
* Archive comment trees and submissions as JSON
* Archive comment trees and submissions as static HTML 
  with a Jinja2 HTML template
* Aggressively cache entries that couldn't have changed
  with a two-layer caching system that includes requests_cache
  and a sqlite database

Installation
--------------

Install dlhn with pip:

.. code:: bash

    pip install dlhn

    # pip install -e git+https://github.com/westurner/dlhn#egg=dlhn
    # pip install -e git+https://github.com/westurner/dlhn@master#egg=dlhn
    # pip install -e git+https://github.com/westurner/dlhn@v0.2.6#egg=dlhn


Usage
------

Download HN comments and submissions with:

.. code:: bash

	dlhn -u dlhntestuser -o index.html --expire-newerthan 14d

Optionally, create a repo for e.g. GitHub Pages and add a ``Makefile``:

.. code:: makefile

    # hnlog Makefile

    USERNAME:=dlhntestuser

    default: backup

    install:
        pip install -e git+https://github.com/westurner/dlhn#egg=dlhn

    backup:
        @# items with a cachetime newer than 14d ago may need to be pulled again
        @# because they may not be locked yet (cachetime != item_time)
        dlhn -u '$(USERNAME)' -o index.html --expire-newerthan 14d

    backup-nocache:
        dlhn -u '$(USERNAME)' -o index.html

    commit:
        git add ./index.html ./index.html.json ./dlhn.sqlite && \
        git commit -m ":books: Updated index.html, index.html.json, and dlhn.sqlite"

    push:
        git push

    all: backup commit push

And pass `USERNAME` as an arg when calling ``make``:

.. code:: bash

    make all USERNAME=dlhntestuser

References
-----------

- Hacker News Guidelines: https://news.ycombinator.com/newsguidelines.html
- Hacker News API docs: https://github.com/HackerNews/API
- `dlhntestuser <https://news.ycombinator.com/user?id=dlhntestuser>`__

  - Submissions: https://news.ycombinator.com/submitted?id=dlhntestuser
  - Comments: https://news.ycombinator.com/threads?id=dlhntestuser

License
--------
BSD License


Credits
-------

* `@westurner <https://github.com/westurner>`_
