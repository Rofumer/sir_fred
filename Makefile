# Sir Fred: Quality of Life Edition
# Requires Python 3 with SkoolKit (pip install skoolkit) and sjasmplus
# (tools/bin/sjasmplus.exe is included for Windows; elsewhere put sjasmplus
# into tools/bin/ or PATH). On Windows use mingw32-make or run the python
# commands directly.

PYTHON ?= python

.PHONY: all build unpack test listing clean

all: build

build: build/Sir_Fred_QoL.z80

build/Sir_Fred_QoL.z80: qol.cfg patches/*.asm original/SirFred.z80 tools/build.py tools/z80snap.py
	$(PYTHON) tools/build.py

unpack:
	$(PYTHON) tools/z80snap.py original/SirFred.z80 --ram build/original_ram.bin

listing:
	$(PYTHON) tools/mklisting.py

test: build
	$(PYTHON) tests/run_all.py

clean:
	$(PYTHON) -c "import shutil,glob,os; [shutil.rmtree(p) if os.path.isdir(p) else os.remove(p) for p in glob.glob('build/*')]"
