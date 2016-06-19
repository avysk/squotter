"""Tests for reactors."""

from mock import call, Mock
from nose.tools import eq_

from squirrel_tree.reactor import CompositeReactor, Reactor


def composite_reactor_test():
    """Test CompositeReactor."""
    subreactors = [Mock(Reactor), Mock(Reactor), Mock(Reactor)]
    composite = CompositeReactor(subreactors)

    def _check_subreactors(expected):
        for subreactor in subreactors:
            eq_(subreactor.method_calls, [expected])
            subreactor.reset_mock()

    composite.insert_callback('chain1', 'value1')
    _check_subreactors(call.insert_callback('chain1', 'value1'))
    composite.remove_callback('chain2')
    _check_subreactors(call.remove_callback('chain2'))
    composite.delete_callback('chain3', 'value3')
    _check_subreactors(call.delete_callback('chain3', 'value3'))
    composite.move_callback('chain4', 'value4', 'chain5', 'value5')
    _check_subreactors(call.move_callback('chain4', 'value4',
                                          'chain5', 'value5'))
    composite.create_callback('chain6')
    _check_subreactors(call.create_callback('chain6'))
