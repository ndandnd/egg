# Attribution and changes

This folder contains an adapted subset of **Dataset for Evaluating Costs and
Operations of Public Bus Fleet Electrification**, by Hubert Maximilian Sistig,
Philipp Sinhuber, Matthias Rogge, and Dirk Uwe Sauer (2025), released on
Figshare under **Creative Commons Attribution 4.0 International (CC BY 4.0)**:

- Dataset DOI: <https://doi.org/10.6084/m9.figshare.26088190.v1>
- Dataset record: <https://figshare.com/articles/dataset/Dataset_for_Evaluating_Costs_and_Operations_of_Public_Bus_Fleet_Electrification/26088190>
- Article: <https://doi.org/10.1038/s44333-025-00030-y>
- License deed: <https://creativecommons.org/licenses/by/4.0/>

Suggested citation: Sistig, Hubert Maximilian; Sinhuber, Philipp; Rogge,
Matthias; Sauer, D.U. (Dirk Uwe) (2025). *Dataset for Evaluating Costs and
Operations of Public Bus Fleet Electrification*. figshare. Dataset.
https://doi.org/10.6084/m9.figshare.26088190.v1.

## Changes made in this adaptation

- Selected all 37 mandatory Hildenbrand service-trip rows and the complete
  directed 5×5 deadhead distance/time/elevation matrix. Source fields, units,
  workbook row numbers, the local intake SHA-256 fingerprint, the Figshare-
  supplied archive MD5, and the SHA-256/CRC of each source member are retained
  in `hildenbrand_native_cases.json`. The SHA-256 fingerprint is not presented
  as a publisher-supplied checksum.
- Generated two explicitly restricted one-depot NativeCase variants, one for
  each of the two source-flagged depots. These are EGG input variants, not the
  source study's original two-depot problem or its published outputs.
- Added modelled service/deadhead energy from the paper's EB-3 Table 2
  assumptions and explicit EGG movement/depot-charging policies. The source
  contains no per-trip energy or observed charging data; those fields remain
  separate and are marked as modelled.
- Retained exact source seconds and directed arc asymmetry. No source archive,
  publisher-generated solution, or raw GitHub code is included here.

The authors and source study are not endorsing EGG or this transformation.
