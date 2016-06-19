"""Tests for FileReactor."""

import os.path
import shutil
import tempfile

from nose import with_setup

from squirrel_tree.reactor import FileReactor
from squirrel_tree.trie import Trie


class Test(object):

    """Tests for squirrel_tree.reactor.FileReactor."""

    def __init__(self):
        """Test initialisation."""
        self._root = None
        self._pool = None

    def setup(self):
        """Create temp dirs for root and pool."""
        self._root = tempfile.mkdtemp()
        self._pool = tempfile.mkdtemp()
        for fname in ['foo', 'bar', 'baz', 'quux']:
            with open(os.path.join(self._pool, fname), 'w') as faile:
                faile.write("content of {}\n".format(fname))

    def teardown(self):
        """Cleanup root and pool."""
        shutil.rmtree(self._root)
        self._root = None
        shutil.rmtree(self._pool)
        self._pool = None

    @with_setup(setup, teardown)
    def smoke_test(self):
        """Test all basic operations of FileReactor."""
        for method in ['copy', 'hardlink', 'symlink']:
            if method == 'hardlink' and 'link' not in dir(os):
                # cannot test hardlinks
                continue
            if method == 'symlink' and 'symlink' not in dir(os):
                # cannot test symlinks
                continue
            reactor = FileReactor(root_dir=self._root,
                                  pool_dir=self._pool,
                                  method=method)
            trie = Trie(reactor=reactor)
            trie['a'] = ['foo']
            trie['ab'] = ['bar']
            trie['abc'] = ['foo', 'bar', 'quux']
            trie['ad'] = ['baz']
            trie['abc'] = ['bar', 'baz']
            del trie['ad']
