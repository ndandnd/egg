"""Standard-library supervisor for tiny CPU import/operator/replay stage probes.

Each native-import stage has its own child, so SIGILL and import failures leave
an immutable receipt. This reads no TRAIN bank and takes no optimizer step.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import os
import socket
import subprocess
import sys
import time

STAGES = (
    ("numpy", "import numpy as n; assert n.__version__ == '1.26.4'; print(n.__version__); print(float((n.eye(4) @ n.ones(4)).sum()))"),
    ("scipy", "import scipy; assert scipy.__version__ == '1.13.1'; print(scipy.__version__)"),
    ("sklearn_joblib", "import sklearn, joblib; assert sklearn.__version__ == '1.7.2'; assert joblib.__version__ == '1.5.2'; print(sklearn.__version__, joblib.__version__)"),
    ("torch", "import torch; assert str(torch.__version__) == '2.4.1+cpu'; torch.set_num_threads(1); print(torch.__version__); print(float((torch.eye(4) @ torch.ones(4)).sum()))"),
    ("graph_autograd_roundtrip", """
import tempfile
from pathlib import Path
import numpy as np
import torch
from egglab import physical_route_graph_v6 as g
g.configure_cpu()
sample = {'group':'synthetic', 'source':'source0', 'x':np.arange(68).reshape(4,17)/68,
 'y':np.array([1.,0.,1.,1.]), 'movement_ids':[10,11,12,13], 'trip_count':2,
 'graph':{'src':np.array([0,1,1,2]), 'dst':np.array([1,2,2,3]), 'nodes':4}}
batch = g.batches([sample], np.zeros(17), np.ones(17), labelled=True)
for family in g.FAMILIES:
 torch.manual_seed(17); model = g.GraphScorer(family)
 loss = (torch.nn.functional.binary_cross_entropy_with_logits(model(batch[0]), batch[0]['y'], reduction='none')*batch[0]['w']).sum()
 loss.backward()
 assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
 with tempfile.TemporaryDirectory(prefix='egg-graph-probe-') as folder:
  path = Path(folder)/'model.npz'; g.save_model(model,path)
  assert np.allclose(g.predict(model,batch),g.predict(g.restore_model(path),batch),rtol=0,atol=1e-12)
 print(family,model.parameter_count,float(loss.detach()))
"""),
)


def run(python, output):
    output = Path(output)
    if output.exists():
        raise ValueError("CPU probe receipt is immutable")
    flags = []
    if Path("/proc/cpuinfo").exists():
        flags = [line for line in Path("/proc/cpuinfo").read_text().splitlines()
                 if line.startswith(("model name", "flags"))][:2]
    receipt = {"hostname": socket.gethostname(), "platform": platform.platform(),
        "python": str(python), "cpu_identity": flags, "stages": [], "status": "running"}
    # Append progress via flush/fsync in one exclusive JSONL file:
    # each line is a complete receipt snapshot, preserving evidence of hard kills.
    with output.open("x") as stream:
        def persist():
            stream.write(json.dumps(receipt, sort_keys=True)+"\n"); stream.flush(); os.fsync(stream.fileno())
        persist()
        for name, code in STAGES:
            started = time.monotonic()
            row = {"stage": name, "started_unix": time.time(), "status": "running"}
            receipt["stages"].append(row); persist()
            try:
                child = subprocess.run([str(python), "-c", code], text=True,
                                       capture_output=True, timeout=60)
                row.update({"returncode": child.returncode, "stdout": child.stdout,
                            "stderr": child.stderr, "status": "passed" if child.returncode == 0 else "failed"})
            except subprocess.TimeoutExpired as exc:
                row.update({"status": "failed", "timeout": True, "stdout": str(exc.stdout), "stderr": str(exc.stderr)})
            except OSError as exc:
                row.update({"status": "failed", "type": type(exc).__name__, "message": str(exc)})
            row["elapsed_seconds"] = time.monotonic()-started
            if row["status"] != "passed":
                receipt["status"] = "failed"; persist(); return False
            persist()
        receipt["status"] = "passed"; persist(); return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return 0 if run(args.python, args.output) else 1


if __name__ == "__main__":
    sys.exit(main())
