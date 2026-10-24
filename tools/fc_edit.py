"""Helper used during fact-checking: apply (old,new) pairs, reporting any misses instead of aborting."""
def edit(p, pairs):
    s = open(p).read()
    miss = []
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b, 1)
        else:
            miss.append(a[:80])
    open(p, 'w').write(s)
    for m in miss:
        print("MISS:", m)
