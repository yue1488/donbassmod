"""Frequency estimate of the structure sets of the Donbass dimension (stdlib only).

An exact re-implementation of the vanilla 1.20.1 algorithm of minecraft:random_spread (one candidate chunk per
spacing x spacing region, positioned with a LegacyRandomSource seeded from region, world seed and salt) including the
exclusion zones (a candidate is dropped when a candidate of the other set lies within chunk_count chunks - the other
set's own exclusion zone applies there too).  It counts candidates that survive the exclusion zones; the biome rule
(steppe / balka) and the placement of the pieces are not part of it, so only RELATIVE numbers between two parameter
sets are meaningful.

Usage:  python3 tools/sim_structure_frequency.py [seeds] ["SPACING/SEP+SPACING/SEP" ...]
        e.g.  python3 tools/sim_structure_frequency.py 4 "17/6+13/5"   (settlements + checkpoints, compared with the
        0.3.1 values 16/6 + 14/5 that are always printed first).  Prints structures per 10,000 chunks.
"""
import sys, random
M48 = (1 << 48) - 1

def potential(seed, salt, spacing, sep, cx, cz):
    rx, rz = cx // spacing, cz // spacing                      # floorDiv
    s = (rx * 341873128712 + rz * 132897987541 + seed + salt)
    s = (s & ((1 << 64) - 1))
    st = (s ^ 0x5DEECE66D) & M48
    def nxt(bits):
        nonlocal st
        st = (st * 0x5DEECE66D + 0xB) & M48
        return st >> (48 - bits)
    def nextInt(bound):
        if bound & (bound - 1) == 0:
            return (bound * nxt(31)) >> 31
        while True:
            i = nxt(31); j = i % bound
            if i - j + (bound - 1) < (1 << 31):
                return j
    k = spacing - sep
    a = nextInt(k); b = nextInt(k)
    return rx * spacing + a, rz * spacing + b

class Set:
    def __init__(s, salt, spacing, sep, excl=None):
        s.salt, s.sp, s.sep, s.excl = salt, spacing, sep, excl   # excl = (Set, chunk_count)
    def is_chunk(s, seed, cx, cz, cache):
        key = (id(s), cx, cz)
        r = cache.get(key)
        if r is None:
            px, pz = potential(seed, s.salt, s.sp, s.sep, cx // s.sp * s.sp, cz // s.sp * s.sp)
            r = (px == cx and pz == cz)
            if r and s.excl:
                other, c = s.excl
                for i in range(cx - c, cx + c + 1):
                    for j in range(cz - c, cz + c + 1):
                        if other.is_chunk(seed, i, j, cache):
                            r = False; break
                    if not r: break
            cache[key] = r
        return r

def count(sset, seed, regions=120):
    """number of structure chunks and of raw candidates in regions x regions regions"""
    cache = {}
    n_ok = n_all = 0
    for rx in range(regions):
        for rz in range(regions):
            px, pz = potential(seed, sset.salt, sset.sp, sset.sep, rx * sset.sp, rz * sset.sp)
            n_all += 1
            if sset.is_chunk(seed, px, pz, cache):
                n_ok += 1
    return n_ok, n_all

def world(settle, blockpost):
    S = Set(1730101, *settle)
    return {
        "settlements": S,
        "shallow": Set(1730102, 10, 4),
        "active": Set(1730103, 20, 7, (S, 3)),
        "deep": Set(1730104, 24, 8, (S, 3)),
        "plants": Set(1730105, 18, 6, (S, 4)),
        "freight": Set(1730106, 22, 7, (S, 4)),
        "blockposts": Set(1730107, blockpost[0], blockpost[1], (S, 3)),
        "admin": Set(1730108, 36, 14, (S, 4)),
    }

def density(name, w, seeds, area_chunks=2400):
    """structures per 1000x1000 chunks (equal area for all sets): count regions covering area_chunks^2 chunks"""
    tot = 0.0
    for seed in seeds:
        sset = w[name]
        regions = area_chunks // sset.sp
        cache = {}
        ok = 0
        for rx in range(regions):
            for rz in range(regions):
                px, pz = potential(seed, sset.salt, sset.sp, sset.sep, rx * sset.sp, rz * sset.sp)
                if sset.is_chunk(seed, px, pz, cache):
                    ok += 1
        tot += ok / (regions * sset.sp) ** 2 * 1e4        # per 10,000 chunks
    return tot / len(seeds)

if __name__ == "__main__":
    rnd = random.Random(2026)
    seeds = [rnd.getrandbits(63) for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 4)]
    configs = {"old 16/6 + 14/5": ((16, 6), (14, 5))}
    for a in sys.argv[2:]:
        s, b = a.split("+")
        configs[a] = (tuple(map(int, s.split("/"))), tuple(map(int, b.split("/"))))
    base = None
    for label, (st, bp) in configs.items():
        w = world(st, bp)
        res = {n: density(n, w, seeds) for n in w}
        if base is None:
            base = res
        print(f"== settlements {st}, blockposts {bp}")
        for n, v in res.items():
            print(f"  {n:11s} {v:7.2f} per 10k chunks   x{v / base[n]:.3f} vs old")
