import unittest
import pytest
from collections import UserDict

from sickchill.oldbeard.numdict import NumDict


class NumDictTest(unittest.TestCase):
    """
    Test the NumDict class
    """

    def test_constructors(self):
        """
        Test NumDict constructors
        """
        # dicts for testing
        dict_0 = {}  # Empty dictionary
        dict_1 = {1: "Elephant"}  # Single numeric key
        dict_2 = {1: "Elephant", 2: "Mouse"}  # Multiple numeric keys
        dict_3 = {"3": "Aardvark"}  # Numeric string key
        dict_4 = {"3": "Aardvark", "4": "Ant"}  # Multiple numeric string keys
        dict_5 = {5: "Cat", "6": "Dog"}  # Mixed numeric and numeric string keys
        dict_6 = {1: None, "2": None}  # None as values
        dict_7 = {0: "Empty"}  # None as key

        # Construct NumDicts from dicts
        num_dict = NumDict()
        num_dict_0 = NumDict(dict_0)
        num_dict_1 = NumDict(dict_1)
        num_dict_2 = NumDict(dict_2)
        num_dict_3 = NumDict(dict_3)
        num_dict_4 = NumDict(dict_4)
        num_dict_5 = NumDict(dict_5)
        num_dict_6 = NumDict(dict_6)
        num_dict_7 = NumDict(dict_7)

        # Most NumDicts from dicts should compare equal...
        assert num_dict == {}
        assert num_dict_0 == dict_0
        assert num_dict_1 == dict_1
        assert num_dict_2 == dict_2

        # ...however, numeric keys are not equal to numeric string keys...
        assert num_dict_3 != dict_3
        assert num_dict_4 != dict_4
        assert num_dict_5 != dict_5
        assert num_dict_6 != dict_6

        assert num_dict_7 == dict_7

        # Construct dicts from NumDicts
        dict_from_num_dict = dict(num_dict)
        dict_from_num_dict_1 = dict(num_dict_1)
        dict_from_num_dict_2 = dict(num_dict_2)
        dict_from_num_dict_3 = dict(num_dict_3)
        dict_from_num_dict_4 = dict(num_dict_4)
        dict_from_num_dict_5 = dict(num_dict_5)
        dict_from_num_dict_6 = dict(num_dict_6)
        dict_from_num_dict_7 = dict(num_dict_7)

        # All dicts from NumDicts should compare equal
        assert num_dict == dict_from_num_dict
        assert num_dict_1 == dict_from_num_dict_1
        assert num_dict_2 == dict_from_num_dict_2
        assert num_dict_3 == dict_from_num_dict_3
        assert num_dict_4 == dict_from_num_dict_4
        assert num_dict_5 == dict_from_num_dict_5
        assert num_dict_6 == dict_from_num_dict_6
        assert num_dict_7 == dict_from_num_dict_7

        # Construct NumDicts from NumDicts
        num_dict_from_num_dict = NumDict(num_dict)
        num_dict_from_num_dict_0 = NumDict(num_dict_0)
        num_dict_from_num_dict_1 = NumDict(num_dict_1)
        num_dict_from_num_dict_2 = NumDict(num_dict_2)
        num_dict_from_num_dict_3 = NumDict(num_dict_3)
        num_dict_from_num_dict_4 = NumDict(num_dict_4)
        num_dict_from_num_dict_5 = NumDict(num_dict_5)
        num_dict_from_num_dict_6 = NumDict(num_dict_6)
        num_dict_from_num_dict_7 = NumDict(num_dict_7)

        # All NumDicts from NumDicts should compare equal
        assert num_dict == num_dict_from_num_dict
        assert num_dict_0 == num_dict_from_num_dict_0
        assert num_dict_1 == num_dict_from_num_dict_1
        assert num_dict_2 == num_dict_from_num_dict_2
        assert num_dict_3 == num_dict_from_num_dict_3
        assert num_dict_4 == num_dict_from_num_dict_4
        assert num_dict_5 == num_dict_from_num_dict_5
        assert num_dict_6 == num_dict_from_num_dict_6
        assert num_dict_7 == num_dict_from_num_dict_7

        # keyword arg constructor should fail
        with self.assertRaises(TypeError):
            NumDict(one=1, two=2)  # Raise TypeError since we can't have numeric keywords

        # item sequence constructors work fine...
        assert NumDict([(1, "Elephant"), (2, "Mouse")]) == dict_from_num_dict_2
        assert NumDict(dict=[(1, "Elephant"), (2, "Mouse")]) == dict_from_num_dict_2
        assert NumDict([(1, "Elephant"), ("2", "Mouse")]) == dict_from_num_dict_2
        assert NumDict(dict=[("1", "Elephant"), (2, "Mouse")]) == dict_from_num_dict_2

        # ...unless you have a non-numeric key
        with self.assertRaises(TypeError):
            NumDict([("Rat", 11), ("Snake", 12)])
        with self.assertRaises(TypeError):
            NumDict(dict=[("Rat", 11), ("Snake", 12)])

        # combining item sequence constructors with keyword args does not work
        with self.assertRaises(TypeError):  # Raise TypeError since we can't have numeric keywords
            NumDict([(1, "one"), (2, "two")], two=3, five=4)

        # alternate constructors
        dict_8 = {1: "Echo", 2: "Echo"}

        assert NumDict.fromkeys("1 2".split()) == dict_from_num_dict_6
        assert NumDict().fromkeys("1 2".split()) == dict_from_num_dict_6
        assert NumDict.fromkeys("1 2".split(), "Echo") == dict_8
        assert NumDict().fromkeys("1 2".split(), "Echo") == dict_8
        assert num_dict_1.fromkeys("1 2".split()) is not num_dict_1
        self.assertIsInstance(num_dict_1.fromkeys("1 2".split()), NumDict)
        self.assertIsInstance(num_dict_2.fromkeys("1 2".split()), NumDict)
        self.assertIsInstance(num_dict_3.fromkeys("1 2".split()), NumDict)
        self.assertIsInstance(num_dict_4.fromkeys("1 2".split()), NumDict)

    def test_repr(self):
        """
        Test representation of NumDicts
        """
        # dicts for testing
        dict_0 = {}  # Empty dictionary
        dict_1 = {1: "Elephant"}  # Single numeric key
        dict_2 = {1: "Elephant", 2: "Mouse"}  # Multiple numeric keys
        dict_3 = {"3": "Aardvark"}  # Numeric string key
        dict_4 = {"3": "Aardvark", "4": "Ant"}  # Multiple numeric string keys
        dict_5 = {5: "Cat", "6": "Dog"}  # Mixed numeric and numeric string keys
        dict_6 = {1: None, "2": None}  # None as values
        dict_7 = {0: "Empty"}  # None as key

        #  Construct NumDicts from dicts
        num_dict = NumDict()
        num_dict_0 = NumDict(dict_0)
        num_dict_1 = NumDict(dict_1)
        num_dict_2 = NumDict(dict_2)
        num_dict_3 = NumDict(dict_3)
        num_dict_4 = NumDict(dict_4)
        num_dict_5 = NumDict(dict_5)
        num_dict_6 = NumDict(dict_6)
        num_dict_7 = NumDict(dict_7)

        reps = (
            "{}",
            "{1: 'Elephant'}",
            "{1: 'Elephant', 2: 'Mouse'}",
            "'3': 'Aardvark'",
            "{'3': 'Aardvark', '4': 'Ant'}",
            "{5: 'Cat', '6': 'Dog'}",
            "{1: None, '2': None}",
            "{0: 'Empty'}",
        )

        # Most representations of NumDicts should compare equal to dicts...
        assert str(num_dict) == str({})
        assert repr(num_dict) == repr({})
        assert repr(num_dict) in reps

        assert str(num_dict_0) == str(dict_0)
        assert repr(num_dict_0) == repr(dict_0)
        assert repr(num_dict_0) in reps

        assert str(num_dict_1) == str(dict_1)
        assert repr(num_dict_1) == repr(dict_1)
        assert repr(num_dict_1) in reps

        assert str(num_dict_2) == str(dict_2)
        assert repr(num_dict_2) == repr(dict_2)
        assert repr(num_dict_2) in reps

        # ...however, numeric keys are not equal to numeric string keys...
        # ...so the string representations for those are different...
        assert str(num_dict_3) != str(dict_3)
        assert repr(num_dict_3) != repr(dict_3)
        assert repr(num_dict_3) not in reps

        assert str(num_dict_4) != str(dict_4)
        assert repr(num_dict_4) != repr(dict_4)
        assert repr(num_dict_4) not in reps

        assert str(num_dict_5) != str(dict_5)
        assert repr(num_dict_5) != repr(dict_5)
        assert repr(num_dict_5) not in reps

        assert str(num_dict_6) != str(dict_6)
        assert repr(num_dict_6) != repr(dict_6)
        assert repr(num_dict_6) not in reps

        # ...but None keys work just fine
        assert str(num_dict_7) == str(dict_7)
        assert repr(num_dict_7) == repr(dict_7)
        assert repr(num_dict_7) in reps

    def test_rich_comparison_and_len(self):
        """
        Test rich comparison and length
        """
        # dicts for testing
        dict_0 = {}  # Empty dictionary
        dict_1 = {1: "Elephant"}  # Single numeric key
        dict_2 = {1: "Elephant", 2: "Mouse"}  # Multiple numeric keys

        # Construct NumDicts from dicts
        num_dict = NumDict()
        num_dict_0 = NumDict(dict_0)
        num_dict_1 = NumDict(dict_1)
        num_dict_2 = NumDict(dict_2)

        # Construct NumDicts from NumDicts
        num_dict_from_num_dict = NumDict(num_dict)
        num_dict_from_num_dict_0 = NumDict(num_dict_0)
        num_dict_from_num_dict_1 = NumDict(num_dict_1)
        num_dict_from_num_dict_2 = NumDict(num_dict_2)

        all_dicts = [
            dict_0,
            dict_1,
            dict_2,
            num_dict,
            num_dict_0,
            num_dict_1,
            num_dict_2,
            num_dict_from_num_dict,
            num_dict_from_num_dict_0,
            num_dict_from_num_dict_1,
            num_dict_from_num_dict_2,
        ]
        for val_a in all_dicts:
            for val_b in all_dicts:
                assert (val_a == val_b) == (len(val_a) == len(val_b))

    def test_dict_access_and_mod(self):
        """
        Test num dict access and modification
        """
        # dicts for testing
        dict_0 = {}  # Empty dictionary
        dict_1 = {1: "Elephant"}  # Single numeric key
        dict_2 = {1: "Elephant", 2: "Mouse"}  # Multiple numeric keys

        #  Construct NumDicts from dicts
        num_dict_0 = NumDict()
        num_dict_1 = NumDict(dict_1)
        num_dict_2 = NumDict(dict_2)

        # test __getitem__
        assert num_dict_2[1] == "Elephant"
        with pytest.raises(KeyError):
            _ = num_dict_1["Mouse"]  # key is not numeric
        with pytest.raises(KeyError):
            _ = num_dict_1.__getitem__("Mouse")  # key is not numeric
        with pytest.raises(KeyError):
            _ = num_dict_1[None]  # key does not exist
        with pytest.raises(KeyError):
            _ = num_dict_1.__getitem__(None)  # key does not exist

        # Test __setitem__
        num_dict_3 = NumDict(num_dict_2)
        assert num_dict_2 == num_dict_3

        num_dict_3[2] = "Frog"
        assert num_dict_2 != num_dict_3

        # Check None keys and numeric key conversion
        num_dict_3["3"] = "Armadillo"
        num_dict_3[None] = "Cockroach"

        # Check long ints
        num_dict_3[12390809518259081208909880312] = "Squid"
        num_dict_3["12390809518259081208909880312"] = "Octopus"
        assert num_dict_3[12390809518259081208909880312] == "Octopus"

        with pytest.raises(TypeError):
            num_dict_3.__setitem__("Gorilla", 1)  # key is not numeric
        with pytest.raises(TypeError):
            num_dict_3["Chimpanzee"] = 1  # key is not numeric
        with pytest.raises(TypeError):
            num_dict_3[(4, 1)] = 1  # key is not numeric
        with pytest.raises(TypeError):
            num_dict_3[[1, 3, 4]] = 1  # key is not numeric and is not hashable

        # Test __delitem__
        del num_dict_3[3]
        del num_dict_3[None]
        with pytest.raises(KeyError):
            del num_dict_3[3]  # already deleted
        with pytest.raises(KeyError):
            num_dict_3.__delitem__(3)  # already deleted
        with pytest.raises(KeyError):
            del num_dict_3["Mouse"]  # key would not exist, since it is not numeric

        # Test clear
        num_dict_3.clear()
        assert num_dict_3 == {}

        # Test copy()
        num_dict_2a = dict_2.copy()
        assert num_dict_2 == num_dict_2a
        num_dict_2b = num_dict_2.copy()
        assert num_dict_2b == num_dict_2
        num_dict_2c = UserDict({1: "Elephant", 2: "Mouse"})
        num_dict_2d = num_dict_2c.copy()  # making a copy of a UserDict is special cased
        assert num_dict_2c == num_dict_2d

        class MyNumDict(NumDict):
            """
            subclass Numdict for testing
            """

            def display(self):
                """
                add a method to subclass to differentiate from superclass
                """
                print("MyNumDict:", self)

        my_num_dict = MyNumDict(num_dict_2)
        my_num_dict_a = my_num_dict.copy()
        assert my_num_dict_a == my_num_dict

        my_num_dict[1] = "Frog"
        assert my_num_dict_a != my_num_dict

        # Test keys, items, values
        assert sorted(num_dict_2) == sorted(dict_2)
        assert sorted(num_dict_2.items()) == sorted(dict_2.items())
        assert sorted(num_dict_2.values()) == sorted(dict_2.values())

        # Test "in".
        for i in num_dict_2:
            assert i in num_dict_2
            assert (i in num_dict_1) == (i in dict_1)
            assert (i in num_dict_0) == (i in dict_0)

        assert None not in num_dict_2
        assert (None in num_dict_2) is (None in dict_2)

        dict_2[None] = "Cow"
        num_dict_2[None] = dict_2[None]
        assert None in num_dict_2
        assert (None in num_dict_2) is (None in dict_2)

        assert "Penguin" not in num_dict_2

        # Test update
        test = NumDict()
        test.update(dict_2)
        assert test == num_dict_2

        # Test get
        for i in num_dict_2:
            assert num_dict_2.get(i) == num_dict_2[i]
            assert num_dict_1.get(i) == dict_1.get(i)
            assert num_dict_0.get(i) == dict_0.get(i)

        for i in ["purple", None, 12312301924091284, 23]:
            assert num_dict_2.get(i) == dict_2.get(i), i

        with pytest.raises(AssertionError):
            assert num_dict_2.get("1") == dict_2.get("1"), 1  # dict_2 expects string key which does not exist

        # Test "in" iteration.
        num_dict_2b = num_dict_2
        for i in range(20):
            num_dict_2[i] = str(i)
            num_dict_2b[str(i)] = str(i)
        assert num_dict_2 == num_dict_2b

        ikeys = []
        for k in num_dict_2:
            ikeys.append(k)
        assert set(ikeys) == set(num_dict_2)

        # Test setdefault
        val = 1
        test = NumDict()
        assert test.setdefault(val, 42) == 42
        assert test.setdefault(val, "42") == 42
        assert test.setdefault(val, 42) != "42"
        assert test.setdefault(val, "42") != "42"
        assert val in test

        assert test.setdefault(val, 23) == 42
        assert test.setdefault(val, "23") ==  42
        assert test.setdefault(val, 23) != "42"
        assert test.setdefault(val, "23") != "42"
        assert val in test

        # Test pop
        val = 1
        test = NumDict({val: 42})
        assert test.pop(val) == 42
        pytest.raises(KeyError, test.pop, val)
        assert test.pop(val, 1) == 1
        test[val] = 42
        assert test.pop(val, 1) == 42

        # Test popitem
        val = 1
        test = NumDict({val: 42})
        assert test.popitem() == (val, 42)
        pytest.raises(KeyError, test.popitem)

    def test_missing(self):
        """
        Test missing keys
        """
        # Make sure NumDict doesn't have a __missing__ method
        assert not hasattr(NumDict, "__missing__")

        class NumDictD(NumDict):
            """
            subclass defines __missing__ method returning a value
            """

            def __missing__(self, key):
                key = 42
                return key

        num_dict_d = NumDictD({1: 2, 3: 4})
        assert num_dict_d[1] == 2
        assert num_dict_d[3] == 4
        assert 2 not in num_dict_d
        assert 2 not in num_dict_d
        assert num_dict_d[2] == 42

        class NumDictE(NumDict):
            """
            subclass defines __missing__ method raising RuntimeError
            """

            def __missing__(self, key):
                raise RuntimeError(key)

        num_dict_e = NumDictE()
        try:
            num_dict_e[42]
        except RuntimeError as err:
            assert err.args == (42,)
        else:
            self.fail("num_dict_e[42] didn't raise RuntimeError")

        class NumDictF(NumDict):
            """
            subclass sets __missing__ instance variable (no effect)
            """

            def __init__(self):
                # An instance variable __missing__ should have no effect
                self.__missing__ = lambda key: None
                NumDict.__init__(self)

        num_dict_f = NumDictF()
        try:
            num_dict_f[42]
        except KeyError as err:
            assert err.args == (42,)
        else:
            self.fail("num_dict_f[42] didn't raise KeyError")

        class NumDictG(NumDict):
            """
            subclass doesn't define __missing__ at a all
            """

            pass

        num_dict_g = NumDictG()
        try:
            num_dict_g[42]
        except KeyError as err:
            assert err.args == (42,)
        else:
            self.fail("num_dict_g[42] didn't raise KeyError")

        class NumDictH(NumDictD):
            """
            subclass calls super classes __missing__ and modifies the value before returning it
            """

            def __missing__(self, key):
                return super().__missing__(key) + 1

        num_dict_h = NumDictH()
        assert num_dict_h[None] == num_dict_d[None] + 1


def test_main():
    """
    Run tests when run as main
    """
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
