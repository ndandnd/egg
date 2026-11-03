# Input acquisition 01

Model memo 263cf9f4 and literature b201374a precede all runs. The only acquisition source is src/experiments/pin_opf_inputs.py at f9b23e60. Its two API URLs use DE, EUR/MWh, ordered HourUTC and Danish-local request dates 2024-01-17/07-17. The third is the official 1-MV-rural--0-sw CSV download linked by SimBench. No replacement days, grid or URLs. Preserve each successful or failed request and any bytes received. An ordinary failure on one permits the two other prespecified sources. Raw network data are local. No solver or publication. This checks input availability; series reduction, topology conversion, licensing attribution in analysis and fleet deployment remain separate.

Working directory is the OPF worktree. Exact command:

    ulimit -t 25 && /usr/bin/time -p /usr/bin/perl -e 'alarm 110; exec @ARGV' /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -I -B src/experiments/pin_opf_inputs.py /private/tmp/egg-opf-input-20261102-a01

Fresh output directory is required by the script. Allow 30 CPU seconds, 120 elapsed seconds inclusive, no workers or native math solver. At most 1 MB per price response and 100 MB for the grid archive. Store each consumed buffer digest once. Record external POSIX time. No automatic second request to repair a failed input.
