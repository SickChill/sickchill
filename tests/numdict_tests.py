# coding=utf-8

"""
Unit Tests for sickbeard/numdict.py
"""

import sys
import os.path
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard.numdict import NumDict

PY3 = sys.version_info >= (3, )

if PY3:
    from collections import UserDict
else:
    from UserDict import UserDict


class NumDictTest(unittest.TestCase):
    """
    Test the NumDict class
    """
    def test_constructors(self):
        """
        Test NumDict constructors
        """
        # dicts for testing
        d0 = {}  # Empty dictionary
        d1 = {1: 'Elephant'}  # Single numeric key
        d2 = {1: 'Elephant', 2: 'Mouse'}  # Multiple numeric keys
        d3 = {'3': 'Aardvark'}  # Numeric string key
        d4 = {'3': 'Aardvark', '4': 'Ant'}  # Multiple numeric string keys
        d5 = {5: 'Cat', '6': 'Dog'}  # Mixed numeric and numeric string keys
        d6 = {1: None, '2': None}  # None as values
        d7 = {None: 'Empty'}  # None as key

        # Construct NumDicts from dicts
        n = NumDict()
        n0 = NumDict(d0)
        n1 = NumDict(d1)
        n2 = NumDict(d2)
        n3 = NumDict(d3)
        n4 = NumDict(d4)
        n5 = NumDict(d5)
        n6 = NumDict(d6)
        n7 = NumDict(d7)

        # Most NumDicts from dicts should compare equal...
        self.assertEqual(n, {})
        self.assertEqual(n0, d0)
        self.assertEqual(n1, d1)
        self.assertEqual(n2, d2)

        # ...however, numeric keys are not equal to numeric string keys...
        self.assertNotEqual(n3, d3)
        self.assertNotEqual(n4, d4)
        self.assertNotEqual(n5, d5)
        self.assertNotEqual(n6, d6)

        # ...but None keys work just fine
        self.assertEqual(n7, d7)

        # Construct dicts from NumDicts
        dn = dict(n)
        dn1 = dict(n1)
        dn2 = dict(n2)
        dn3 = dict(n3)
        dn4 = dict(n4)
        dn5 = dict(n5)
        dn6 = dict(n6)
        dn7 = dict(n7)

        # All dicts from NumDicts should compare equal
        self.assertEqual(n, dn)
        self.assertEqual(n1, dn1)
        self.assertEqual(n2, dn2)
        self.assertEqual(n3, dn3)
        self.assertEqual(n4, dn4)
        self.assertEqual(n5, dn5)
        self.assertEqual(n6, dn6)
        self.assertEqual(n7, dn7)

        # Construct NumDicts from NumDicts
        nn = NumDict(n)
        nn0 = NumDict(n0)
        nn1 = NumDict(n1)
        nn2 = NumDict(n2)
        nn3 = NumDict(n3)
        nn4 = NumDict(n4)
        nn5 = NumDict(n5)
        nn6 = NumDict(n6)
        nn7 = NumDict(n7)

        # All NumDicts from NumDicts should compare equal
        self.assertEqual(n, nn)
        self.assertEqual(n0, nn0)
        self.assertEqual(n1, nn1)
        self.assertEqual(n2, nn2)
        self.assertEqual(n3, nn3)
        self.assertEqual(n4, nn4)
        self.assertEqual(n5, nn5)
        self.assertEqual(n6, nn6)
        self.assertEqual(n7, nn7)

        # keyword arg constructor should fail
        with self.assertRaises(TypeError):
            NumDict(one=1, two=2)  # Raise TypeError since we can't have numeric keywords

        # item sequence constructors work fine...
        self.assertEqual(NumDict([(1, 'Elephant'), (2, 'Mouse')]), dn2)
        self.assertEqual(NumDict(dict=[(1, 'Elephant'), (2, 'Mouse')]), dn2)
        self.assertEqual(NumDict([(1, 'Elephant'), ('2', 'Mouse')]), dn2)
        self.assertEqual(NumDict(dict=[('1', 'Elephant'), (2, 'Mouse')]), dn2)

        # ...unless you have a non-numeric key
        with self.assertRaises(TypeError):
            NumDict([('Rat', 11), ('Snake', 12)])
        with self.assertRaises(TypeError):
            NumDict(dict=[('Rat', 11), ('Snake', 12)])

        # combining item sequence constructors with keyword args does not work
        with self.assertRaises(TypeError):  # Raise TypeError since we can't have numeric keywords
            NumDict([(1, 'one'), (2, 'two')], two=3, five=4)

        # alternate constructors
        d8 = {1: 'Echo', 2: 'Echo'}

        self.assertEqual(NumDict.fromkeys('1 2'.split()), dn6)
        self.assertEqual(NumDict().fromkeys('1 2'.split()), dn6)
        self.assertEqual(NumDict.fromkeys('1 2'.split(), 'Echo'), d8)
        self.assertEqual(NumDict().fromkeys('1 2'.split(), 'Echo'), d8)
        self.assertTrue(n1.fromkeys('1 2'.split()) is not n1)
        self.assertIsInstance(n1.fromkeys('1 2'.split()), NumDict)
        self.assertIsInstance(n2.fromkeys('1 2'.split()), NumDict)
        self.assertIsInstance(n3.fromkeys('1 2'.split()), NumDict)
        self.assertIsInstance(n4.fromkeys('1 2'.split()), NumDict)

    def test_repr(self):
        # dicts for testing
        d0 = {}  # Empty dictionary
        d1 = {1: 'Elephant'}  # Single numeric key
        d2 = {1: 'Elephant', 2: 'Mouse'}  # Multiple numeric keys
        d3 = {'3': 'Aardvark'}  # Numeric string key
        d4 = {'3': 'Aardvark', '4': 'Ant'}  # Multiple numeric string keys
        d5 = {5: 'Cat', '6': 'Dog'}  # Mixed numeric and numeric string keys
        d6 = {1: None, '2': None}  # None as values
        d7 = {None: 'Empty'}  # None as key

        #  Construct NumDicts from dicts
        n = NumDict()
        n0 = NumDict(d0)
        n1 = NumDict(d1)
        n2 = NumDict(d2)
        n3 = NumDict(d3)
        n4 = NumDict(d4)
        n5 = NumDict(d5)
        n6 = NumDict(d6)
        n7 = NumDict(d7)

        reps = (
            "{}",
            "{1: 'Elephant'}",
            "{1: 'Elephant', 2: 'Mouse'}",
            "'3': 'Aardvark'",
            "{'3': 'Aardvark', '4': 'Ant'}",
            "{5: 'Cat', '6': 'Dog'}",
            "{1: None, '2': None}",
            "{None: 'Empty'}",
        )

        # Most representations of NumDicts should compare equal to dicts...
        self.assertEqual(str(n), str({}))
        self.assertEqual(repr(n), repr({}))
        self.assertIn(repr(n), reps)

        self.assertEqual(str(n0), str(d0))
        self.assertEqual(repr(n0), repr(d0))
        self.assertIn(repr(n0), reps)

        self.assertEqual(str(n1), str(d1))
        self.assertEqual(repr(n1), repr(d1))
        self.assertIn(repr(n1), reps)

        self.assertEqual(str(n2), str(d2))
        self.assertEqual(repr(n2), repr(d2))
        self.assertIn(repr(n2), reps)

        # ...however, numeric keys are not equal to numeric string keys...
        # ...so the string representations for those are different...
        self.assertNotEqual(str(n3), str(d3))
        self.assertNotEqual(repr(n3), repr(d3))
        self.assertNotIn(repr(n3), reps)

        self.assertNotEqual(str(n4), str(d4))
        self.assertNotEqual(repr(n4), repr(d4))
        self.assertNotIn(repr(n4), reps)

        self.assertNotEqual(str(n5), str(d5))
        self.assertNotEqual(repr(n5), repr(d5))
        self.assertNotIn(repr(n5), reps)

        self.assertNotEqual(str(n6), str(d6))
        self.assertNotEqual(repr(n6), repr(d6))
        self.assertNotIn(repr(n6), reps)

        # ...but None keys work just fine
        self.assertEqual(str(n7), str(d7))
        self.assertEqual(repr(n7), repr(d7))
        self.assertIn(repr(n7), reps)

    def test_rich_comparison_and_len(self):
        # dicts for testing
        d0 = {}  # Empty dictionary
        d1 = {1: 'Elephant'}  # Single numeric key
        d2 = {1: 'Elephant', 2: 'Mouse'}  # Multiple numeric keys

        # Construct NumDicts from dicts
        n = NumDict()
        n0 = NumDict(d0)
        n1 = NumDict(d1)
        n2 = NumDict(d2)

        # Construct NumDicts from NumDicts
        nn = NumDict(n)
        nn0 = NumDict(n0)
        nn1 = NumDict(n1)
        nn2 = NumDict(n2)

        all_dicts = [d0, d1, d2, n, n0, n1, n2, nn, nn0, nn1, nn2]
        for a in all_dicts:
            for b in all_dicts:
                self.assertEqual(a == b, len(a) == len(b))

    def test_dict_access_and_modification(self):
        # dicts for testing
        d0 = {}  # Empty dictionary
        d1 = {1: 'Elephant'}  # Single numeric key
        d2 = {1: 'Elephant', 2: 'Mouse'}  # Multiple numeric keys

        #  Construct NumDicts from dicts
        n0 = NumDict()
        n1 = NumDict(d1)
        n2 = NumDict(d2)

        # test __getitem__
        self.assertEqual(n2[1], 'Elephant')
        with self.assertRaises(KeyError):
            n1['Mouse']  # key is not numeric
        with self.assertRaises(KeyError):
            n1.__getitem__('Mouse')  # key is not numeric
        with self.assertRaises(KeyError):
            n1[None]  # key does not exist
        with self.assertRaises(KeyError):
            n1.__getitem__(None)  # key does not exist

        # Test __setitem__
        n3 = NumDict(n2)
        self.assertEqual(n2, n3)

        n3[2] = 'Frog'
        self.assertNotEqual(n2, n3)

        # Check None keys and numeric key conversion
        n3['3'] = 'Armadillo'
        n3[None] = 'Cockroach'

        # Check long ints
        n3[12390809518259081208909880312] = 'Squid'
        n3['12390809518259081208909880312'] = 'Octopus'
        self.assertEqual(n3[12390809518259081208909880312], 'Octopus')

        with self.assertRaises(TypeError):
            n3.__setitem__('Gorilla', 1)  # key is not numeric
        with self.assertRaises(TypeError):
            n3['Chimpanzee'] = 1  # key is not numeric
        with self.assertRaises(TypeError):
            n3[(4, 1)] = 1  # key is not numeric
        with self.assertRaises(TypeError):
            n3[[1, 3, 4]] = 1  # key is not numeric and is not hashable

        # Test __delitem__
        del n3[3]
        del n3[None]
        with self.assertRaises(KeyError):
            del n3[3]  # already deleted
        with self.assertRaises(KeyError):
            n3.__delitem__(3)  # already deleted
        with self.assertRaises(KeyError):
            del n3['Mouse']  # key would not exist, since it is not numeric

        # Test clear
        n3.clear()
        self.assertEqual(n3, {})

        # Test copy()
        n2a = d2.copy()
        self.assertEqual(n2, n2a)
        n2b = n2.copy()
        self.assertEqual(n2b, n2)
        n2c = UserDict({1: 'Elephant', 2: 'Mouse'})
        n2d = n2c.copy()  # making a copy of a UserDict is special cased
        self.assertEqual(n2c, n2d)

        class MyNumDict(NumDict):
            """
            subclass Numdict for testing
            """
            def display(self):
                """
                add a method to subclass to differentiate from superclass
                """
                print('MyNumDict:', self)

        m2 = MyNumDict(n2)
        m2a = m2.copy()
        self.assertEqual(m2a, m2)

        m2[1] = 'Frog'
        self.assertNotEqual(m2a, m2)

        # Test keys, items, values
        self.assertEqual(sorted(n2.keys()), sorted(d2.keys()))
        self.assertEqual(sorted(n2.items()), sorted(d2.items()))
        self.assertEqual(sorted(n2.values()), sorted(d2.values()))

        # Test "in".
        for i in n2:
            self.assertIn(i, n2)
            self.assertEqual(i in n1, i in d1)
            self.assertEqual(i in n0, i in d0)

        self.assertFalse(None in n2)
        self.assertEqual(None in n2, None in d2)

        d2[None] = 'Cow'
        n2[None] = d2[None]
        self.assertTrue(None in n2)
        self.assertEqual(None in n2, None in d2)

        self.assertEqual(n2.has_key(None), None in d2)
        if not PY3:
            self.assertEqual(n2.has_key(None), d2.has_key(None))
        self.assertFalse('Penguin' in n2)

        # Test update
        t = NumDict()
        t.update(d2)
        self.assertEqual(t, n2)

        # Test get
        for i in n2:
            self.assertEqual(n2.get(i), n2[i])
            self.assertEqual(n1.get(i), d1.get(i))
            self.assertEqual(n0.get(i), d0.get(i))

        for i in ['purple', None, 12312301924091284, 23]:
            self.assertEqual(n2.get(i), d2.get(i), i)

        with self.assertRaises(AssertionError):
            i = '1'
            self.assertEqual(n2.get(i), d2.get(i), i)  # d2 expects string key which does not exist

        # Test "in" iteration.
        n2b = n2
        for i in range(20):
            n2[i] = str(i)
            n2b[str(i)] = str(i)
        self.assertEqual(n2, n2b)

        ikeys = []
        for k in n2:
            ikeys.append(k)
        self.assertEqual(set(ikeys), set(n2.keys()))

        # Test setdefault
        x = 1
        t = NumDict()
        self.assertEqual(t.setdefault(x, 42), 42)
        self.assertEqual(t.setdefault(x, '42'), 42)
        self.assertNotEqual(t.setdefault(x, 42), '42')
        self.assertNotEqual(t.setdefault(x, '42'), '42')
        self.assertIn(x, t)

        self.assertEqual(t.setdefault(x, 23), 42)
        self.assertEqual(t.setdefault(x, '23'), 42)
        self.assertNotEqual(t.setdefault(x, 23), '42')
        self.assertNotEqual(t.setdefault(x, '23'), '42')
        self.assertIn(x, t)

        # Test pop
        x = 1
        t = NumDict({x: 42})
        self.assertEqual(t.pop(x), 42)
        self.assertRaises(KeyError, t.pop, x)
        self.assertEqual(t.pop(x, 1), 1)
        t[x] = 42
        self.assertEqual(t.pop(x, 1), 42)

        # Test popitem
        x = 1
        t = NumDict({x: 42})
        self.assertEqual(t.popitem(), (x, 42))
        self.assertRaises(KeyError, t.popitem)

    def test_missing(self):
        # Make sure NumDict doesn't have a __missing__ method
        self.assertEqual(hasattr(NumDict, "__missing__"), False)

        class D(NumDict):
            """
            subclass defines __missing__ method returning a value
            """
            def __missing__(self, key):
                return 42

        d = D({1: 2, 3: 4})
        self.assertEqual(d[1], 2)
        self.assertEqual(d[3], 4)
        self.assertNotIn(2, d)
        self.assertNotIn(2, d.keys())
        self.assertEqual(d[2], 42)

        class E(NumDict):
            """
            subclass defines __missing__ method raising RuntimeError
            """
            def __missing__(self, key):
                raise RuntimeError(key)

        e = E()
        try:
            e[42]
        except RuntimeError as err:
            self.assertEqual(err.args, (42,))
        else:
            self.fail("e[42] didn't raise RuntimeError")

        class F(NumDict):
            """
            subclass sets __missing__ instance variable (no effect)
            """
            def __init__(self):
                # An instance variable __missing__ should have no effect
                self.__missing__ = lambda key: None
                NumDict.__init__(self)
        f = F()
        try:
            f[42]
        except KeyError as err:
            self.assertEqual(err.args, (42,))
        else:
            self.fail("f[42] didn't raise KeyError")

        class G(NumDict):
            """
            subclass doesn't define __missing__ at a all
            """
            pass

        g = G()
        try:
            g[42]
        except KeyError as err:
            self.assertEqual(err.args, (42,))
        else:
            self.fail("g[42] didn't raise KeyError")

        class H(D):
            """
            subclass calls super classes __missing__ and modifies the value before returning it
            """
            def __missing__(self, key):
                return super(H, self).__missing__(key) + 1

        h = H()
        self.assertEqual(h[None], d[None]+1)


def test_main():
    import logging
    log = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    log.info("=======================")
    log.info("STARTING - COMMON TESTS")
    log.info("=======================")
    log.info("######################################################################")

    suite = unittest.TestLoader().loadTestsFromTestCase(NumDictTest)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    test_main()
