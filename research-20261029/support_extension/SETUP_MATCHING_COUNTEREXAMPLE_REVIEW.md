# Positive setup can invalidate minimum-requirement matching replacement

**Verdict: PASS.** The proposed point counterexample is physically correct, including the complete assignment graph, terminal refill and both matchings' nonempty setup-feasible sets. This is an analytical review only: no code, execution, data, imports, tests, hashes or numerical case search.

## Model and exact point

There are two services per simultaneous batch, with a=b=(9/10,2/5), common capacity B=1, unit charging/export efficiency, full initial/final inventory, no other draw, complete2x2 graph, fee1 per bus, early charge/export powers K_c=K_d=1 and terminal power/budget H=2. The common windows and all-bus availability are unchanged. Each NONZERO BUS-SPECIFIC early action occupies connector setup time tau=3/20, then its energy-transfer time at power<=1. Setups occupy the same connector and cannot overlap another action/setup. Terminal charging has no setup under this model. No charging is allowed during services. All actions and setups are sequential; no bus can transfer its battery energy directly to another.

The diagonal perfect matching has high/high requirement4/5 and low/low requirement0, hence R_diag=4/5. The cross matching has two requirements3/10, hence R_cross=3/5. These are the only perfect matchings, so cross is the UNIQUE minimum-r matching of cardinality2.

On the diagonal, buy C=4/5,X=0 on the high bus in ONE early action. Its early time is3/20+4/5=19/20<=1. That bus starts the window at1/10, reaches9/10, consumes its B service9/10 and reaches0. The low bus starts the window at3/5, receives no early energy and consumes2/5 to reach1/5. Terminal purchases1 and4/5 restore full inventory; they take total time(9/5)/2=9/10<=1 on the shared terminal connector. Nonnegative service consumption and monotone charge actions preserve all intermediate SOC bounds. Thus

    (C,X,E,L,c)=(4/5,0,4/5,9/5,2)

is a fully feasible whole-plan point.

## Why no minimum-r substitute exists

For the cross matching, each of its TWO buses must gain at least3/10 battery energy before its B service. At the target X=0 there can be no export action, since directional energies are nonnegative. Each bus therefore requires a distinct nonzero charge action. At total C=4/5 the shared connector needs at least4/5 energy-transfer time plus two setups, giving

    4/5+2*(3/20)=11/10>1.

Splitting actions only adds setup, lower power only adds duration, and terminal energy cannot repair a preterminal service inventory violation. A single action cannot recharge two buses under the declared per-bus action law. Because efficiencies are unit and the model projects net loads, any candidate with E=4/5 but X>0 has C=4/5+X and even L unchanged; it has still more energy-transfer time and cannot rescue the point. Thus the failure holds in the LOAD–COST projection too, not only when the original C/X coordinates are held fixed.

The cross matching itself remains feasible: purchase3/10 on each bus, using3/5+2*(3/20)=9/10 early time, then terminal purchase2 at power2. It is the target point that is lost, not an infeasible matching selected by a defective algorithm. A plan with fewer matching edges needs at least3 counted buses and c>=3, so it cannot reproduce c=2. Paid idle/extra buses cannot reproduce that cost either. The complete graph and all fleet alternatives therefore close the simple omitted-assignment workaround.

## Optional monotone linear-query contrast

The error can also be observed without a negative price or nonconvex objective. Take F(E,L)=E+2L, which is convex and coordinatewise increasing. Unit efficiency/full refill imply E+L=S=13/5 for every physical plan, so c+F=c+26/5−E.

Any schedule has E<=C+X<=17/20 whenever an early action occurs, and E=0 otherwise: at least one setup consumes3/20 of the unit window. The diagonal attains E=17/20 in one high-bus charge, with terminal L=7/4<=2. Its objective is127/20. A two-bus cross schedule requires at least two actions, so E<=7/10; it attains that bound by purchases3/10 and2/5, followed by terminal purchase19/10. Its best objective is13/2. Any plan with c>=3 has objective at least147/20>13/2, using the same universal early bound. Therefore

    true whole-plan minimum =127/20,
    minimum-r-per-cardinality restricted minimum =13/2,
    loss from that restriction =3/20.

This uses exact endpoint/time inequalities, not an optimization run. Because the query is linear in the complete load/cost coordinates, physical and hull minimum values coincide for the TRUE model; it is NOT a positive support-gap example. It diagnoses the incorrect assignment reduction under setup.

## Consequence and limits

Ignoring setup still gives the valid minimum-r OUTER polygons, and the conservative action-count/occupancy INNER sets remain valid sufficient constructions. Neither inclusion is contradicted. What fails is an exact common-setup theorem that replaces every same-cardinality matching by its minimum-r matching: recharge concentration across buses matters once each active bus/action costs connector time. Both matchings can be feasible and compatibility complete while that statistic is insufficient.

The result applies to the explicitly stated bus-specific per-action setup law, not merely a fee for changing the connector's charge/export direction. It does not address a model permitting simultaneous bus charging, overlapping setup, service retiming, altered connector power, or station battery transfers. It is a negative scope result, not a new empirical benchmark, generic hardness result, positive-gap discovery or learning case. No existing source or manuscript was changed.
