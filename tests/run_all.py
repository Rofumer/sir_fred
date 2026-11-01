"""Run every test; exit code 0 only if all pass."""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ['test_build.py', 'test_window.py', 'test_rope.py', 'test_descend.py',
         'test_listing.py', 'test_pickup.py', 'test_use.py', 'test_coyote.py', 'test_inertia.py',
         'test_sessions.py']

failed = []
for t in TESTS:
    print('=' * 70 + '\n' + t)
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(HERE, t)], cwd=HERE)
    print('-- %s %s (%.1fs)' % (t, 'OK' if r.returncode == 0 else 'FAILED', time.time() - t0))
    if r.returncode:
        failed.append(t)
print('=' * 70)
print('ALL PASSED' if not failed else 'FAILED: ' + ', '.join(failed))
sys.exit(1 if failed else 0)
