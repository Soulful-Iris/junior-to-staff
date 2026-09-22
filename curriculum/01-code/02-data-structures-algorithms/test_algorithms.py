import itertools
import unittest
from algorithms import *

class AlgorithmsTest(unittest.TestCase):
    def test_maps_and_windows_against_oracles(self):
        for n in range(6):
            for values in itertools.product((-1, 0, 1), repeat=n):
                for target in (-1, 0, 1):
                    expected = sum(sum(values[i:j]) == target for i in range(n) for j in range(i+1, n+1))
                    self.assertEqual(subarray_sum(values, target), expected)
                    pair = two_sum(values, target)
                    exists = any(values[i]+values[j] == target for i in range(n) for j in range(i+1,n))
                    self.assertEqual(pair is not None, exists)
                    if pair:
                        self.assertNotEqual(*pair)
                        self.assertEqual(sum(values[i] for i in pair), target)
        for n in range(7):
            for chars in itertools.product('abc', repeat=n):
                text = ''.join(chars)
                expected = max([0] + [j-i for i in range(n) for j in range(i+1,n+1) if len(set(text[i:j])) == j-i])
                self.assertEqual(longest_unique(text), expected)

    def test_binary_and_intervals(self):
        for target, expected in [(-1,0),(1,0),(2,1),(3,3),(9,4)]:
            self.assertEqual(lower_bound([1,2,2,5],target),expected)
        self.assertEqual(lower_bound([],1),0)
        intervals=[[4,5],[1,3],[3,4]]
        self.assertEqual(merge_intervals(intervals),[[1,5]])
        self.assertEqual(intervals,[[4,5],[1,3],[3,4]])
        with self.assertRaises(ValueError): merge_intervals([(3,1)])

    def test_graphs(self):
        grid=[list('110'),list('010'),list('001')]
        original=[row[:] for row in grid]
        self.assertEqual(islands(grid),2)
        self.assertEqual(grid,original)
        self.assertEqual(islands([[]]),0)
        with self.assertRaises(ValueError): islands([['1'],[]])
        self.assertEqual(course_order(2,[(1,0),(1,0)]),[0,1])
        self.assertEqual(course_order(2,[(1,0),(0,1)]),[])
        self.assertEqual(shortest_paths(4,[(0,1,8),(0,2,1),(2,1,1)],0),[0,2,1,float('inf')])
        with self.assertRaises(ValueError): shortest_paths(2,[(0,1,-1)],0)

    def test_lru(self):
        cache=LRU(2);cache.put('a',1);cache.put('b',2)
        self.assertEqual(cache.get('a'),1)
        cache.put('c',3);self.assertIsNone(cache.get('b'))
        cache.put('a',4);self.assertEqual(cache.get('a'),4)
        cache=LRU(0);cache.put('a',1);self.assertIsNone(cache.get('a'))

    def test_other_patterns(self):
        self.assertEqual(top_k_frequent([3,3,2,2,1],2),[2,3])
        self.assertEqual(top_k_frequent([],3),[])
        self.assertEqual(min_coins([1,3,4],6),2)  # Greedy chooses 4+1+1.
        self.assertEqual(min_coins([2],3),-1)
        self.assertEqual(min_coins([],0),0)
        self.assertEqual(daily_temperatures([73,74,75,71,69,72,76,73]),[1,1,4,2,1,1,0,0])
        board=[list('AB'),list('CD')]
        self.assertTrue(word_exists(board,'ABD'))
        self.assertFalse(word_exists(board,'ABA'))
        trie=Trie();trie.insert('app')
        self.assertTrue(trie.contains('app'));self.assertFalse(trie.contains('ap'))
        trie.insert('');self.assertTrue(trie.contains(''))

if __name__ == '__main__': unittest.main()
