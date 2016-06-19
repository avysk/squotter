"""Reactor: the object containing callbacks for trie."""

import os
import os.path
import re
import shutil

from abc import ABCMeta, abstractmethod


class Reactor(object):

    """Reactor interface."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def remove_callback(self, chain):
        """
        Called when a terminal key is completely removed.

        :param chain: The chain from which the last element is removed
        :return: nothing
        """

    @abstractmethod
    def delete_callback(self, chain, value):
        """
        Called when a value is deleted from trie.

        :param chain: chain to a value
        :param value: value being deleted
        """

    @abstractmethod
    def insert_callback(self, chain, value):
        """
        Called when a value is inserted into a Trie.

        :param chain: list of relative keys under which value is inserted
        :param value: the value being inserted
        """

    @abstractmethod
    def create_callback(self, chain):
        """
        Called when a subtrie for new key is created.

        :param chain: the chain of parent keys, ending with the key of created
        Trie
        """

    @abstractmethod
    def move_callback(self, old_chain, old_key, new_chain, new_key):
        """
        Called when a subtree is moved.

        :param old_chain: the old location of the subtree
        :param old_key: the key of subtree under old location
        :param new_chain: the new location of the subtree
        :param key: the key of subtree under new location
        """


class EmptyReactor(Reactor):

    """Reactor which does nothing."""

    def remove_callback(self, chain):
        """Do nothing."""
        pass

    def insert_callback(self, chain, value):
        """Do nothing."""
        pass

    def create_callback(self, chain):
        """Do nothing."""
        pass

    def move_callback(self, old_chain, old_key, new_chain, new_key):
        """Do nothing."""
        pass

    def delete_callback(self, chain, value):
        """Do nothing."""
        pass


class CompositeReactor(Reactor):

    """Reactor which calls callbacks from the given set of sub-reactors."""

    def __init__(self, reactor_list):
        self._reactors = reactor_list

    def insert_callback(self, chain, value):
        """Call insert_callback of subreactors."""
        for reactor in self._reactors:
            reactor.insert_callback(chain, value)

    def remove_callback(self, chain):
        """Call remove_callback of subreactors."""
        for reactor in self._reactors:
            reactor.remove_callback(chain)

    def delete_callback(self, chain, value):
        """Call delete_callback of subreactors."""
        for reactor in self._reactors:
            reactor.delete_callback(chain, value)

    def move_callback(self, old_chain, old_key, new_chain, new_key):
        """Call move_callback of subreactors."""
        for reactor in self._reactors:
            reactor.move_callback(old_chain, old_key, new_chain, new_key)

    def create_callback(self, chain):
        """Call create_callback of subreactors."""
        for reactor in self._reactors:
            reactor.create_callback(chain)


class FileReactor(Reactor):

    """
    Reactor which keeps filesystem in sync with a trie.

    Values in a trie are supposed to be lists of filenames. The
    corresponding files are kept in a hierarchical directory
    structure, corresponding to the inner structure of the trie. The
    files can be either copied, symlinked or hardlinked to their
    place.
    """

    def __init__(self, root_dir, pool_dir='/',
                 method='copy', ignore_regex=None):
        """
        Create a FileReactor.

        :param root_dir: root directory of hierarchal filesystem
        :param pool_dir: directory from which files are taken
        :param method: the method used to put files in a hierarchical
               filestystem. Can be one of 'copy', 'hardlink' or
               'symlink'.
        :param ignore_regex: regex specifying files not to be removed on
               value change.
        """

        methods = {'copy': shutil.copyfile,
                   'hardlink': getattr(os, 'link', None),
                   'symlink': getattr(os, 'symlink', None)}
        if method not in methods:
            raise ValueError("Acceptable methods are: {}".format(
                methods.keys()))
        self._put = methods[method]
        if not self._put:
            raise ValueError("{} is not supported on this platform.".format(
                method))

        if not os.path.isdir(root_dir):
            raise ValueError("{} is not a directory".format(root_dir))
        if not os.access(root_dir, os.W_OK):
            raise ValueError("{} is not writable".format(root_dir))
        self._root = root_dir

        if not os.path.isdir(pool_dir):
            raise ValueError("{} is not a directory".format(pool_dir))
        self._pool = pool_dir

        self._ignore = ignore_regex and re.compile(ignore_regex)

    def remove_callback(self, chain):
        """
        Remove subdirectory from hierarchical filesystem.

        :param chain: the list of path components to the subdirectory to
               be removed.

        Warning: on Windows files in use may cause problems!
        """
        rem_path = self._to_path(chain)
        assert os.path.isdir(rem_path),\
            "Requested removal of non-existant dir {}".format(rem_path)
        shutil.rmtree(rem_path)

    def delete_callback(self, chain, value):
        """
        Remove value from hierarchical filesystem.

        Warning: on Windows files in use may cause problems!
        """
        del_path = self._to_path(chain)
        for fname in value:
            del_fname = os.path.join(del_path, fname)
            assert os.path.isfile(del_fname),\
                "Requested removal of non-exstant file {}".format(del_fname)
            os.unlink(del_fname)

    def insert_callback(self, chain, value):
        dst_path = self._to_path(chain)
        # First make sure we have all needed files
        needed = set()
        for fname in value:
            dst = os.path.join(dst_path, fname)
            needed.add(os.path.abspath(dst))
            if os.path.exists(dst):
                continue
            src = os.path.join(self._pool, fname)
            self._put(src, dst)
        # Now make sure we remove extra files
        to_remove = [fname for fname in os.listdir(dst_path)
                     # collect everything that is file
                     if os.path.isfile(fname) and
                     # which does not belong
                     os.path.abspath(fname) not in needed and
                     # and not ignored
                     self._not_ignored(fname)]
        for fname in to_remove:
            os.unlink(fname)

    def create_callback(self, chain):
        if chain == ['']:
            # No need to create root
            return
        cr_path = self._to_path(chain)
        assert not os.path.exists(cr_path),\
            "{} already exists".format(cr_path)
        os.mkdir(cr_path)

    def move_callback(self, old_chain, old_key, new_chain, new_key):
        src = os.path.join(self._to_path(old_chain), old_key)
        dst = os.path.join(self._to_path(new_chain), new_key)
        shutil.move(src, dst)

    def _to_path(self, chain):
        return os.path.join(self._root, *chain)

    def _not_ignored(self, fname):
        return not (self._ignore and self._ignore.match(fname))
