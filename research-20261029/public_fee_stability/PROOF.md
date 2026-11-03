# Fee stability from closed certificates

Prospective source-only derivation. No interval has been computed or qualified here.

Fix the original depot15 physical opportunity set, source case, supply objective and all non-fee costs. Its used-bus fee is f0=100. Let N(x) be the number of used buses and J0(x) its original objective. Changing only the fee to f=f0+tau gives Jtau(x)=J0(x)+tau*N(x), without changing feasibility. Restrict f>=0. Retain the already independently proved physical obstruction N>=2.

Let L2 be any qualified lower on the original exactly-two-bus optimum. A qualified original global physical lower L is sufficient: D0>=L implies J0(x)>=L on the two-bus subset. Thus use L2=L if no stronger conditional bound is compactly transferred. Every two-bus physical plan then costs at least L2+2tau, for either sign of tau. Applying this shift to every physical count without conditioning on N=2 would be invalid.

Let A be the exact original affine mandatory-service-energy floor a*service/eta. The original model has nonnegative movement energy and operating costs, nonnegative quadratic supply cost, full terminal replenishment and positive efficiency. Every N>=3 fleet at new fee f>=0 has objective at least N*f+A>=3*f+A. This is a freshly stated algebraic consequence of the admitted original model, not an old global bound shifted by3tau. If only a qualified old three-plus floor L3<=3*f0+A is transferred, then L3+3tau is also valid: Jtau>=3*f+A>=L3+3tau. The direct A form may be stronger. Never allow f<0 in this argument.

Take the two already physically admitted complete plans x0,x1 used in the qualified hull witness and KEEP its original exact weight w in[0,1]. Write Nbar=(1−w)N0+w*N1 and U for its qualified original mixture objective. Feasibility and mean loads remain unchanged; operating cost shifts by tau*Nbar. Therefore CHtau<=U+tau*Nbar. It is unnecessary to repeat a physical replay, re-evaluate the original mixture or optimize w at the new fee.

Consequently a sufficient strict-gap region is exactly the intersection

    tau>=−100,
    (L2−U)+(2−Nbar)*tau>0,
    (300+A−U)+(3−Nbar)*tau>0.

Use L3−U instead of300+A−U if only the weaker qualified L3 is admitted. On this region,

    Dtau−CHtau >= min(L2+2tau, 3*(100+tau)+A)−(U+Nbar*tau)>0.

This covers all physical fleet counts: zero/one are physically impossible, two use their exact-count shift, three and above use the nonnegative-fee floor. Hull components of ANY fleet count remain permitted; a single feasible mixture gives an upper regardless of other hull alternatives. Existing finite fleet caps can only make this conservative argument easier and need not be used.

For each strict affine inequality alpha+beta*tau>0: beta>0 gives the open lower endpoint−alpha/beta; beta<0 gives the open upper endpoint; beta=0 imposes no restriction if alpha>0 and makes the intersection empty otherwise. Intersect with the CLOSED fee boundary tau>=−100. Coincident strict endpoints remain open; a coincident fee boundary is included only if both strict inequalities hold there. Do not accept equality as a positive-gap certificate. Retain the exact rational endpoints and openness flags; decimal displays must be outward and secondary.

At tau0 both inequalities must independently pass using the source-bound exact constants; otherwise report failed transfer/design admission, not a stability result. The strict inequalities and positive original fee imply an open neighborhood of tau0 once valid constants are admitted. The result is a sufficient certificate region for one fixed witness and these lower bounds, not the maximal stability region, an exact phase diagram, calibration, practical significance or robustness to altered physics. Marginal supply prices are unaffected as functions of load; the classical positive-gap implication excludes weak own-load support of the whole-fleet participant throughout the certified region.
