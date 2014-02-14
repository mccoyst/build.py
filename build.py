#!/usr/bin/env python

import glob
import os
import os.path
import pickle
import subprocess

cc = 'clang'
cflags = ['-Wall', '-Werror', '-g', '-O2']
ld = 'clang'
ldflags = []

def build(deps):
	recipe = tsort(deps)
	if not recipe:
		print 'something bad happened'
		return

	for step in recipe:
		last_mod = 0
		try:
			s = os.stat(step)
			last_mod = s.st_mtime
		except OSError:
			pass
		up_to_date = True
		for dep in deps[step]:
			try:
				s = os.stat(dep)
				if last_mod < s.st_mtime:
					up_to_date = False
					break
			except OSError:
				print "I don't know how to build %s and it doesn't exist." % (dep)
				return

		if up_to_date:
			continue

		if step.endswith('.c') or step.endswith('.h'):
			if last_mod == 0 and len(deps[step]) == 0:
				print "I don't know how to build %s and it doesn't exist." % (step)
				return
		elif step.endswith('.o'):
			src = [c for c in deps[step] if c.endswith('.c')]
			try:
				output, newdeps = compile(step, src)
				for nd in newdeps:
					if nd not in deps: deps[nd] = []
				deps[step] = list(set(deps[step]) | set(newdeps))
				if output: print output,
			except subprocess.CalledProcessError as err:
				print 'failed to compile %s:\n%s' % (step, err.output),			
		else:
			objs = [o for o in deps[step] if o.endswith('.o')]
			libs = [a for a in deps[step] if a.endswith('.a')]
			try:
				output = link(step, objs, libs)
				if output: print output,
			except subprocess.CalledProcessError as err:
				print 'failed to link %s:\n%s' % (step, err.output),

	with open('_depcache', 'wb') as cache:
		pickle.dump(deps, cache)

def compile(target, source):
	depfile = target+'.d'
	cmd = [cc, '-c', '-o', target, '-MMD', '-MF', depfile]
	cmd.extend(cflags)
	cmd.extend(source)
	output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	deps = []
	with open(depfile) as df:
		content = df.read()
		deps = content.rstrip().split()[1:]
	os.remove(depfile)
	return output, deps

def link(target, objs, libs):
	cmd = [ld, '-o', target]
	cmd.extend(ldflags)
	cmd.extend(objs)
	cmd.extend(libs)
	return subprocess.check_output(cmd, stderr=subprocess.STDOUT)

def tsort(graph):
	if len(graph) == 0:
		return None

	roots = []
	indegrees = {}
	dependants = {}

	for v, deps in graph.items():
		if len(deps) == 0:
			roots.append(v)
		indegrees[v] = len(deps)
		for dep in deps:
			if dep in dependants:
				dependants[dep].append(v)
			else:
				dependants[dep] = [v]

	if len(roots) == 0:
		return None

	recipe = []
	while len(roots) > 0:
		v = roots.pop()
		recipe.append(v)
		if v not in dependants:
			continue
		for kid in dependants[v]:
			indegrees[kid] -= 1
			if indegrees[kid] <= 0:
				roots.append(kid)
 
	if len(recipe) != len(graph):
		return None

	return recipe

if __name__ == '__main__':
	deps = {}
	try:
		with open('_depcache', 'rb') as cache:
			deps = pickle.load(cache)
	except IOError:
		name = os.path.basename(os.getcwd())
		sources = glob.glob('*.c')
		headers = glob.glob('*.h')
		objs = [o.replace('.c', '.o') for o in sources]
		deps = {
			name: objs,
		}
		for i, obj in enumerate(objs):
			deps[obj] = [sources[i]]
			deps[sources[i]] = []
	
	build(deps)
