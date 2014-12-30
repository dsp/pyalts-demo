# (c) 2014 David 'Tiran' Soria Parra
#import mysql.connector as db
import sqlite3 as db
import math
from collections import defaultdict

import path

DB_FILE = 'neweden.sqlite'
baserange = {'supercarrier': 5,
             'carrier': 6.5,
             'dreadnought': 5,
             'jumpfreighter': 5,
             'titan': 3.5,
             'blackops': 3.5}
shiptypes = baserange.keys()

security = {'highsec': 1.00,
            'lowsec': 0.45,
            'nullsec': 0.0}

lightyear = 9.4605284e15 # meters

class SolarSystem(object):
    def __init__(self, sid, name, x, y, z, sec):
        self.sid = sid
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.sec = sec

def neighbours(start, adjacents):
    return adjacents.get(start, [])

def weight(start, goal):
    return 1

def distance(start, goal):
    dx = goal.x - start.x
    dy = goal.y - start.y
    dz = goal.z - start.z
    return math.sqrt(dx*dx + dy*dy + dz*dz) / lightyear

def inrange(start, totest, r):
    dx = (totest.x - start.x) / lightyear
    dy = (totest.y - start.y) / lightyear
    dz = (totest.z - start.z) / lightyear
    return (dx*dx + dy*dy + dz*dz) <= r*r

def jumpadjacent(neweden, jumprange, maxsec=None):
    if maxsec is None:
        maxsec = security['lowsec']

    sortedlist = sorted(neweden.values(), key=lambda x: x.sid)
    d = {}
    for source in sortedlist:
        adjacents = []
        for dest in sortedlist:
            if dest.sid == source.sid:
                continue
            if dest.sec < maxsec:
                dist = distance(source, dest)
                if dist <= jumprange:
                    adjacents.append((dest, dist))
        d[source] = adjacents
    return d

def exists(systems):
    cnx = db.connect(DB_FILE)
    cur = cnx.cursor()
    instr = ','.join(['?'] * len(systems))
    cur.execute("""
        SELECT COUNT(solarSystemID) as c
          FROM mapSolarSystems
         WHERE solarSystemName IN ({})
        """.format(instr), systems)
    count, = cur.fetchone()
    return count == len(systems)

def universe(wormholes=False, maxsec=None):
    if maxsec is None:
        maxsec = security['highsec']
    cnx = db.connect(DB_FILE)
    cur = cnx.cursor()

    excludewspace = ""
    if not wormholes:
        excludewspace = "src.regionID < 11000000 AND"

    # regionID >= 11000000 are W-Space and region 10000004 is UA- CCP
    # consellation

    connections = """
        SELECT
            src.solarSystemID,
            src.solarSystemName,
            src.x,
            src.y,
            src.z,
            src.security,
            dst.solarSystemID,
            dst.solarSystemName,
            dst.x,
            dst.y,
            dst.z,
            dst.security
        FROM
            mapSolarSystems AS src
        LEFT JOIN
            mapSolarSystemJumps AS con,
            mapSolarSystems AS dst
        ON
            src.solarSystemID = con.fromSolarSystemID AND
            dst.solarSystemID = con.toSolarSystemID
        WHERE
            (src.security <= {maxsec} OR dst.security <= {maxsec}) AND
            {wspace} src.regionID != 10000004
        """.format(wspace=excludewspace, maxsec=maxsec)

    universe = {}
    cur.execute(connections)

    adjacentlist = defaultdict(set)
    for row in cur:
        src = universe.get(row[1].lower(), None)
        if src is None:
            src = SolarSystem(*row[6:12])
            universe[src.name.lower()] = src

        dst = universe.get(row[7].lower(), None)
        if dst is None:
            dst = SolarSystem(*row[6:12])
            universe[dst.name.lower()] = dst
        adjacentlist[src].add(dst)
        adjacentlist[dst].add(src)

    cur.close()
    cnx.close()
    return universe, adjacentlist

def jumprange(ship, lvl):
    return baserange[ship] * (1.0 + 0.25 * lvl)

if __name__ == '__main__':
    import sys, functools
    solarsystems, connections = universe()
    s1, s2 = sys.argv[1:]
    a = solarsystems[s1.lower()]
    b = solarsystems[s2.lower()]

    fn = lambda x: neighbours(x, connections)
    direct = map(lambda s: s.name, path.find(a, b, fn, weight, distance))

    print "%s -> %s" % (s1, s2)
    print "distance:   {:.4f} ly".format(distance(a, b))
    print "path:       [{}]: {}".format(len(direct), u' -> '.join(direct))

    def highsec(start, goal):
        if start.sec >= security['lowsec'] and goal.sec >= security['lowsec']:
            return 1000
        else:
            return 5000

    direct = map(lambda s: s.name, path.find(a, b, fn, highsec, distance))
    print "path (hsec) [{}]: {}".format(len(direct), u' -> '.join(direct))
