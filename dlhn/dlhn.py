#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
dlhn -- a Python CLI script to download hacker news comments and submissions
and generate a static HTML archive with a template

TODO:

- TODO: expand all / collapse all
- TODO: favorites
- TODO: Generate a project skeleton and setup.py w/ cookiecutter
"""
import codecs
import collections
import datetime
import json
import logging
import os
import sys
import time

if sys.version_info.major < 3:
    from HTMLParser import HTMLParser
    HTML_PARSER = HTMLParser()
    unescape = HTML_PARSER.unescape
else:
    import html
    unescape = html.unescape

__version__ = __import__('dlhn').__version__

import bleach
import bs4
# pip install --user certifi
import jinja2
import requests_cache

log = logging.getLogger()

chardetlog = logging.getLogger('chardet.charsetprober')
chardetlog.setLevel(logging.ERROR)


def make_throttle_hook(timeout=1.0):
    """
    Returns a response hook function which sleeps for `timeout` seconds if
    response is not cached
    """
    def hook(response, *args, **kwargs):
        if not getattr(response, 'from_cache', False):
            log.debug('sleeping')
            time.sleep(timeout)
        return response
    return hook


def remove_new_entries(self, created_after):
    """ Deletes entries from cache with creation time newer than ``created_after``
    """
    keys_to_delete = set()
    for key in self.responses:
        try:
            response, created_at = self.responses[key]
        except KeyError:
            continue
        if created_at > created_after:
            keys_to_delete.add(key)

    for key in keys_to_delete:
        self.delete(key)


REQUESTS = None


def build_requests_session(basedir,
                           expire_after=None,
                           expire_newerthan=None,
                           always_set=False):
    """
    Build a requests session

    Args:
        basedir (str): directory to store dlhn.sqlite in

    Kwargs:
        expire_after (datetime.timedelta): expire cache entries older than this
        expire_newerthan (datetime.timedelta): expire cache entries newer than
            this
        always_set (bool): if True, always set the REQUESTS global;
            otherwise don't modify the REQUESTS global
    """
    global REQUESTS
    if REQUESTS is None or always_set:
        # requests_cache.install_cache('dlhn', expire_after=expire_after)
        REQUESTS = requests_cache.CachedSession(
            cache_name=os.path.join(basedir, 'dlhn'),
            expire_after=expire_after)
        REQUESTS.hooks = {'response': make_throttle_hook(0.5)}
        if expire_after is not None:
            log.info("Removing cache entries older than %r",
                     expire_after)
            REQUESTS.cache.remove_old_entries(
                datetime.datetime.utcnow() - expire_after)
        if expire_newerthan is not None:
            log.info("Removing cache entries newer than %r",
                     expire_newerthan)
            remove_new_entries(REQUESTS.cache,
                datetime.datetime.utcnow() - expire_newerthan)
    else:
        log.error('The REQUESTS global is already set.')


def dlhn(username, output='index.html'):
    """pull hacker news comments

    Arguments:
        username (str): hackernews username

    Keyword Arguments:
        output (str): path to write output to

    Returns:
        str: HTML output

    Raises:
        Exception: ...
    """
    build_requests_session(os.path.dirname(output))

    output_json = '%s.json' % output
    log.info(
        "Pulling hacker news for user %r into %r and %r",
        username, output, output_json)

    cache = None
    if os.path.exists(output_json):
        with codecs.open(output_json, 'r', encoding='utf8') as _file:
            _data = json.load(
                _file,
                object_pairs_hook=collections.OrderedDict)
            cache = _data.get('items')
            log.info(u'Reading cache from %r (%d)' %
                     (output_json, len(cache)))

    items, roots = get_items(username, cache=cache)
    data = collections.OrderedDict()
    data['usernames'] = [username]
    data['items'] = items
    data['roots'] = roots
    html = TEMPLATE.render(**data)
    with codecs.open(output_json, 'w', encoding='utf8') as _file:
        json.dump(data, _file, indent=2)
    with codecs.open(output, 'w', encoding='utf8') as _file:
        _file.write(html)
    return html


ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS[:]
ALLOWED_TAGS.extend(['p', 'pre'])
ALLOWED_ATTRIBUTES = bleach.sanitizer.ALLOWED_ATTRIBUTES.copy()
ALLOWED_ATTRIBUTES['a'].append('rel')


def cleanup_html(html):
    return bleach.clean(
        unescape(html),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES)


def get_items(username, cache=None):
    url = (
        'https://hacker-news.firebaseio.com/v0/user/{}.json?nonce={}'
        .format(username, datetime.datetime.now().isoformat()))
    log.info(('GET', url))
    resp = REQUESTS.get(url)
    json_ = resp.json()
    items = collections.OrderedDict()
    roots = []
    # stack-based ~depth-first search (visitor pattern)
    queue = collections.deque(json_.get('submitted'))
    daysago_14 = time.mktime(
        (datetime.datetime.utcnow()-datetime.timedelta(14))
        .timetuple())
    while len(queue):
        objkey, objtype = queue.popleft(), None
        if isinstance(objkey, tuple):
            objkey, objtype = objkey
        if objkey in items:
            continue

        objjson = None
        if cache is not None:
            _obj = cache.get(str(objkey))
            if _obj is not None:
                if _obj['time'] < daysago_14:
                    objjson = _obj
                    log.info(('CACHE', objkey))

        if objjson is None:
            url = (
                'https://hacker-news.firebaseio.com/v0/item/{}.json'
                .format(objkey))
            log.info(('GET', url))
            objresp = REQUESTS.get(url)
            objjson = objresp.json()

        if objjson:
            if 'text' in objjson:
                objjson['text'] = cleanup_html(objjson['text'])
            objdate = datetime.datetime.fromtimestamp(objjson['time'])
            objjson[u'time_iso'] = objdate.strftime("%F %T%Z")
            if objtype != 'parent':
                queue.extendleft(objjson.get('kids', []))
            parent = objjson.get('parent')
            if parent is None:
                roots.append(objjson['id'])
            else:
                queue.appendleft((parent, 'parent'))
            items[objkey] = objjson
    items_sorted = collections.OrderedDict((
        (key, items.get(key)) for key in sorted(items)
    ))
    return items_sorted, roots


TEMPLATE = jinja2.Template("""
<!doctype html>
<html>
<head>
  <title>{{usernames}}'s comments</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <meta name="description" content="">
  <meta name="author" content="">
  <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.3/umd/popper.min.js" integrity="sha384-vFJXuSJphROIrBnz7yo7oB41mKfc8JzQZiCq4NCceLEaO4IHwicKwpJf9c9IpFgh" crossorigin="anonymous"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js" integrity="sha384-alpBpkh1PFOepccYVYDB4do5UnbKysX5WZXm3XxPqe5iKTfUKjNkCk9SaVuEZflJ" crossorigin="anonymous"></script>
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" integrity="sha384-PsH8R72JQ3SOdhVi3uxftmaW6Vc51MKb0q5P2rRUpPvrszuE4W1povHYgTpBfshb" crossorigin="anonymous">
  <style>
      a {
          text-decoration: underline;
      }
      a.toplink {
          text-decoration: none;
          color: #828282;

      }
      h3 a.toplink {
          padding: 0.4em;
      }
      /* body {
          background: #c0c0c0;
      } */
      .card {
          background-color: #f6f6ef;
          padding: 0.2em 1em; /* */
          margin: 0.2em;
      }
      .card-subtitle a {
          color: #828282 !important;
      }
      footer, footer a {
          text-align: center;
          color: #828282;
      }

      .bold {
          font-weight: bold;
      }
      /* div.kids {
          margin-left: 1em;
      } */
      .collapsed {
          display: none;
      }
      a.collapser {
          float:left;
          padding-right: 4px;
          margin-top: 6px;
          margin-bottom: -6px;
      }

      @media (max-width: 767px) {
          a.collapser {
              float: none;
              display: block;
          }
          .card {
              margin: 4px 0;
              padding: 0 4px;
          }
      }
  </style>
  <script>
      function toggleDownward(elem) {
          // TODO: don't toggle the whole everything thing
          item = $(elem).closest(".item");
          collapsables = item.find('.collapsable');
          state = $(elem).text();
          if (state === '[+]') {
              item.find('.collapsable').removeClass("collapsed");
              collapsables.prev('a.collapser').text('[-]');
          } else {
              item.find('.collapsable').addClass("collapsed");
              collapsables.prev('a.collapser').text('[+]');
          }
      }
  </script>
</head>
<body>
  <nav class="navbar navbar-expand-md navbar-dark bg-dark mb-4" role="navigation">
    <a class="navbar-brand" href="#">hnlog</a>
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarCollapse">
      <ul class="navbar-nav mr-auto">
        <li class="nav-item">
          <a class="nav-link" href="#contents">Contents</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#items">Items</a>
        </li>
      </ul>
    </div>
  </nav>
  <main role="main" class="container-fluid">
  <h3><a id="contents" href="#contents">Contents</a><a href="#" class="toplink">^</a></h3>
  <table class="table table-striped table-sm table-hover table-responsive">
    <caption>Table of Contents</caption>
    <thead>
        <tr>
            <th scope="col">date</th>
            <th scope="col">title</th>
            <th scope="col">user</th>
            <th scope="col">score</th>
        </tr>
    </thead>
    <tbody>
    {% for itemid in roots[:] %}
    {% set item=items.get(itemid) -%}
    {% set itemcssid="{}-{}".format(item.type, item.id) -%}
    {% set fromme=(item.by in usernames) -%}
    <tr scope="row" {% if fromme %} class="bold"{% endif %}>
        <td>{{ item.time_iso }}</td>
        <td><a href="#{{itemcssid}}">{{ item.title }}</a></td>
        <td><a href="https://news.ycombinator.com/user?id={{item.by}}">{{ item.by }}</a></td>
        <td>{{ item.score }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>

  <h3><a id="items" href="#items">Items</a><a href="#" class="toplink">^</a></h3>
  {% for itemid in roots recursive -%}
  {% set item=items.get(itemid) -%}
  {% if item != None -%}
  {% set itemcssid="{}-{}".format(item.type, item.id) -%}
  {% set fromme=(item.by in usernames) -%}
  {% set collapsed=(not fromme and item.parent) %}
  <div class="item card {{ item.type }}" id="{{ itemcssid }}">
    <div class="card-block">
      <a class="collapser" href="#{{ itemcssid }}-collapse" onclick="toggleDownward(this);event.preventDefault()">
      {%- if not fromme %}{% if collapsed %}[+]{% else %}[-]{% endif %}{% endif %}</a>
      <div class="{% if not fromme %}collapsable{% endif %}{% if collapsed %} collapsed{% endif %}" id="{{ itemcssid }}-collapse">
        <h4 class="card-title{% if fromme %} bold{% endif %}">
          {%- if item.title -%}<a href="#{{ itemcssid }}">{{ item.title }}</a>{% endif -%}
        </h4>
        <div class="card-subtitle text-muted">
          <a href="https://news.ycombinator.com/user?id={{ item.by }}">{{ item.by }}</a> |
          <a href="https://news.ycombinator.com/item?id={{ item.id }}"
          {% if not item.title %}id="{{ itemcssid }}"{% endif %}
          >{{ item.time_iso }}</a>
          {%- if item.score %} | {{ item.score }} {% endif %} | <a href="#{{ itemcssid }}">#</a> | <a href="#" class="toplink">^</a>
        </div>
        {% if item.url -%}
        <div class="card-subtitle text-muted">
            <span><a href="{{ item.url }}" rel="nofollow">{{ item.url }}</a></span>
        </div>
        {% endif -%}
        {%- if item.text %}
        <p class="card-text">{% autoescape false %}{{ item.text }}{% endautoescape %}</p>
        {%- endif -%}
        {%- if item.deleted %}<p class="card-text">[deleted]</p>{% endif -%}
        {%- if not fromme and item.parent %}</div>{% endif -%}
        {% if item.kids -%}
        <div class="kids">
          {{ loop(item.kids) }}
        </div>
        {%- endif -%}
      </div>
    </div>
  </div>
  {%- endif -%}{# item != None #}
  {%- endfor -%}
  </main>
</body>
</html>
""")


import unittest


class Test_dlhn(unittest.TestCase):

    def test_dlhn(self):
        destfile = os.path.join('.', 'test.html')
        output = dlhn('dlhntestuser', output=destfile)
        assert output
        with codecs.open(destfile, 'r', encoding='utf8') as file_:
            print(bs4.BeautifulSoup(file_, features='html.parser')
                    .find('main').prettify())

        import subprocess
        subprocess.check_call(("python", "-m", "webbrowser", destfile))


def main(argv=None):
    """
    dlhn Main function

    Keyword Arguments:
        argv (list): commandline arguments (e.g. sys.argv[1:])
    Returns:
        int: 0 if OK
    """
    import optparse

    prs = optparse.OptionParser(
            usage="%prog [-h] [-v/-q/-t] -u <username> [-o <index.html>]",
            version=__version__,
            add_help_option=False,
            description=(
                'Download comments and submissions from the'
                ' Firebase Hacker News API'
                ' and generate a static HTML archive with a Jinja2 template'
            ))

    prs.add_option('-u', '--username',
                   dest='username',
                   action='store',
                   help='HN username to retrieve comments and submissions of')

    prs.add_option('-o', '--output',
                   dest='output',
                   action='store',
                   default='index.html',
                   help='Path to write the generated HTML file to.'
                        ' The JSON and sqlite files will also be written'
                        ' to the dirname of this file')

    prs.add_option('--expire-after',
                   dest='expire_after',
                   action='store',
                   default=None,
                   help="Expire posts older than e.g. 1d or 1h")
    prs.add_option('--expire-newerthan',
                   dest='expire_newerthan',
                   action='store',
                   default=None,
                   help="Expire posts newer than e.g. 14d."
                   " HN does not allow edits after 14d.")

    prs.add_option('-h', '--help',
                   action='store_true')
    prs.add_option('-v', '--verbose',
                   dest='verbose',
                   action='store_true',)
    prs.add_option('-q', '--quiet',
                   dest='quiet',
                   action='store_true',)
    prs.add_option('-t', '--test',
                   dest='run_tests',
                   action='store_true',)

    argv = list(argv) if argv is not None else sys.argv[1:]
    log.debug('argv: %r', argv)
    (opts, args) = prs.parse_args(args=argv)
    loglevel = logging.INFO
    if opts.verbose:
        loglevel = logging.DEBUG
    elif opts.quiet:
        loglevel = logging.ERROR
    logging.basicConfig(level=loglevel)
    log.debug('opts: %r', opts)
    log.debug('args: %r', args)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        return unittest.main()

    if opts.help:
        prs.print_help()
        return 0

    if opts.username is None:
        prs.print_help()
        prs.error('-u/--username must be specified')

    def parse_timedeltastr(str_, default_days=14):
        if str_ is None:
            delta = None
        elif str_ == -1:
            delta = datetime.timedelta(days=default_days)
        elif str_.endswith('d'):
            delta = datetime.timedelta(days=int(str_[:-1]))
        elif str_.endswith('h'):
            delta = datetime.timedelta(hours=int(str_[:-1]))
        elif str_.endswith('m'):
            delta = datetime.timedelta(minutes=int(str_[:-1]))
        else:
            delta = datetime.timedelta(days=int(str_))
        return delta

    expire_after = parse_timedeltastr(opts.expire_after)
    expire_newerthan = parse_timedeltastr(opts.expire_newerthan)
    basedir = os.path.dirname(opts.output)
    build_requests_session(basedir,
                           expire_after=expire_after,
                           expire_newerthan=expire_newerthan,
                           always_set=True)

    EX_OK = 0
    output = dlhn(opts.username, output=opts.output)
    return EX_OK


if __name__ == "__main__":
    import sys
    sys.exit(main(argv=sys.argv[1:]))
