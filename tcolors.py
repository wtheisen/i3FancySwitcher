#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    tcolors.py
    ~~~~~~~~~~

    Get/Set terminal ANSI colors.

    Code for retrieving terminal colors was adopted from
    http://xyne.archlinux.ca/projects/python3-colorsysplus/.

    :Compatibility: Python 2.7 / 3.2
    :Copyright: (c) 2014 Miroslav Koškár <http://mkoskar.com/>
    :License: BSD 2-Clause, see LICENSE for details
"""

from __future__ import print_function

from contextlib import contextmanager
from signal import signal, SIG_DFL, SIGINT
from sys import exit, stdin, stdout, stderr
import os
import re
import select
import subprocess
import termios

_poll = None
_TERM = os.environ.get('TERM')
if os.environ.get('TMUX'):
    _seqfmt = '\033Ptmux;\033{}\a\033\\'
elif _TERM and (_TERM == 'screen' or _TERM.startswith('screen-')):
    _seqfmt = '\033P{}\a\033\\'
else:
    _seqfmt = '{}\033\\'


def _writeseq(seq, flush=False):
    stdout.write(_seqfmt.format(seq))
    if flush:
        stdout.flush()


def set_colorp(n, c, flush=False):
    _writeseq('\033]4;{};{}'.format(n, c), flush)


def get_colorp(n):
    return get_term_color([4, n])


def set_colorfg(c, flush=False):
    _writeseq('\033]10;{}'.format(c), flush)


def get_colorfg():
    return get_term_color([10])


def set_colorbg(c, flush=False):
    _writeseq('\033]11;{}'.format(c), flush)


def get_colorbg():
    return get_term_color([11])


def set_colorcur(c, flush=False):
    _writeseq('\033]12;{}'.format(c), flush)


def get_colorcur():
    return get_term_color([12])


def get_xcolors(file=None, prefix=None):
    proc = None
    if file:
        proc = subprocess.Popen(['cpp', '-P', file], stdout=subprocess.PIPE)
    else:
        proc = subprocess.Popen(['cpp', '-P'], stdin=stdin, stdout=subprocess.PIPE)
    xcolors = []
    xcolor_pattern = re.compile(re.escape(prefix) +
            '(color(\d+)|(foreground)|(background)|(cursorColor))\s*:(.*)$')
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.decode().strip()
        match = xcolor_pattern.match(line)
        if not match:
            continue
        name, p, fg, bg, cur, value = match.groups()
        value = value.strip()
        xcolors.append((name, value, p, fg, bg, cur))
    if proc.wait() != 0:
        raise RuntimeError('Preprocessing failed')
    return xcolors


def set_from_xcolors(file=None, prefix=None):
    xcolors = get_xcolors(file, prefix)
    for c in xcolors:
        name, value, p, fg, bg, cur = c
        if fg:
            set_colorfg(value)
        elif bg:
            set_colorbg(value)
        elif cur:
            set_colorcur(value)
        else:
            set_colorp(p, value)
    return xcolors


def get_term_color(ansi, timeout=1000, retries=5):
    global _poll
    if not _poll:
        _poll = select.poll()
        _poll.register(stdin.fileno(), select.POLLIN)

    while _poll.poll(0):
        stdin.read()

    query = '\033]' + ';'.join([str(a) for a in ansi]) + ';?' + '\007'
    os.write(0, _seqfmt.format(query).encode())

    regex = re.compile(
        '\033\\](\d+;)+rgba?:(([0-9a-f]+)/)?([0-9a-f]+)/([0-9a-f]+)/([0-9a-f]+)\007',
        re.IGNORECASE
    )
    match = None
    output = ''
    while not match:
        if retries < 1 or not _poll.poll(timeout):
            return None
        retries -= 1
        output += stdin.read()
        match = regex.search(output)
    return '#' + ''.join(match.group(i)[:2] for i in [4, 5, 6])


@contextmanager
def get_term_colors():
    if not stdin.isatty():
        raise RuntimeError('<stdin> is not connected to a terminal')

    tc_save = None
    try:
        tc_save = termios.tcgetattr(stdin.fileno())
        tc = termios.tcgetattr(stdin.fileno())
        tc[3] &= ~termios.ECHO
        tc[3] &= ~termios.ICANON
        tc[6][termios.VMIN] = 0
        tc[6][termios.VTIME] = 0
        termios.tcsetattr(stdin.fileno(), termios.TCSANOW, tc)

        yield
    finally:
        if tc_save:
            termios.tcsetattr(
                stdin.fileno(),
                termios.TCSANOW,
                tc_save
            )


if __name__ == '__main__':
    import argparse
    import textwrap

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Get/Set terminal ANSI colors.
            Color can be given as name or RGB specification (e.g., #rrggbb).
            """
        )
    )
    subparsers = parser.add_subparsers(dest='mode')
    p_parser = subparsers.add_parser(
        'p',
        help='get/set palette color',
        description='Get/Set palette color.'
    )
    f_parser = subparsers.add_parser(
        'f',
        help='get/set foreground color',
        description='Get/Set foreground color.'
    )
    b_parser = subparsers.add_parser(
        'b',
        help='get/set background color',
        description='Get/Set background color.'
    )
    c_parser = subparsers.add_parser(
        'c',
        help='get/set cursor color',
        description='Get/Set cursor color.'
    )
    x_parser = subparsers.add_parser(
        'x',
        help='get/set as/from X resources',
        description='Get/Set colors as/from X resources.'
    )

    p_parser.add_argument('index', help='palette color index')
    p_parser.add_argument('color', nargs='?', help='palette color')
    f_parser.add_argument('color', nargs='?', help='foreground color')
    b_parser.add_argument('color', nargs='?', help='background color')
    c_parser.add_argument('color', nargs='?', help='cursor color')
    x_parser.add_argument('-p', '--print', action='store_true',
                          help="don't apply, print-out only")
    x_parser.add_argument('--prefix', default='*',
                          help='X resources prefix (default: *)')
    x_parser.add_argument('file', nargs='?',
                          help="X resources source file; '-' for stdin")
    args = parser.parse_args()

    try:
        if args.mode == 'p':
            if args.color:
                set_colorp(args.index, args.color)
            else:
                output = []
                with get_term_colors():
                    output.append(get_colorp(args.index))
                print('\n'.join(output))
        elif args.mode == 'f':
            if args.color:
                set_colorfg(args.color)
            else:
                output = []
                with get_term_colors():
                    output.append(get_colorfg())
                print('\n'.join(output))
        elif args.mode == 'b':
            if args.color:
                set_colorbg(args.color)
            else:
                output = []
                with get_term_colors():
                    output.append(get_colorbg())
                print('\n'.join(output))
        elif args.mode == 'c':
            if args.color:
                set_colorcur(args.color)
            else:
                output = []
                with get_term_colors():
                    output.append(get_colorcur())
                print('\n'.join(output))
        elif args.mode == 'x':
            if args.file:
                if args.print:
                    for c in get_xcolors(args.file, args.prefix):
                        print(c[0], c[1])
                else:
                    set_from_xcolors(args.file, args.prefix)
            else:
                output = []
                with get_term_colors():
                    output.append('{}foreground: {}'.format(args.prefix, get_colorfg()))
                    output.append('{}background: {}'.format(args.prefix, get_colorbg()))
                    output.append('{}cursorColor: {}'.format(args.prefix, get_colorcur()))
                    for n in range(0, 16):
                        output.append('{}color{}: {}'.format(args.prefix, n, get_colorp(n)))
                print('\n'.join(output))
        else:
            parser.print_usage()
            exit(2)
    except KeyboardInterrupt:
        signal(SIGINT, SIG_DFL)
        os.kill(os.getpid(), SIG_DFL)
    except RuntimeError as e:
        print('{}: error: {}'.format(parser.prog, e), file=stderr)
        exit(1)
