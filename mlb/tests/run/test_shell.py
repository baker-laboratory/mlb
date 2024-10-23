import ipd
import mlb
from assertpy import assert_that as ASSERT

def main():
    test_bash()

def test_bash():
    ASSERT(('foo\n', '', 0)).is_equal_to(ipd.dev.bash('echo foo'))
    ASSERT(('foo\n', '', 0)).is_equal_to(ipd.dev.bash('echo foobar | cut -b 1-3'))
    ASSERT(('foo\nbar\n', '', 0)).is_equal_to(ipd.dev.bash('echo foo; echo bar'))
    ASSERT(('foo\nbar\n', '', 0)).is_equal_to(ipd.dev.bash('echo foo && echo bar'))
    ASSERT((
        '',
        '/bin/sh: line 1: wXyZ: command not found\n',
        127,
    )).is_equal_to(ipd.dev.bash('wXyZ && echo bar'))
    ASSERT((
        'bar\n',
        '/bin/sh: line 1: wXyZ: command not found\n',
        0,
    )).is_equal_to(ipd.dev.bash('wXyZ; echo bar'))

if __name__ == '__main__':
    main()
