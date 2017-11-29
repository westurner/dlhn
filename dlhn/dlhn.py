#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
phnc -- pull hacker news comments, submissions, and favorites

TODO:

- expand all / collapse all
- favorites
- Generate a project skeleton w/ cookiecutter
- Choose a better name than phnc
  - phnc
  - https://westurner.github.io/hackernewslog
  - https://westurner.github.io/hnlog
  - https://westurner.github.io/ynewslog
"""
import codecs
import collections
import datetime
import logging
import time

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

import bleach
import bs4
# pip install --user certifi
import jinja2
import requests
import requests_cache
import urlobject

log = logging.getLogger()

chardetlog = logging.getLogger('chardet.charsetprober')
chardetlog.setLevel(logging.ERROR)

requests_cache.install_cache('phnc')


def phnc(username, output=None):
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
    username = 'westurner'
    items, roots = get_items(username)
    html = TEMPLATE.render(
        items=items,
        roots=roots,
        usernames=dict.fromkeys([username]))
    with codecs.open('test.html', 'w', encoding='utf8') as _file:
        _file.write(html)
    return html


HTML_PARSER = HTMLParser()

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS[:]
ALLOWED_TAGS.extend(['p', 'pre'])
ALLOWED_ATTRIBUTES = bleach.sanitizer.ALLOWED_ATTRIBUTES.copy()
ALLOWED_ATTRIBUTES['a'].append('rel')


def cleanup_html(html):
    return bleach.clean(
        HTML_PARSER.unescape(html),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES)


def get_items(username):
    url = 'https://hacker-news.firebaseio.com/v0/user/{}.json'.format(username)
    resp = requests.get(url)
    json = resp.json()
    items = collections.OrderedDict()
    roots = []
    # stack-based ~depth-first search (visitor pattern)
    queue = collections.deque(json.get('submitted'))
    while len(queue):
        objkey, objtype = queue.popleft(), None
        if isinstance(objkey, tuple):
            objkey, objtype = objkey
        if objkey in items:
            continue
        url = 'https://hacker-news.firebaseio.com/v0/item/{}.json'.format(objkey)
        print(('GET', url))
        objresp = requests.get(url)
        objjson = objresp.json()

        if objjson:
            if 'text' in objjson:
                objjson['text'] = cleanup_html(objjson['text'])
            if 'time' in objjson:
                objjson[u'time_iso'] = datetime.datetime.fromtimestamp(
                    objjson['time']).strftime("%F %T%Z")
            if objtype != 'parent':
                queue.extendleft(objjson.get('kids', []))
            parent = objjson.get('parent')
            if parent is None:
                roots.append(objjson['id'])
            else:
                queue.appendleft((parent, 'parent'))
            items[objkey] = objjson
        #time.sleep(0.4)
    items_sorted = collections.OrderedDict((
        (key, items.get(key)) for key in sorted(items)
    ))
    return items_sorted, roots[::-1]


TEMPLATE = jinja2.Template("""
<!doctype html>
<html>
<head>
  <title>{{usernames.keys()}}'s comments</title>
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
        </tr>
    </thead>
    <tbody>
    {% for itemid in roots[:] %}
    {% set item=items.get(itemid) -%}
    {% set itemcssid="{}-{}".format(item.type, item.id) -%}
    {% set fromme=(item.by in usernames) -%}
    <tr scope="row">
        <td>{{ item.time_iso }}</td>
        <td><a href="#{{itemcssid}}">{{ item.title }}</a><td>
        <td><span{% if fromme %} class="bold"{% endif %}>
            <a href="https://news.ycombinator.com/user?id={{item.by}}">{{ item.by }}</a></span></td>
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
          {%- if item.score %} | {{ item.score }} points {% endif -%} | <a href="#{{ itemcssid }}">#</a> | <a href="#" class="toplink">^</a>
        </div>
        <div class="card-subtitle text-muted">
            {% if item.url -%}<span><a href="{{ item.url }}" rel="nofollow">{{ item.url }}</a></span>{% endif -%}
        </div>
        {%- if item.text %}
          <p class="card-text">{% autoescape false %}{{ item.text }}{% endautoescape %}
        </p>
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


class Test_phnc(unittest.TestCase):

    def setUp(self):
        pass

    # def test_phnc(self):
    #     output = phnc('westurner', output='testoutput.html')
    #     assert bool(output)

    def test_it(self):

        output = phnc('westurner', output='test.html')
        assert output
        with codecs.open('test.html','r', encoding='utf8') as file_:
            print(bs4.BeautifulSoup(file_).find('main').prettify())

        import subprocess
        subprocess.check_call("web './test.html'", shell=True)


    def tearDown(self):
        pass


def main(argv=None):
    """
    Main function

    Keyword Arguments:
        argv (list): commandline arguments (e.g. sys.argv[1:])
    Returns:
        int:
    """
    import logging
    import optparse

    prs = optparse.OptionParser(usage="%prog [-v/-q/-t] <username>")

    prs.add_option('-u', '--username',
                   dest='username',
                   action='store')

    prs.add_option('-o', '--output',
                   dest='output',
                   action='store',
                   default='comments.html')

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    argv = list(argv) if argv else []
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
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        return unittest.main()

    EX_OK = 0
    output = phnc(opts.username, output=opts.output)
    return EX_OK


if __name__ == "__main__":
    import sys
    sys.exit(main(argv=sys.argv[1:]))
