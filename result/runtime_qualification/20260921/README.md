# Qualified local runtime

Official PyPI MIP 1.17.6 / CBCBox 2.929 runs on native arm64 Python 3.12.2.
MIP 2.0.0 / CBCBox 2.935 failed native loading with macOS CODESIGNING Invalid Page,
including after a clean reinstall. The exact failing dependency/page remains
unknown. No signature, quarantine or system security setting was changed.

`qualified-environment.lock.txt` records the successful environment.
`qualification-final.json` preserves LP objective 1, binary MILP objective/bound
3 and INFEASIBLE control success after NumPy installation, one thread under
a 30-second process cap. `qualification-final-worker.py` is the checked control
implementation; `qualified-wheel-verification.json` matches the two solver
wheels to official PyPI hashes. Original local paths are historical provenance.

This does not establish equivalence to another solver/version, operational
physical correctness, or a global dependency recommendation. The separate
physical and reuse qualifications provide model-level checks.

Official versions: https://pypi.org/project/mip/1.17.6/ and
https://pypi.org/project/cbcbox/2.929/ .
