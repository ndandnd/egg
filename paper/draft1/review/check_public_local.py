"""Review two authorized, private exports without modifying either original."""
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time


EXPORTS = (
    ("binary", "public_certificate_bundle/attempt01/public-sign-verifier",
     "fa7d7d40c95e185eb4165fe2cb19e14ca0e5cbf63db0321b0c7d4bc5c007c6e7"),
    ("additive", "public_exact_energy_portable/attempt01/bundle",
     "56579467ecbcf5e11479cc5406278c531ba57bb78084750f68c6050dc78d39dc"),
)


def limit_cpu():
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))


def main(archive, destination):
    os.umask(0o077)
    destination.mkdir(exist_ok=False)
    for name, export, digest in EXPORTS:
        start = time.monotonic()
        fresh = destination / name
        shutil.copytree(archive / export, fresh, ignore=shutil.ignore_patterns("verification.json"))
        proc = subprocess.run(
            [sys.executable, "-I", "-S", "-B", "verify.py", "--manifest-sha256",
             digest, "--output", "verification.json"],
            cwd=fresh, timeout=165, preexec_fn=limit_cpu, check=False,
        )
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        print(json.dumps(dict(model=name, exit=proc.returncode, copy_and_check_s=time.monotonic()-start,
                              cumulative_children_peak_rss_bytes_macos=usage.ru_maxrss)), flush=True)
        if proc.returncode or usage.ru_maxrss > 5 * 2**30:
            return 1
        report = json.loads((fresh / "verification.json").read_text())
        if report["status"] != "PASS":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
