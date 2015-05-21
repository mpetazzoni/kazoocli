#!/usr/bin/env python

# Copyright (C) 2015 Maxime Petazzoni <maxime.petazzoni@bulix.org>

from __future__ import print_function

import atexit
import datetime
import hexdump
import inspect
import json
import kazoo.client
import os
import pytz
import readline
import shlex
import time


class Completer(object):
    """A helper class for read-line completion in the client's prompt."""

    def __init__(self, words):
        self.words = sorted(words)
        self.prefix = None

    def complete(self, text, state):
        if text != self.prefix:
            self.matches = [w for w in self.words
                            if w.startswith(text)]
            self.prefix = text

        if state < len(self.matches):
            return self.matches[state]
        return None


class KazooCli(object):
    """KazooCli, an interactive command-line ZooKeeper client.

    KazooCli is a command-line client for ZooKeeper implemented on top of the
    Kazoo library. It provides an interactive command-line prompt to interact
    with a ZooKeeper ensemble, with Unix-like filesystem navigation commands.

    If offers readline-based history, and completion of commands and zNode
    paths and names.
    """

    _DEFAULT_ZOOKEEPER_PORT = 2181

    def __init__(self, server):
        self._path = '/'
        self._zk = None

        # Setup the readline prompt.
        try:
            histfile = os.path.join(os.path.expanduser('~'),
                                    '.kazoocli.history')
            atexit.register(readline.write_history_file, histfile)
            readline.read_history_file(histfile)
            readline.parse_and_bind('tab: complete')
            readline.set_completer(self._completer)
            readline.set_completer_delims(' \t\n')
        except IOError:
            pass

        self._commands = set([c for c in dir(self) if not c.startswith('_')])
        self.connect(server)
        self._serve()

    def _fix_server_uri(self, uri):
        """Ensures that the given server URI contains a port number."""
        details = uri.split(':')
        if not uri or not details or len(details) > 2:
            raise ValueError('Invalid ZooKeeper server URI: {}'.format(uri))

        if len(details) == 1:
            return '{}:{}'.format(uri, KazooCli._DEFAULT_ZOOKEEPER_PORT)

        try:
            int(details[1])
            return uri
        except:
            raise ValueError(('Invalid ZooKeeper server port {}; '
                              'expected port number').format(details[1]))

    def _completer(self, text, state):
        if state == 0:
            buf = readline.get_line_buffer()
            tokens = buf.split()
            if len(tokens) < 2 and not buf.endswith(' '):
                words = ['{} '.format(c) for c in self._commands]
            else:
                self.connect()
                path = os.path.dirname(text)
                words = ['{}'.format(os.path.join(path, c))
                         for c in self._zk.get_children(self._get_path(path))]
            self._completer = Completer(words)

        return self._completer.complete(text, state)

    def help(self, command=None):
        """Get help.

        Usage: help [command]

        When invoked without arguments, displays a list of all available
        commands. When a command is given as an argument, detailed help for
        this command is shown instead."""
        if command and command not in self._commands:
            print('Unknown command {}!'.format(command))
            return

        if command:
            print(inspect.getdoc(getattr(self, command)))
            return

        for command in sorted(self._commands):
            print(command, end='')

            doc = inspect.getdoc(getattr(self, command))
            if not doc:
                print()
                continue

            print(': {}'.format(doc.splitlines()[0]))

    def connect(self, server=None):
        """Connect to the current server, or to a new server."""
        server = self._fix_server_uri(server) if server else self._server
        if self._zk and self._zk.connected and server == self._server:
            # Already connected and not changing server.
            return

        self.disconnect()

        self._server = server
        print('Connecting to {}...'.format(self._server))
        self._zk = kazoo.client.KazooClient(hosts=self._server, timeout=3)
        self._zk.start()
        self.state()

    def disconnect(self):
        """Disconnect from the current server."""
        if self._zk and self._zk.connected:
            self._zk.stop()
            self._zk.close()
            print('Disconnected from {}.'.format(self._server))

    def state(self):
        """Show the current connection state."""
        try:
            version = '.'.join(map(str, self._zk.server_version()))
            state = self._zk.command('ruok')
        except:
            version = 'n/a'

        print('{}; server {} has version {} and reports {}.'
              .format(self._zk.state.title(), self._server, version, state))

    def _fmt_time(self, ts=None):
        ts = (ts / 1000.0) if ts else time.time()
        d = datetime.datetime.utcfromtimestamp(ts)
        return pytz.utc.localize(d).strftime('%c %Z')

    def _get_path(self, path=None):
        path = path or self._path
        if not path.startswith('/'):
            path = os.path.abspath(os.path.join(self._path, path))
        return path

    def _check_path(self, path):
        path = self._get_path(path)
        stat = self._zk.exists(path)
        if not stat:
            raise IOError('{} does not exist!'.format(path))
        return path, stat

    def ls(self, path=None):
        """Lists zNodes under the current zNode."""
        self.lsr(path, max_depth=0)

    def lsr(self, path=None, max_depth=3, indent=''):
        """Recursively display zNodes under the current zNode.

        Usage: lsr [path [max-depth]]
        """
        max_depth = int(max_depth)
        self.connect()
        path, _ = self._check_path(path)
        results = []
        for child in sorted(self._zk.get_children(path)):
            child_path = os.path.join(path, child)
            child_stat = self._zk.exists_async(child_path)
            results.append({'name': child,
                            'path': child_path,
                            'stat': child_stat})

        for child in results:
            c_stat = child['stat'].get()
            print('{}{}'.format(indent, child['name']), end='')
            if c_stat.children_count:
                print('/', end='')
                if max_depth:
                    print()
                    self.lsr(path=child['path'],
                             indent=(indent + '  '),
                             max_depth=(max_depth - 1))
                else:
                    print('...')
            else:
                print()

    def cd(self, path=None):
        """Enter the given zNode."""
        self.connect()
        self._path, _ = self._check_path(path)

    def stat(self, path=None):
        """Display information about a Znode."""
        self.connect()
        _, stat = self._check_path(path)
        print('created : {}'.format(self._fmt_time(stat.ctime)))
        print('modified: {}'.format(self._fmt_time(stat.mtime)))
        print('children: {}'.format(stat.children_count))
        if stat.data_length:
            print('  data    : {} byte{}'
                  .format(stat.data_length,
                          's' if stat.data_length != 1 else ''))

    def get(self, path=None):
        """Display the contents of a zNode."""
        self.connect()
        path, stat = self._check_path(path)
        if not stat.data_length:
            return

        data, _ = self._zk.get(path)
        if data[0] == '{':
            try:
                print(json.dumps(json.loads(data), sort_keys=True))
                return
            except:
                pass

        print(data)

    cat = get

    def hex(self, path=None):
        """Display the contents of a zNode as an hexadecimal dump."""
        self.connect()
        path, stat = self._check_path(path)
        if not stat.data_length:
            return

        data, _ = self._zk.get(path)
        hexdump.hexdump(data)

    def set(self, path, value):
        """Set (or create) a zNode to the given value.

        Usage: set <path> <value>"""
        self.connect()
        path = self._get_path(path)

        if not self._zk.exists(path):
            self._zk.create(path, value)
        else:
            self._zk.set(path, value)

        self._zk.sync(path)
        self.stat(path)

    def mkdir(self, path):
        """Create an empty zNode."""
        self.set(path, '')

    def rm(self, path):
        """Remove a zNode.

        A remove can only be removed if it has no children. Use rmr to
        recursively remove a zNode hierarchy."""
        self.connect()
        path, stat = self._check_path(path)
        self._zk.delete(path)
        print('Removed {} ({} byte{}).'
              .format(path, stat.data_length,
                      's' if stat.data_length != 1 else ''))

    def rmr(self, path):
        """Recursively remove a zNode and all of its children."""
        self.connect()
        path, _ = self._check_path(path)
        self._zk.delete(path, recursive=True)
        print('Removed {} and all its children.'.format(path))

    def exit(self):
        """Exit the program."""
        self._stop = True

    quit = exit

    def _serve(self):
        self._stop = False
        self.connect()
        while not self._stop:
            try:
                command = raw_input('{}> '.format(self._path)).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not command:
                continue

            tokens = shlex.split(command)
            verb = tokens.pop(0)

            if not hasattr(self, verb):
                print('Unknown command {}.'.format(verb))
                continue

            if len(tokens) == 1 and tokens[0] in ['-h', '--help']:
                self.help(verb)
                continue

            try:
                getattr(self, verb)(*tokens)
            except Exception, e:
                print('Error: {}'.format(e))
        self.disconnect()
