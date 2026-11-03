#!/bin/bash
# EGG yield rule (user, 1 Oct 2026): EGG yields ONLY to the evspv2g stochastic project,
# i.e. nc437 jobs whose name starts with "v2g" or whose comment is "evspv2g-stochastic".
# If any such job is PENDING or RUNNING: pending EGG (egg-claude-*) arrays -> Nice=10000,
# ArrayTaskThrottle=1. Otherwise: Nice=0, throttle restored to the value in $1 (default 2).
# Only touches egg-claude-* jobs. Prints one status line.
source /etc/profile.d/slurm.sh
T=${1:-2}
v2g=$(squeue -u nc437 -h -t PENDING,RUNNING -o "%j|%k" | awk -F"|" '$1 ~ /^v2g/ || $2 == "evspv2g-stochastic"' | wc -l)
egg=$(squeue -u nc437 -h -t PENDING -o "%A|%j" | awk -F"|" '$2 ~ /^egg-claude-/ {print $1}' | sort -u)
for j in $egg; do
  if [ "$v2g" -gt 0 ]; then scontrol update JobId=$j Nice=10000 ArrayTaskThrottle=1 >/dev/null 2>&1
  else scontrol update JobId=$j Nice=0 ArrayTaskThrottle=$T >/dev/null 2>&1; fi
done
echo "$(date -u +%FT%TZ) v2g_jobs=$v2g egg_pending_arrays=$(echo $egg | wc -w) mode=$([ "$v2g" -gt 0 ] && echo yield || echo normal)"
