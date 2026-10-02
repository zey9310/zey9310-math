#!/bin/bash
# build_sms.sh — builds SAT Modulo Symmetries (smsg) with the Glasgow Subgraph Solver,
# pinned to the versions that were tested (Ubuntu 24.04, 29-30 Sep 2026).
# These are the commands that produced a working build in the test environment; the
# script as a whole was assembled from those steps. Needs sudo for apt.
set -e
sudo apt-get update
sudo apt-get install -y git cmake g++ make zlib1g-dev libgmp-dev \
  libboost-dev libboost-container-dev libboost-graph-dev libboost-iostreams-dev \
  libboost-program-options-dev libboost-thread-dev
# (libboost-all-dev also works, but pulls in far more and failed once on a stale package index)

git clone --recursive https://github.com/markirch/sat-modulo-symmetries sms
cd sms
git checkout 63958bd                      # tested SMS commit (only a docs change after 464f12f)
git submodule update --init --recursive    # CaDiCaL b023aaf
# The latest Glasgow Subgraph Solver crashes with SMS ("add_directed_edge() on a graph that was
# not declared directed"). Pin the version used by the published 31-vertex computation:
git -C glasgow-subgraph-solver checkout abd331a7ef57c83961323f0e24f95ace04d6e9bf
# SMS links Glasgow statically but not GMP, which Glasgow needs:
sed -i '/libglasgow_subgraphs.a/a link_libraries(gmpxx gmp)' CMakeLists.txt
bash build-and-install.sh -s -l || true    # the script's final pip step fails on Ubuntu 24 (PEP 668)
test -x "$HOME/.local/bin/smsg" || { echo "smsg was not built"; exit 1; }
pip install . --break-system-packages 2>/dev/null || pip install --user .   # installs the pysms module
echo
echo "Done. Add this to your shell before running:"
echo '  export PATH=$HOME/.local/bin:$PATH LD_LIBRARY_PATH=$HOME/.local/lib:/usr/local/lib'
