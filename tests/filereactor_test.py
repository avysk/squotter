"""Tests for FileReactor."""

import os
import os.path
import shutil
import sys
import tempfile

from mock import patch
from nose.tools import assert_equal, assert_raises_regexp,\
    assert_false, assert_true

from squirrel_tree.reactor import FileReactor
from squirrel_tree.trie import Trie


class Test(object):

    """Tests for squirrel_tree.reactor.FileReactor."""

    def __init__(self):
        """Test initialisation."""
        self._root = None
        self._pool = None
        self._contents = {}

        # We are not supposed to all readlink if it's not available
        # getattr to make pylint on Windows happy
        def _no_readlink(_):
            raise AssertionError("readlink not available")
        self._readlink = getattr(os, 'readlink', _no_readlink)

    def setup(self):
        """Create temp dirs for root and pool."""
        self._root = tempfile.mkdtemp()
        self._pool = tempfile.mkdtemp()
        for fname in ['foo', 'bar', 'baz', 'quux']:
            with open(os.path.join(self._pool, fname), 'w') as faile:
                self._contents[fname] = "content of {}\n".format(fname)
                faile.write(self._contents[fname])

    def teardown(self):
        """Cleanup root and pool."""
        shutil.rmtree(self._root)
        self._root = None
        shutil.rmtree(self._pool)
        self._pool = None

    def copy_smoke_test(self):
        """Test all basic operations of FileReactor using copy method."""
        self._smoke('copy')

    def hardlink_smoke_test(self):
        """Test all basic operations of FileReactor using hardlink method."""
        self._smoke('hardlink')

    def symlink_smoke_test(self):
        """Test all basic operations of FileReactor using symlink method."""
        self._smoke('symlink')

    def _smoke(self, method):
        if method == 'hardlink' and 'link' not in dir(os):
            # cannot test hardlinks
            assert True
            return
        if method == 'symlink' and 'symlink' not in dir(os):
            # cannot test symlinks
            assert True
            return
        reactor = FileReactor(root_dir=self._root,
                              pool_dir=self._pool,
                              method=method)
        trie = Trie(reactor=reactor)
        # Should be empty initially
        self._assert_fs(method, {})
        trie['a'] = ['foo']
        self._assert_fs(method, {'a': {'foo': None}})
        trie['ab'] = ['bar']
        self._assert_fs(method, {'a': {'foo': None,
                                       'b': {'bar': None}}})
        trie['abc'] = ['foo', 'bar', 'quux']
        self._assert_fs(method, {'a': {'foo': None,
                                       'b': {'bar': None,
                                             'c': {'foo': None,
                                                   'bar': None,
                                                   'quux': None}}}})
        trie['ad'] = ['baz']
        self._assert_fs(method, {'a': {'foo': None,
                                       'b': {'bar': None,
                                             'c': {'foo': None,
                                                   'bar': None,
                                                   'quux': None}},
                                       'd': {'baz': None}}})
        trie['abc'] = ['bar', 'baz']
        self._assert_fs(method, {'a': {'foo': None,
                                       'b': {'bar': None,
                                             'c': {'bar': None, 'baz': None}},
                                       'd': {'baz': None}}})
        del trie['a']
        self._assert_fs(method, {'a': {'b': {'bar': None,
                                             'c': {'bar': None, 'baz': None}},
                                       'd': {'baz': None}}})
        del trie['ad']
        self._assert_fs(method, {'ab': {'bar': None,
                                        'c': {'bar': None, 'baz': None}}})

    def _assert_fs(self, method, struct):
        self._assert_fs_rec(method, self._root, struct)

    def _assert_fs_rec(self, method, root, struct):
        in_root = os.listdir(root)
        files_in_root = {thing for thing in in_root
                         if os.path.isfile(os.path.join(root, thing))}
        expected_files_in_root = {thing for thing in struct
                                  if struct[thing] is None}
        assert_equal(files_in_root, expected_files_in_root)
        dirs_in_root = {thing for thing in in_root
                        if os.path.isdir(os.path.join(root, thing))}
        expected_dirs_in_root = {thing for thing in struct
                                 if struct[thing] is not None}
        assert_equal(dirs_in_root, expected_dirs_in_root)

        for fname in files_in_root:
            self._assert_file(method, root, fname)

        for dname in dirs_in_root:
            subpath = os.path.join(root, dname)
            substruct = struct[dname]
            self._assert_fs_rec(method, subpath, substruct)

    def _assert_file(self, method, path, fname):
        faile = os.path.join(path, fname)
        source = os.path.join(self._pool, fname)

        if method == 'symlink':
            assert_true(os.path.islink(faile), "Not a symlink")
            assert_true(os.path.isfile(faile), "Not a file")
            target = self._readlink(faile)
            assert_equal(target, source, "Wrong symlink target")
            return

        assert_false(os.path.islink(faile), "Is a symlink")
        assert_true(os.path.isfile(faile), "Not a file")
        with open(faile, 'r') as faile_r:
            content = faile_r.read()
        assert_equal(content, self._contents[fname])
        # Let's test if we got a hardlink or not
        # We do this by writing something to the file inside self._root
        # and checking it was reflected in the source in self._pool
        placeholder = "Testing hardlink"
        with open(faile, 'w') as faile_w:
            faile_w.write(placeholder)
        with open(source, 'r') as source_r:
            content = source_r.read()
        if method == 'hardlink':
            # The original file had to change
            assert_equal(content, placeholder, "Not a hardlink")
            # Reset the content of the original file back
            with open(source, 'w') as source_w:
                source_w.write(self._contents[fname])
        else:
            # This was not a hardlink, the original file had to stay the same
            assert_equal(content, self._contents[fname])
        # Reset the content of the file in hierarchical filesystem
        with open(faile, 'w') as faile_w:
            faile_w.write(self._contents[fname])

    def unknown_method_test(self):
        """Test that FileReactor raises exception for unknown method."""
        # pylint: disable=no-self-use
        def _fail():
            return FileReactor('', method='gnusto')
        assert_raises_regexp(ValueError,
                             r"^Acceptable methods are:.*$",
                             _fail)

    def unsupported_method_test(self):
        """
        Test that FileReactor raises exception for unsupported method.

        Windows-only.
        """
        # pylint: disable=no-self-use

        if sys.platform != 'win32':
            assert True
            return

        assert_raises_regexp(ValueError,
                             r"^hardlink is not supported on this platform.",
                             lambda: FileReactor('', method='hardlink'))
        assert_raises_regexp(ValueError,
                             r"^symlink is not supported on this platform.",
                             lambda: FileReactor('', method='symlink'))

    def improper_root_test(self):
        """Test that FileReactor raises exception for bad root directory."""
        def _no_root():
            return FileReactor('quux', method='copy')
        assert_raises_regexp(ValueError,
                             r"^.*quux is not a directory$",
                             _no_root)

        def _no_writable_root():
            root = os.path.join(self._root, 'foobar')
            os.mkdir(root, 0o500)  # r-x------
            try:
                if sys.platform == 'win32':
                    # I don't know how to create read-only dir on Windows
                    # mode in mkdir is ignored, and chmod doesn't help
                    with patch('os.access', return_value=False):
                        return FileReactor(root, method='copy')
                else:
                    return FileReactor(root, method='copy')
            except:
                os.chmod(root, 0o700)  # rwx------
                raise
        assert_raises_regexp(ValueError,
                             r"^.*foobar is not writable$",
                             _no_writable_root)

        def _no_pool():
            pool = os.path.join(self._pool, 'barbaz')
            open(pool, 'w').close()
            return FileReactor(self._root, pool_dir=pool, method='copy')
        assert_raises_regexp(ValueError,
                             r"^.*barbaz is not a directory",
                             _no_pool)
