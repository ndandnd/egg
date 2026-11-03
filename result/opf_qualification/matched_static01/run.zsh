set -eu
ulimit -t 30
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
/usr/local/bin/python3.12 -I -B -c 'import resource,runpy,signal,sys; signal.alarm(57); sys.argv=["src/experiments/audit_static_cone.py","src/runs/opf-inputs-20261103/grid/1-MV-rural--0-sw.zip","src/runs/opf-native-static","result/opf_qualification/matched_static01/result.json"]; runpy.run_path(sys.argv[0],run_name="__main__"); print("observed_peak_rss_bytes",resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)'
