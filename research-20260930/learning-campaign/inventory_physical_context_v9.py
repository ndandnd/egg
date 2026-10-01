"""Fit-fold-only input inventory; no model loader, labels, fitting or solver."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import time
import traceback

import numpy as np

from egglab import native_recharge as nr
from egglab import physical_learning_cases as registry
from egglab import physical_context_features_v9 as features

ROOT = Path(__file__).resolve().parents[2]
POLICY = "physical-context-v9-fit-only-range-inventory-v1"
PINS = {
    32: ("20260930-route-pool32-v1", "35251cbc8c81787263b51f6259820299e862fba97efa6b8d09c9b1f9c8211842"),
    64: ("20260930-route-pool64-v3", "64791ec33307612bd8ad7f3c2396c42e0ffdc44717d2c865fe268f61bdab5eb0"),
    128: ("20260930-route-pool128-v3", "d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d"),
}
FROZEN_FEATURE_SHA = "a83c629902a6e704010b02c0c3b22e0ebbdb99351126af20fa78055ee208c33f"
SOURCE_FILES = (
    "research-20260930/learning-campaign/inventory_physical_context_v9.py",
    "src/tests/test_physical_context_v9_inventory.py",
    "src/egglab/physical_context_features_v9.py", "src/egglab/learned_proposals.py",
    "src/egglab/native_recharge.py", "src/egglab/native_hull.py",
    "src/egglab/physical_learning_cases.py", "src/egglab/physical_route_model_v2.py",
    "src/egglab/physical_route_model_v3.py",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_PROTOCOL.md",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_REVIEW.md",
)
UNITS = (
    *("indicator",)*4, *("horizon_fraction",)*3, *("battery_upper_fraction",)*3,
    "horizon_fraction", *("currency_per_kwh",)*4, "indicator", "constant_one",
    "kWh", "kWh", *("dimensionless",)*9, "connector_hours", "kW", "kW",
    "kWh", "dimensionless", "candidate_count", *("currency_per_kwh_squared",)*4,
)
CASE_REGISTRY_FIELDS = frozenset(("base_id", "base_group", "split", "generator", "case_identity"))
SOURCE_REGISTRY_FIELDS = frozenset(("base_id", "base_group", "source", "case_identity", "market_identity"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for piece in iter(lambda: stream.read(1024*1024), b""):
            digest.update(piece)
    return digest.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def registry_projection(text, allowed):
    """Decode top-level allowed scalars only; skip excluded JSON values lexically.

    The hash-pinned pool embeds plans. This small balanced-value skipper does not
    decode excluded strings, arrays or objects, including case payloads. It is
    not a general JSON loader: allowed registry values must be JSON scalars.
    """
    decoder = json.JSONDecoder()
    position = 0
    length = len(text)
    result, seen = {}, set()

    def space(index):
        while index < length and text[index].isspace(): index += 1
        return index

    def string_end(index):
        index += 1
        while index < length:
            if text[index] == "\\": index += 2
            elif text[index] == '"': return index+1
            else: index += 1
        raise ValueError("Unterminated registry JSON string")

    def value_end(index):
        if text[index] == '"': return string_end(index)
        if text[index] in "[{":
            stack = [text[index]]; index += 1
            while index < length and stack:
                character = text[index]
                if character == '"': index = string_end(index); continue
                if character in "[{": stack.append(character)
                elif character in "]}":
                    if not stack or (stack.pop(), character) not in (("[", "]"), ("{", "}")):
                        raise ValueError("Unbalanced registry JSON value")
                index += 1
            if stack: raise ValueError("Unterminated registry JSON value")
            return index
        while index < length and text[index] not in ",}" and not text[index].isspace(): index += 1
        return index

    position = space(position)
    if position >= length or text[position] != "{": raise ValueError("Registry row requires object")
    position = space(position+1)
    while position < length and text[position] != "}":
        if text[position] != '"': raise ValueError("Registry key requires string")
        end = string_end(position)
        key = decoder.decode(text[position:end])
        if key in seen: raise ValueError("Duplicate registry key")
        seen.add(key); position = space(end)
        if position >= length or text[position] != ":": raise ValueError("Registry key requires colon")
        position = space(position+1)
        if position >= length: raise ValueError("Missing registry value")
        end = value_end(position)
        if key in allowed:
            value = decoder.decode(text[position:end])
            if isinstance(value, (list, dict)): raise ValueError("Registry field must be scalar")
            result[key] = value
        position = space(end)
        if position < length and text[position] == ",":
            position = space(position+1)
            if position >= length or text[position] == "}": raise ValueError("Trailing registry comma")
        elif position >= length or text[position] != "}": raise ValueError("Registry separator missing")
    if position >= length or text[position] != "}" or space(position+1) != length:
        raise ValueError("Registry row has trailing or incomplete content")
    return result


def projected_rows(path, allowed):
    with Path(path).open() as stream:
        return [registry_projection(line, allowed) for line in stream if line.strip()]


def partitions(prefix, fold):
    """Exact predefined v2(32)/v3(64,128) partition, with no model import."""
    if prefix not in PINS or type(fold) is not int or fold not in range(4):
        raise ValueError("Only predefined registry prefixes/folds")
    ordered = tuple(f"physical_v2_s{i}" for i in range(10000, 10000+prefix))
    outer = tuple(group for index, group in enumerate(ordered) if index % 4 == fold)
    training = tuple(group for group in ordered if group not in outer)
    inner = training[2::6]
    fit = tuple(group for group in training if group not in inner)
    assert (len(fit), len(inner), len(outer)) == (5*prefix//8, prefix//8, prefix//4)
    return fit, inner, outer


def load_input_registry(pool, prefix, expected_sha):
    pool = Path(pool)
    if sha(pool/"pool_manifest.json") != expected_sha: raise ValueError("Pinned manifest changed")
    manifest = json.loads((pool/"pool_manifest.json").read_text())
    expected_policy = ("physical-route-source-pool32-admitted-train-v1" if prefix == 32
                       else "physical-route-source-pool-prefix-v3")
    if (manifest.get("policy") != expected_policy or manifest.get("train_only") is not True
            or manifest.get("base_ids") != list(range(10000,10000+prefix))):
        raise ValueError("Not exact TRAIN input registry")
    hashes = {name: sha(pool/name) for name in ("cases.jsonl", "source_inputs.jsonl")}
    if hashes != manifest.get("output_hashes"): raise ValueError("Pinned input table changed")
    cases = projected_rows(pool/"cases.jsonl", CASE_REGISTRY_FIELDS)
    sources = projected_rows(pool/"source_inputs.jsonl", SOURCE_REGISTRY_FIELDS)
    expected_groups = {f"physical_v2_s{i}" for i in range(10000,10000+prefix)}
    by_group = {}
    for row in cases:
        group, base_id = row.get("base_group"), row.get("base_id")
        if (type(base_id) is not int or base_id not in range(10000,10000+prefix)
                or group != f"physical_v2_s{base_id}" or group in by_group
                or row.get("split") != "train" or row.get("generator") != registry.GENERATOR):
            raise ValueError("Invalid case registry header")
        by_group[group] = row
    if set(by_group) != expected_groups: raise ValueError("Incomplete case registry")
    pairs = {}
    for row in sources:
        pair = row.get("base_group"), row.get("source")
        if (pair[0] not in by_group or pair[1] not in ("source0", "source1") or pair in pairs
                or row.get("base_id") != by_group[pair[0]]["base_id"]
                or row.get("case_identity") != by_group[pair[0]]["case_identity"]):
            raise ValueError("Invalid source registry header")
        pairs[pair] = row
    intended = {(group,source) for group in expected_groups for source in ("source0", "source1")}
    # This is registry presence only. No plan, label, outcome or censor reason is read.
    missing = {("physical_v2_s10037", "source0")} if prefix >= 64 else set()
    if set(pairs) != intended-missing: raise ValueError("Observed source registry changed")
    return {"cases":by_group, "sources":pairs, "manifest_sha256":expected_sha,
            "table_sha256":hashes, "case_headers_sha256":canonical_sha(cases),
            "source_headers_sha256":canonical_sha(sources)}


def column_stats(values, weights, ratios=False):
    values = np.asarray(values, dtype=float); weights = np.asarray(weights, dtype=float)
    finite = np.isfinite(values)
    output = {"rows":len(values), "missing_nan":int(np.isnan(values).sum()),
              "nonfinite_infinity":int(np.isinf(values).sum()), "finite_rows":int(finite.sum())}
    if not finite.any():
        return {**output, "minimum":None, "maximum":None, "range":None,
                "mean":None, "variance_population":None, "std_population":None,
                "equal_group_source_edge_mean":None, "equal_group_source_edge_variance":None,
                "constant_exact":None, "near_constant_roundoff":None, "unique_count":0,
                "maximum_absolute":None, "negative_rows":0, "ratio_gt_one_rows":0 if ratios else None}
    x = values[finite]; w = weights[finite]; w = w/w.sum()
    mean = float(np.mean(x)); weighted_mean = float(np.dot(w,x))
    lo, hi = float(x.min()), float(x.max()); spread = hi-lo
    if spread == 0.:
        mean = weighted_mean = lo
        variance = weighted_variance = 0.
    else:
        variance = float(np.mean((x-mean)**2))
        weighted_variance = float(np.dot(w,(x-weighted_mean)**2))
    return {**output, "minimum":lo, "maximum":hi, "range":spread, "mean":mean,
            "variance_population":variance, "std_population":float(np.sqrt(variance)),
            "equal_group_source_edge_mean":weighted_mean,
            "equal_group_source_edge_variance":weighted_variance,
            "constant_exact":spread == 0.,
            "near_constant_roundoff":0. < spread <= 1e-12*max(1.,abs(lo),abs(hi)),
            "unique_count":int(len(np.unique(x))), "maximum_absolute":max(abs(lo),abs(hi)),
            "negative_rows":int((x<0).sum()), "ratio_gt_one_rows":int((x>1).sum()) if ratios else None}


def inventory_fold(inputs, prefix, fold, *, case_factory=registry.make_case,
                   market_factory=registry.market, featurizer=features.edge_features):
    fit, inner, outer = partitions(prefix,fold)
    samples, identities, matrices, masks = [], [], [], []
    for group in fit:  # Strict gate precedes case/market construction or feature extraction.
        header = inputs["cases"][group]
        case = case_factory(header["base_id"])
        if case.identity() != header["case_identity"]: raise ValueError("Regenerated fit case identity changed")
        window = np.asarray([nr._window(case,movement) is not None
                             and nr._window(case,movement)[1]>nr._window(case,movement)[0]
                             for movement in case.movements], dtype=bool)
        for source in ("source0", "source1"):
            row = inputs["sources"].get((group,source))
            if row is None: continue
            market = market_factory(case,source)
            if market.identity() != row["market_identity"]: raise ValueError("Regenerated fit market identity changed")
            x = featurizer(case,market)
            if x.shape != (len(case.movements),len(features.FEATURES)) or not np.isfinite(x).all():
                raise ValueError("Invalid fit-only feature matrix")
            matrices.append(x); masks.append(window)
            samples.append({"group":group,"source":source,"movement_rows":len(x),
                            "positive_window_rows":int(window.sum())})
            identities.append({"group":group,"source":source,"case_identity":case.identity(),
                "market_identity":market.identity(), "feature_matrix_sha256":canonical_sha(x.tolist())})
    if not samples or {row["group"] for row in samples} != set(fit): raise ValueError("Fit input support missing")
    source_counts = Counter(row["group"] for row in samples)
    weights = np.concatenate([np.full(row["movement_rows"],1/(len(fit)*source_counts[row["group"]]*row["movement_rows"]))
                              for row in samples])
    x = np.concatenate(matrices); positive = np.concatenate(masks)
    columns = []
    for index,(name,unit) in enumerate(zip(features.FEATURES,UNITS)):
        ratios = "over_usable" in name or name == "window_isolated_span_ratio"
        columns.append({"column":index,"name":name,"unit":unit,
            "all_fit_movement_rows":column_stats(x[:,index],weights,ratios),
            "conditional_positive_window_rows":column_stats(x[positive,index],weights[positive],ratios)})
    return {"prefix":prefix,"fold":fold,"fit_groups":fit,
        "excluded_inner_groups_identifiers_only":inner,"excluded_outer_groups_identifiers_only":outer,
        "fit_groups_sha256":canonical_sha(fit),"fit_source_samples":samples,
        "input_identities":identities,"fit_input_projection_sha256":canonical_sha(identities),
        "fit_group_count":len(fit),"fit_source_count":len(samples),"movement_rows":len(x),
        "positive_window_rows":int(positive.sum()),"feature_matrix_sha256":canonical_sha(x.tolist()),
        "feature_extraction_scope":"fit groups only in this prefix/fold; no inner/outer feature construction",
        "weight_sum":float(weights.sum()),"columns":columns}


def run(root=ROOT):
    started = time.monotonic(); root = Path(root)
    source_hashes = {name:sha(root/name) for name in SOURCE_FILES}
    if source_hashes["src/egglab/physical_context_features_v9.py"] != FROZEN_FEATURE_SHA:
        raise ValueError("Reviewed v9 featurizer changed")
    if len(UNITS) != len(features.FEATURES): raise ValueError("Feature units dimension changed")
    folds, evidence = [], []
    for prefix,(directory,manifest_sha) in PINS.items():
        inputs = load_input_registry(root/"result/physical_learning"/directory,prefix,manifest_sha)
        evidence.append({"prefix":prefix,"pool_path":"result/physical_learning/"+directory,
            **{key:inputs[key] for key in ("manifest_sha256","table_sha256","case_headers_sha256","source_headers_sha256")}})
        for fold in range(4):
            fold_started = time.monotonic()
            row = inventory_fold(inputs,prefix,fold)
            row["elapsed_seconds"] = time.monotonic()-fold_started
            folds.append(row)
    return {"policy":POLICY,"passed":True,"features":features.FEATURES,"units":UNITS,
        "source_hashes":source_hashes,"input_pools":evidence,"folds":folds,
        "runtime":{"python":platform.python_version(),"numpy":np.__version__,"platform":platform.platform()},
        "scope":{"case_payloads":"never decoded; fit cases regenerated and registry identity verified",
            "source_plan_label_outcome_values":"never decoded; excluded values only lexically skipped / byte-hashed",
            "case_source_headers":"identity/registry whitelist only, no numeric feature use of IDs",
            "source_markets":"source0/source1 regenerated only after per-fold FIT gating and identity verified",
            "normalization":"none fitted; raw input statistics only","target_features_read":False,
            "inner_outer_features_constructed":False,"reserved_data_read":False,"fit_or_solver_run":False},
        "definitions":{"variance":"population ddof0; descriptive only",
            "weighted":"equal group, then observed source, then movement; conditional weights renormalized on support",
            "near_constant":"nonzero range<=1e-12*max(1,abs(min),abs(max)); descriptive roundoff flag, not a training tolerance",
            "positive_window":"declared depot/pullin window duration>0, regardless of power or realized use",
            "ratio_gt_one":"unclipped usable-span stress/capacity ratios, not feasibility labels"},
        "elapsed_seconds":time.monotonic()-started}


def save_new(path,value):
    with Path(path).open("x") as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False); stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json")
    args = parser.parse_args(argv)
    if args.output.exists(): raise ValueError("Immutable inventory output already exists")
    started = time.monotonic()
    try:
        result=run(); result["total_execution_seconds"]=time.monotonic()-started
        save_new(args.output,result)
        print(json.dumps({"output":str(args.output),"sha256":sha(args.output),"elapsed_seconds":time.monotonic()-started,
                          "folds":len(result["folds"]),"passed":True},sort_keys=True))
    except BaseException as exc:
        failure=args.output.with_name(args.output.stem+f".failure.{time.time_ns()}.json")
        save_new(failure,{"policy":POLICY,"passed":False,"type":type(exc).__name__,"message":str(exc),
                          "traceback":traceback.format_exc(),"elapsed_seconds":time.monotonic()-started})
        raise


if __name__ == "__main__": main()
