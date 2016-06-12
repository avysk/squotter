"""
Tests for trie implementation
"""

from nose.tools import raises

import squirrel_tree.trie


def trie_creation_smoke_test():
    """
    Trie smoke test
    """
    trie = squirrel_tree.trie.Trie()
    assert trie.chain == ['']
    assert trie.terminal
    trie[''] = 42
    assert trie.terminal
    assert trie[''] == 42
    trie['foo'] = 'bar'
    assert not trie.terminal
    assert trie['foo'] == 'bar'


@raises(KeyError)
def trie_no_content_1_test():
    """
    Test KeyError exception when there's key but no content; for root
    """
    trie = squirrel_tree.trie.Trie()
    print trie['']


@raises(KeyError)
def trie_no_content_2_test():
    """
    Test KeyError exception when there's key but no content; for created key
    """
    trie = squirrel_tree.trie.Trie()
    trie['foobar'] = 1
    trie['foobaz'] = 2
    print trie['foo']


@raises(KeyError)
def trie_no_key_exception_1_test():
    """
    Test KeyError when there's no key at all.
    """
    trie = squirrel_tree.trie.Trie()
    trie['foo'] = 1
    trie['bar'] = 2
    print trie['quux']


@raises(KeyError)
def trie_no_key_exception_2_test():
    """
    Test KeyError when there's only shorter key.
    """
    trie = squirrel_tree.trie.Trie()
    trie['foo'] = 1
    print trie['foobar']


@raises(KeyError)
def trie_no_key_exception_3_test():
    """
    Test KeyError when there's only longer key.
    """
    trie = squirrel_tree.trie.Trie()
    trie['foobar'] = 1
    print trie['foo']


def trie_add_longer_key_test():
    """
    Test addition of key longer than one in a trie.
    """
    trie = squirrel_tree.trie.Trie()
    trie['foo'] = 1
    trie['foobar'] = 2
    assert trie['foo'] == 1
    assert trie['foobar'] == 2
    assert not trie.terminal
    # Should have keys for '', 'foo' and 'bar'
    assert len(trie) == 3
    foo_trie = trie.get_subtrie('foo')
    assert not foo_trie.terminal
    foobar_trie = foo_trie.get_subtrie('bar')
    assert foobar_trie.terminal
    assert trie.chain == ['']
    assert foo_trie.chain == ['', 'foo']
    assert foobar_trie.chain == ['', 'foo', 'bar']


def trie_add_shorter_key_test():
    """
    Test addition of shorter key than one in a trie.
    """
    trie = squirrel_tree.trie.Trie()
    # Original trie:
    #
    # '' -> foobar -> foobar_{a, b, c}
    #    -> barbaz
    trie[''] = 'root'
    trie['foobar'] = 1
    trie['barbaz'] = 2
    trie['foobar_a'] = 'a'
    trie['foobar_b'] = 'b'
    trie['foobar_c'] = 'c'
    # Should have keys for '', 'foobar', '_', 'a', 'b', 'c' and 'barbaz'
    assert len(trie) == 7
    # Now insert key foo, the result should be
    # '' -> foo -> foobar -> foobar_{a, b, c}
    #    -> barbaz
    trie['foo'] = 3
    assert len(trie) == 8
    assert trie[''] == 'root'
    assert trie['foobar'] == 1
    assert trie['barbaz'] == 2
    assert trie['foobar_a'] == 'a'
    assert trie['foobar_b'] == 'b'
    assert trie['foobar_c'] == 'c'
    assert trie['foo'] == 3
    foo_trie = trie.get_subtrie('foo')
    foobar_trie = foo_trie.get_subtrie('bar')
    foobar_1_trie = foobar_trie.get_subtrie('_')
    a_trie = foobar_1_trie.get_subtrie('a')
    b_trie = foobar_1_trie.get_subtrie('b')
    c_trie = foobar_1_trie.get_subtrie('c')
    assert a_trie.terminal
    assert b_trie.terminal
    assert c_trie.terminal
    assert foo_trie.chain == ['', 'foo']
    assert foobar_trie.chain == ['', 'foo', 'bar']
    assert foobar_1_trie.chain == ['', 'foo', 'bar', '_']
    assert a_trie.chain == ['', 'foo', 'bar', '_', 'a']
    assert b_trie.chain == ['', 'foo', 'bar', '_', 'b']
    assert c_trie.chain == ['', 'foo', 'bar', '_', 'c']
