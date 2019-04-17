#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `dlhn` package."""

import difflib
import os

import bs4
import pytest

from dlhn import dlhn
from dlhn.dlhn import main

TESTUSERNAME = "dlhntestuser"

# def test_content(response):
#     """Sample pytest test function with the pytest fixture as an argument."""
#     # from bs4 import BeautifulSoup
#     # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_main_noargs():
    with pytest.raises(SystemExit):
        output = main([])
        assert output == 2


def test_main_help():
    output = main(["-h", "--help"])
    assert output == 0


def test_dlhn_dlhntestuser(tmpdir, username=TESTUSERNAME):
    destfile = str(tmpdir / "dlhn-test1.html")
    output = dlhn.dlhn(username, output=destfile)
    assert output
    with open(destfile, "r") as file_:
        bs = bs4.BeautifulSoup(file_, features='html.parser')
        main = bs.find("main")
        assert bool(main) == True
        assert bs.find("title").string == "['%s']'s comments" % username
        link = bs.find("a",
                dict(href="https://www.ycombinator.com/companies/"))
        assert bool(link) == True


def test_main_pull(tmpdir, username=TESTUSERNAME):
    testfiles = [str(tmpdir / "dlhn-test%d.html") % n for n in (1, 2)]
    args = ["-u", username, "-o", testfiles[0]]
    output = main(args)
    assert output == 0
    args = ["-u", username, "-o", testfiles[1], "--expire-newerthan", "14d"]
    output = main(args)
    assert output == 0

    with open(testfiles[0], "r") as _file1:
        with open(testfiles[1], "r") as _file2:
            file1 = _file1.readlines()
            file2 = _file2.readlines()

    diff = difflib.unified_diff(file1, file2)
    assert "" == "\n".join(list(diff))
