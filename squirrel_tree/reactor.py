"""Reactor: the object containing callbacks for trie."""
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
