#!/usr/bin/env python

from build import tsort

def is_legit(recipe, graph):
	if recipe is None:
		return False

	seen = set()
	for x in recipe:
		if x not in graph:
			return False
		for d in graph[x]:
			if d not in seen:
				return False
		seen.add(x)
	return True

if __name__ == '__main__':
	test_tests = [
		({}, None),
		({'a':[]}, ['b']),
		({'a':[], 'b':['a']}, ['b', 'a']),
	]
	for g, r in test_tests:
		assert not is_legit(r, g), 'illegitimate (%r): %r' % (g, r)

	good_tests = [
		{'a':[]},
		{'a':[], 'b':['a']},
		{'a':[], 'b':['a'], 'c':['b']},
		{'a':[], 'b':[], 'c':['a','b']},
		{'a':[], 'b':['a'], 'c':['a','b']},
	]
	for test in good_tests:
		result = tsort(test)
		assert is_legit(result, test), 'illegitimate: tsort(%r) = %r' % (test, result)

	bad_tests = [
		{'a':['b'], 'b':['a']},
		{'a':[], 'b':['a','c'], 'c':['b']},
		{'a':[], 'b':['c'], 'c':['b']},
		{'a':['z']},
		{},
		{'a':['b','z'], 'b':[]},
	]
	for test in bad_tests:
		result = tsort(test)
		assert result == None, '%r != %r' % (result, None)
