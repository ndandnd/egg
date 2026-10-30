# Native v5 fixture-freeze receipt review

Independent metadata/hash review passed. This review used compact receipts and lock metadata; fixture bytes were hashed without displaying or interpreting their contents. No runtime imports, tests, native jobs, signals, or fixture generation were performed.

The freeze supervisor reports `passed=true`, worker return code 0, no primary/monitor/secondary errors, and no source changes. PGID 43396 is confirmed absent, its leader reaped, with no survivors or cleanup/probe errors. Elapsed allocation was 1.3812452927231789 s, peak sampled tree RSS 216268800 bytes, and supervisor CPU 0.339091 s. Complete accounting carries 721.7986948764081 s forward to **723.5190311691314 s**; no additional administration charge is required.

All 179 attempt source hashes, 145 lock source hashes, five receipt artifacts, lock assets, check evidence, and inherited evidence matched. The passing source-bound check is `freeze-v2-checks/attempt01` (135 tests). Attempt SHA-256 is `a08d7f0491738df99f8bd1221d064e1422baeae01d8058f2f3c2b1ceb1a3708d`; lock SHA-256 is `2c91d5137100d9831ce37126f5e63942b6688f0efd95dcdf6c5ddf6e887e8214`. The GRB library hash remains `54c2ca41a9a9c80b4dd27df09e6b8a73abbb18de90e95198ae676611910dca96`.

Both fixtures exactly match v4 hashes: 50997/40 is `c6eca9f94f1190d9736f6ac3732b6dbd395578e723b7907ff2cee179cbd10429`; 50999/80 is `cc7f146c0c84fbb1efe6e5ac1cf5e654e73c3e93aa98d1914a68b09183f0e928`. Identity, full/restricted movement IDs, and market metadata are unchanged (movement counts 1435/488 and 6213/1981). Task list, split, and environment are unchanged: exactly eight tasks, original cases and clocks, one worker/thread, 5 GiB, and approved 1800/1620/180 s cumulative limits.

No compact receipt or lock prerequisite blocker remains for the parent's conditional launch under the v5 protocol, stopping at the first failure. This establishes freeze integrity and cleanup only; native qualification, 80-trip timeliness, and learned-method benefit remain unproved. Historical v4 failure remains unchanged.
