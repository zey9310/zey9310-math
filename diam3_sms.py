#!/usr/bin/env python3
"""
diam3_sms.py N [--maxdeg 4] [--diam 3] [--forbid 4,8] [--count] [--timeout SECONDS]

Decides, with SAT Modulo Symmetries (smsg + Glasgow subgraph solver), whether a graph exists on
N vertices with
    minimum degree >= 3,  maximum degree <= MAXDEG,  diameter <= DIAM (2 or 3),
    and no cycle of any FORBID length (default 4 and 8).
SMS generates graphs up to isomorphism, so "Number of graphs: 0" (UNSAT) is a complete proof
that no such graph exists on N vertices (up to solver correctness; add --lrat to get a checkable
proof). --count enumerates and counts all solutions (for validation against nauty).

Target: every graph with min degree >= 3 and diameter <= 3 has a 4- or 8-cycle. Graphs on
<= 23 vertices are settled (arXiv:2609.04686), and diameter <= 3 with max degree Delta forces
N <= 1 + Delta + Delta(Delta-1) + Delta(Delta-1)^2 (53 for Delta = 4). So running N = 24..53
with --maxdeg 4 settles the whole max-degree-4 case.
"""
import argparse, os, subprocess, sys, tempfile, time
from pysms.graph_builder import GraphEncodingBuilder


def add_diameter(b, n, D):
    """diameter <= D (D in {2, 3}) via auxiliary variables; only the needed implications."""
    E = b.var_edge
    R2 = {}
    for p in range(n):                       # R2[p,q] -> p~q or a common neighbour exists
        for q in range(p + 1, n):
            r = b.id()
            R2[(p, q)] = r
            clause = [-r, E(p, q)]
            for w in range(n):
                if w in (p, q):
                    continue
                a = b.id()
                b.append([-a, E(p, w)])
                b.append([-a, E(w, q)])
                clause.append(a)
            b.append(clause)
    r2 = lambda p, q: R2[(min(p, q), max(p, q))]
    for u in range(n):
        for v in range(u + 1, n):
            if D == 2:
                b.append([r2(u, v)])
                continue
            clause = [r2(u, v)]              # dist <= 2, or u~w with dist(w,v) <= 2
            for w in range(n):
                if w in (u, v):
                    continue
                a = b.id()
                b.append([-a, E(u, w)])
                b.append([-a, r2(w, v)])
                clause.append(a)
            b.append(clause)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int)
    ap.add_argument("--mindeg", type=int, default=3)
    ap.add_argument("--maxdeg", type=int, default=4)
    ap.add_argument("--diam", type=int, default=3, choices=[2, 3])
    ap.add_argument("--forbid", default="4,8", help="comma-separated cycle lengths to forbid")
    ap.add_argument("--count", action="store_true", help="count all solutions (validation)")
    ap.add_argument("--timeout", type=float, default=None)
    ap.add_argument("--lrat", default=None, help="write an LRAT proof of UNSAT to this file")
    a = ap.parse_args()
    n = a.n

    b = GraphEncodingBuilder(n, directed=False)
    b.minDegree(a.mindeg)
    if a.maxdeg < n - 1:
        b.maxDegree(a.maxdeg)
    add_diameter(b, n, a.diam)

    tmp = tempfile.mkdtemp()
    cnf, cyc = os.path.join(tmp, "enc.cnf"), os.path.join(tmp, "cycles.txt")
    with open(cnf, "w") as fh:
        b.print_dimacs(fh)
    with open(cyc, "w") as f:
        for k in map(int, a.forbid.split(",")):
            f.write(f"{k} " + " ".join(f"{i} {(i + 1) % k}" for i in range(k)) + "\n")

    cmd = ["smsg", "--vertices", str(n), "--all-graphs", "--forbidden-subgraph-file", cyc, "--dimacs", cnf]
    if not a.count:
        cmd.append("--hide-graphs")
    if a.lrat:
        cmd += ["--lrat-output", a.lrat]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print(f"n={n} mindeg={a.mindeg} maxdeg={a.maxdeg} diam<={a.diam} forbid={a.forbid}: TIMEOUT after {time.time()-t0:.0f}s", flush=True)
        return
    count = None
    for line in p.stdout.splitlines():
        if line.strip().startswith("Number of graphs:"):
            count = int(line.split(":")[1])
    status = "ERROR" if count is None else ("UNSAT (no such graph)" if count == 0 else f"{count} graph(s) FOUND")
    print(f"n={n} mindeg={a.mindeg} maxdeg={a.maxdeg} diam<={a.diam} forbid={a.forbid}: {status}  [{time.time()-t0:.1f}s]", flush=True)
    if count is None:
        print(p.stdout[-800:], p.stderr[-800:])
    if count and not a.count:
        print("!!! rerun with --count to print the graphs, then verify them independently")


if __name__ == "__main__":
    main()
