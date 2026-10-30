# Public-input interpretation

The benchmark uses the pinned Sistig dataset version 1 and its existing intake
fingerprints and attribution. The public paper describes GTFS-derived timetables
and estimates of depot travel from geographic/routing information. Vehicle
energy and charger settings are assumptions in the source study, not observed
operator telemetry. EGG adds its own charging-resource, cost and terminal-inventory
rules; its results are not a reproduction of the source's vehicle-and-crew study.
[Sistig et al., Methods](https://www.nature.com/articles/s44333-025-00030-y).

The Eberbach intake retains the previously declared EGG settings for comparability:
400 kWh usable battery, 360 kW shared depot power, one connector, full initial and
terminal inventory, and a 30-hour horizon. Fixed bus cost 100 and zero travel cost
are stylized EGG choices. These are not claims about installed Eberbach equipment,
observed electricity demand, or monetary operating costs. The source facts and
modeled fields must remain separate in the derived artifact and manuscript.

The paper's Methods page was checked on 28 September 2026. The browser could not
fetch the separate table page or Figshare record/API during this follow-up; this
does not alter the pinned archive or its earlier verified provenance. No new
table-value or license verification is claimed. See the existing
[attribution](../../data/public/sistig_26088190_v1/ATTRIBUTION.md) and
[source-only Eberbach review](../computational-design/EBERBACH_INTAKE_PLAN.md).
No publisher-generated solution, charging schedule, or private GIRO data is used.
