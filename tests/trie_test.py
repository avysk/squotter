"""Tests for trie implementation."""

from nose import with_setup
from nose.tools import assert_raises, eq_
from mock import call, Mock

import squirrel_tree.trie
from squirrel_tree.reactor import Reactor


class Test(object):

    """Tests for squirrel_tree.trie.Trie."""

    def __init__(self):
        """Test initialisation."""
        self._reactor = None
        self._trie = None

    def setup(self):
        """Create a mock reactor and Trie which uses it."""
        self._reactor = Mock(Reactor)
        self._trie = squirrel_tree.trie.Trie(reactor=self._reactor)
        self._reactor.create_callback.assert_called_once_with([''])
        self._reactor.insert_callback.assert_not_called()
        self._reactor.delete_callback.assert_not_called()
        self._reactor.move_callback.assert_not_called()
        self._reactor.reset_mock()

    def teardown(self):
        """Assert that all reactor calls were checked in test."""
        eq_(self._reactor.method_calls, [], msg="Unchecked reactor calls left")
        self._trie = None
        self._reactor = None

    def _check_reactor(self, *expected):
        """
        Assert that the reactor was called with expected chain of actions.

        :param expected: list of pairs [action, args]
               action is one of 'insert', 'create', 'delete' or 'move'
               args is an iterable of expected arguments for the corresponding
                    reactor callback.
        """
        to_call = {'insert': call.insert_callback,
                   'create': call.create_callback,
                   'delete': call.delete_callback,
                   'move': call.move_callback}
        chain = [to_call[action](*action_args)
                 for action, action_args in expected]
        actual = self._reactor.method_calls
        eq_(actual, chain)
        self._reactor.reset_mock()

    @with_setup(setup, teardown)
    def trie_incorrect_creation_test(self):
        """Test non-root trie with no suffix."""
        with assert_raises(ValueError) as context:
            bad_trie = squirrel_tree.trie.Trie(parent=self._trie)
            assert not bad_trie  # unreachable
        eq_(context.exception.message, 'Only root trie may have empty suffix.')
        with assert_raises(ValueError) as context:
            bad_trie = squirrel_tree.trie.Trie(parent=self._trie, suffix='')
            assert not bad_trie  # unreachable
        eq_(context.exception.message, 'Only root trie may have empty suffix.')

    @with_setup(setup, teardown)
    def trie_creation_smoke_test(self):
        """Trie smoke test."""
        trie = self._trie
        eq_(trie.chain, [''])
        assert trie.terminal
        trie[''] = 42
        self._check_reactor(['insert', ([''], 42)])
        assert trie.terminal
        eq_(trie[''], 42)
        trie['foo'] = 'bar'
        self._check_reactor(
            ['create', (['', 'foo'],)],
            ['insert', (['', 'foo'], 'bar')]
        )
        assert not trie.terminal
        eq_(trie['foo'], 'bar')

    @with_setup(setup, teardown)
    def trie_no_content_test(self):
        """Test KeyError exception when there's no content."""
        with assert_raises(KeyError) as context:
            trie = self._trie
            content = trie['']
            assert not content  # unreachable
        eq_(context.exception.message, 'No content in requested key.')
        trie['foobar'] = 1
        self._check_reactor(
            # Create trie for 'foobar' and insert value there
            ['create', (['', 'foobar'],)],
            ['insert', (['', 'foobar'], 1)])
        trie['foobaz'] = 2
        self._check_reactor(
            # Create trie for 'fooba'
            ['create', (['', 'fooba'],)],
            # Move 'foobar' to 'fooba'->'r'
            ['move', ([''], 'foobar', ['', 'fooba'], 'r')],
            # Create 'fooba'->'z'
            ['create', (['', 'fooba', 'z'],)],
            # Insert value there
            ['insert', (['', 'fooba', 'z'], 2)]
        )
        with assert_raises(KeyError) as context:
            trie = self._trie
            content = trie['fooba']
            assert not content  # unreachable
        eq_(context.exception.message, 'No content in requested key.')

    @with_setup(setup, teardown)
    def trie_no_key_exception_1_test(self):
        """Test KeyError when there's no key at all."""
        self._trie['foo'] = 1
        self._trie['bar'] = 2
        self._check_reactor(
            # Create trie for 'foo' and insert value
            ['create', (['', 'foo'],)],
            ['insert', (['', 'foo'], 1)],
            # Create trie for 'bar' and insert value
            ['create', (['', 'bar'],)],
            ['insert', (['', 'bar'], 2)]
        )
        with assert_raises(KeyError) as context:
            content = self._trie['quux']
            assert not content  # unreachable
        eq_(context.exception.message, 'No requested key.')

    @with_setup(setup, teardown)
    def trie_no_key_exception_2_test(self):
        """Test KeyError when there's only shorter key."""
        self._trie['foo'] = 1
        self._check_reactor(
            # Create trie for 'foo' and insert value
            ['create', (['', 'foo'],)],
            ['insert', (['', 'foo'], 1)]
        )
        with assert_raises(KeyError) as context:
            content = self._trie['foobar']
            assert not content  # unreachable
        eq_(context.exception.message, 'No requested key.')

    @with_setup(setup, teardown)
    def trie_no_key_exception_3_test(self):
        """Test KeyError when there's only longer key."""
        self._trie['foobar'] = 1
        self._check_reactor(
            # Create trie for 'foobar' and insert value
            ['create', (['', 'foobar'],)],
            ['insert', (['', 'foobar'], 1)]
        )
        with assert_raises(KeyError) as context:
            content = self._trie['foo']
            assert not content  # unreachable
        eq_(context.exception.message, 'No requested key.')

    @with_setup(setup, teardown)
    def trie_add_longer_key_test(self):
        """Test addition of key longer than one in a trie."""
        self._trie['foo'] = 1
        self._trie['foobar'] = 2
        self._check_reactor(
            # Create trie for 'foo' and insert value
            ['create', (['', 'foo'],)],
            ['insert', (['', 'foo'], 1)],
            # Create trie for 'foo'->'bar' and insertr value
            ['create', (['', 'foo', 'bar'],)],
            ['insert', (['', 'foo', 'bar'], 2)]
        )
        eq_(self._trie['foo'], 1)
        eq_(self._trie['foobar'], 2)
        assert not self._trie.terminal
        # Should have keys for '', 'foo' and 'bar'
        eq_(len(self._trie), 3)
        foo_trie = self._trie.get_subtrie('foo')
        assert not foo_trie.terminal
        foobar_trie = foo_trie.get_subtrie('bar')
        assert foobar_trie.terminal
        eq_(self._trie.chain, [''])
        eq_(foo_trie.chain, ['', 'foo'])
        eq_(foobar_trie.chain, ['', 'foo', 'bar'])

    @with_setup(setup, teardown)
    def trie_add_shorter_key_test(self):
        """Test addition of shorter key than one in a trie."""
        # Original trie:
        #
        # '' -> foobar -> foobar_{a, b, c}
        #    -> barbaz
        self._trie[''] = 'root'
        self._trie['foobar'] = 1
        self._trie['barbaz'] = 2
        self._trie['foobar_a'] = 'a'
        self._trie['foobar_b'] = 'b'
        self._trie['foobar_c'] = 'c'
        self._check_reactor(
            # fill '', 'foobar' and 'barbaz'
            ['insert', ([''], 'root')],
            ['create', (['', 'foobar'],)],
            ['insert', (['', 'foobar'], 1)],
            ['create', (['', 'barbaz'],)],
            ['insert', (['', 'barbaz'], 2)],
            # create and fill 'foobar'->'_a'
            ['create', (['', 'foobar', '_a'],)],
            ['insert', (['', 'foobar', '_a'], 'a')],
            # transform 'foobar'->'_a' to 'foobar'->'_'->'a'
            ['create', (['', 'foobar', '_'],)],
            ['move', (['', 'foobar'], '_a', ['', 'foobar', '_'], 'a')],
            # create and fille 'foobar'->'_'->{'b', 'c'}
            ['create', (['', 'foobar', '_', 'b'],)],
            ['insert', (['', 'foobar', '_', 'b'], 'b')],
            ['create', (['', 'foobar', '_', 'c'],)],
            ['insert', (['', 'foobar', '_', 'c'], 'c')]
        )
        # Should have keys for '', 'foobar', '_', 'a', 'b', 'c' and 'barbaz'
        eq_(len(self._trie), 7)
        # Now insert key foo, the result should be
        # '' -> foo -> foobar -> foobar_{a, b, c}
        #    -> barbaz
        self._trie['foo'] = 3
        self._check_reactor(
            # Create 'foo', fill it in and move 'foobar' to 'foo'->'bar'
            ['create', (['', 'foo'],)],
            ['insert', (['', 'foo'], 3)],
            ['move', ([''], 'foobar', ['', 'foo'], 'bar')]
        )
        eq_(len(self._trie), 8)
        eq_(self._trie[''], 'root')
        eq_(self._trie['foobar'], 1)
        eq_(self._trie['barbaz'], 2)
        eq_(self._trie['foobar_a'], 'a')
        eq_(self._trie['foobar_b'], 'b')
        eq_(self._trie['foobar_c'], 'c')
        eq_(self._trie['foo'], 3)
        foo_trie = self._trie.get_subtrie('foo')
        foobar_trie = foo_trie.get_subtrie('bar')
        foobar_1_trie = foobar_trie.get_subtrie('_')
        a_trie = foobar_1_trie.get_subtrie('a')
        b_trie = foobar_1_trie.get_subtrie('b')
        c_trie = foobar_1_trie.get_subtrie('c')
        assert a_trie.terminal
        assert b_trie.terminal
        assert c_trie.terminal
        eq_(foo_trie.chain, ['', 'foo'])
        eq_(foobar_trie.chain, ['', 'foo', 'bar'])
        eq_(foobar_1_trie.chain, ['', 'foo', 'bar', '_'])
        eq_(a_trie.chain, ['', 'foo', 'bar', '_', 'a'])
        eq_(b_trie.chain, ['', 'foo', 'bar', '_', 'b'])
        eq_(c_trie.chain, ['', 'foo', 'bar', '_', 'c'])
