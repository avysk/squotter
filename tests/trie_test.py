"""
Tests for trie implementation
"""

import squirrel_tree.trie


def trie_creation_smoke_test():
    """
    Trie smoke test
    """
    trie = squirrel_tree.trie.Trie()
    assert trie.chain == ['']
    trie['foo'] = 'bar'
    assert trie['foo'] == 'bar'
