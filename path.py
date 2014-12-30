# (c) 2014 David 'Tiran' Soria Parra
from heapq import heappush, heappop
from math import sqrt
from collections import namedtuple
import sys

class NoPathExists(Exception):
    pass

def bfs(start, goal, fn_neighbours, maxcount=None):
    queue = [(start, [start])]
    seen = set()
    results = []
    minimum = sys.maxint
    while queue:
        current, path = queue.pop(0)
        if len(path) > minimum:
            return results
        if current == goal:
            minimum = min(minimum, len(path))
            results.append(path)
            if maxcount and len(results) >= maxcount:
              return results
        for n in fn_neighbours(current):
            if current not in seen:
                npath = path + [n]
                queue.append((n, npath))
        seen.add(current)
    if results:
        return results
    return NoPathExists

def alljumps(start, goal, fn_neighbours):
    sets = {}
    for path in bfs(a, b, fn):
        for j, solarsystem in enumerate(path):
            if j not in sets:
                sets[j] = set()
            sets[j].add(solarsystem.name)
    return sets

def find(start, goal, fn_neighbours, fn_weight, fn_distance):
    """Simple A* algorithm for path finding.

    Currently doesn't properly update the priority queue with estimates.
    """
    def path(came_from, current):
        def path_reverse(came_from, current):
            if current in came_from:
                return [current] + path_reverse(came_from, came_from[current])
            return [current]
        p = path_reverse(came_from, current)
        p.reverse()
        return p

    closedset = set()
    came_from = {}
    openset = set([start])
    g_score = {start: 0}

    pq = []
    heappush(pq, (fn_distance(start, goal), start))
    while openset:
        _, current = heappop(pq)

        openset.remove(current)
        closedset.add(current)
        if current == goal:
            return path(came_from, current)
        for neighbour in fn_neighbours(current):
            if neighbour in closedset:
                continue
            tentative = g_score[current] + fn_weight(current, neighbour)
            if neighbour not in openset or tentative < g_score[neighbour]:
                came_from[neighbour] = current
                g_score[neighbour] = tentative

                if neighbour not in openset:
                    f = g_score[neighbour] + fn_distance(neighbour, goal)
                    openset.add(neighbour)
                    heappush(pq, (f, neighbour))
                else:
                    # TODO: DEREASE KEY FOR NEIGHBOUR
                    pass
    raise NoPathExists

if __name__ == '__main__':
    # tests
    def test_weight(a, b):
        return 1

    def test_distance(a, b):
        return sqrt((b.x - a.x)**2 + (b.y - a.y)**2)

    class Node(object):
        def __init__(self, name, x, y):
            self.name = name
            self.x = x
            self.y = y
        def __repr__(self):
            return self.name

    a = Node('a', 0, 0)
    b = Node('b', 0, 1)
    c = Node('c', 1, 0)
    d = Node('d', 2, 2)
    e = Node('e', 3, 3)

    def test_neighbours(a):
        return {a: [b, c],
                b: [d],
                c: [d]}.get(a, [])
    print find(a, d, test_neighbours, test_weight, test_distance)
    print bfs(a, d, test_neighbours)
