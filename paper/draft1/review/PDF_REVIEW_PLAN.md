# Reviewed PDF build

Publish the revised paper from source c593bc759a72e030956be3c686f958aa02592d6b using the adjacent exact command script. It stages only TeX, bibliography, figures and the committed PDF-only entry point in a fresh directory. Compile once, then render once and visually inspect the resulting pages. Science is not regenerated. Budget 120 CPU seconds and 180 elapsed seconds inclusive, individual tool CPU limit 60 seconds and one configured native thread. The process meter covers staging, build and rendering. RSS is unmeasured for this lightweight artifact operation. Preserve a failed build and its cost without automatic retry. Copy the exact reviewed PDF into the tracked build location on success. From the PR checkout after this control is committed and backed up:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 180; exec @ARGV or die $!;' /bin/sh paper/draft1/review/build_review_copy.sh > /private/tmp/egg-pr57-reviewed-pdf-20261102-a01.stdout 2> /private/tmp/egg-pr57-reviewed-pdf-20261102-a01.time
```
