"""Prospective grid-information learners; importing defines functions only.

No fitting, generation, numerical imports, I/O, or model loading occurs here.
Privileged conditional means enter only the separately labelled capacity test.
Every selection uses validation data; this module has no test-data argument.
"""


def contexts(seed, n):
    """Return new contexts, noisy observations, and diagnostic-only true means.

    AR noise starts at zero before t=0. Its innovations have zero mean and unit
    variance, uniform[-sqrt(3),sqrt(3)], with rho=.6 and multiplier sqrt(1-rho²).
    Consequently E[U|X] equals conditional_U exactly, with no clipping bias.
    The deterministic mean exceeds46 and absolute noise is below32; neither
    observations nor means need clipping. Columns x5..x7 are irrelevant.
    """
    import numpy as np
    if type(seed) is not int or seed < 0 or type(n) is not int or n <= 0:
        raise ValueError('Nonnegative integer seed and positive integer n required')
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1., 1., size=(n, 8))
    t = np.arange(30, dtype=float)
    angle = 2*np.pi*t/24.
    conditional = 90.*(1. + .25*x[:, 0, None]*np.sin(angle)
        + .20*x[:, 1, None]*np.cos(angle)
        + .15*(x[:, 2]*x[:, 3])[:, None]*np.sin(2*angle)
        + .10*(x[:, 4]**2-1/3)[:, None]*np.cos(2*angle))
    innovations = rng.uniform(-np.sqrt(3.), np.sqrt(3.), size=(n, 30))
    ar = np.zeros((n, 30), dtype=float)
    previous = np.zeros(n, dtype=float)
    for period in range(30):
        previous = .6*previous + np.sqrt(1-.6**2)*innovations[:, period]
        ar[:, period] = previous
    observed = conditional + 9.*ar
    if not np.isfinite(observed).all() or np.any(observed < 0):
        raise ValueError('Bounded DGP nonnegativity assertion failed; no clipping')
    return dict(X=x.tolist(), U=observed.tolist(), conditional_U=conditional.tolist())


def _arrays(x, u=None):
    import numpy as np
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] != 8 or not len(x) or not np.isfinite(x).all():
        raise ValueError('Finite nonempty n-by-8 context matrix required')
    if u is None:
        return x
    u = np.asarray(u, dtype=float)
    if u.shape != (len(x), 30) or not np.isfinite(u).all() or np.any(u < 0):
        raise ValueError('Finite nonnegative n-by-30 U matrix required')
    return x, u


def _groups(groups, n):
    if groups is None:
        return list(range(n))
    groups = list(groups)
    if len(groups) != n:
        raise ValueError('One physical group identifier per context row required')
    try:
        for group in groups:
            hash(group)
    except TypeError as exc:
        raise ValueError('Group identifiers must be hashable') from exc
    return groups


def _weights(groups):
    import numpy as np
    counts = {}
    for group in groups:
        counts[group] = counts.get(group, 0)+1
    return np.asarray([1./(len(counts)*counts[group]) for group in groups], dtype=float)


def _features(x, model):
    import numpy as np
    z = (x-model['x_mean'])/model['x_scale']
    if model.get('blind', False):
        z = np.zeros_like(z)
    if model.get('quadratic', False):
        z = np.column_stack([z]+[z[:, i]*z[:, j] for i in range(8) for j in range(i, 8)])
    return z


def _forecast(model, x):
    import numpy as np
    z = _features(x, model)
    if model['kind'] == 'mean':
        return np.broadcast_to(model['mean_u'], (len(x), 30)).copy()
    if model['kind'] == 'torch':
        import torch
        model['model'].eval()
        with torch.no_grad():
            return 90.*model['model'](torch.as_tensor(z, dtype=torch.float64)).cpu().numpy()
    return 90.*np.asarray(model['model'].predict(z), dtype=float)


def predict(fitted, X, method=None):
    """Forecast U in [0,200]; fitted may be one model or fit_models' bundle."""
    import numpy as np
    x = _arrays(X)
    if 'models' in fitted:
        if method not in fitted['models']:
            raise ValueError('An exact fitted method name is required')
        fitted = fitted['models'][method]
    elif method is not None:
        raise ValueError('method applies only to a fitted model bundle')
    result = _forecast(fitted, x)
    if result.shape != (len(x), 30) or not np.isfinite(result).all():
        raise ValueError('Nonfinite or misaligned forecast')
    return np.clip(result, 0., 200.)


def _banks(banks, n):
    """Banks are row-aligned lists of finite nonnegative candidate load matrices.

    Each row may be a matrix or {'loads': matrix}; shape is candidates-by-30.
    Candidate order and duplicates are intentionally retained, without dedup or
    dominance filtering. Physical provenance/admission belongs to the caller's
    paid bank construction; this module generates no routes, reads no bank files,
    and supplies no independent physical admission claim.
    """
    import numpy as np
    if banks is None or len(banks) != n:
        raise ValueError('One caller-admitted physical candidate bank per row required')
    result = []
    for bank in banks:
        loads = np.asarray(bank['loads'] if isinstance(bank, dict) else bank, dtype=float)
        if (loads.ndim != 2 or loads.shape[1] != 30 or not len(loads)
                or not np.isfinite(loads).all() or np.any(loads < 0)):
            raise ValueError('Finite nonnegative nonempty candidate-by-30 loads required')
        result.append(loads)
    return result


def _costs(u, loads):
    import numpy as np
    return (.2+u/900.) @ loads.T + .5/900.*np.sum(loads*loads, axis=1)


def _metrics(predicted, observed, weights, banks):
    import numpy as np
    predicted = np.clip(predicted, 0., 200.)
    if not np.isfinite(predicted).all():
        raise ValueError('Nonfinite validation forecast')
    mse = float(np.sum(weights*np.mean(((predicted-observed)/90.)**2, axis=1)))
    selected_cost, oracle_cost = [], []
    for p, u, loads in zip(predicted, observed, banks):
        truth = _costs(u, loads)
        chosen = int(np.argmin(_costs(p, loads)))
        selected_cost.append(float(truth[chosen]))
        oracle_cost.append(float(np.min(truth)))
    decision = float(np.dot(weights, selected_cost))
    return dict(normalized_mse=mse, normalized_rmse=mse**.5,
                decision_cost=decision, finite_bank_regret=decision-float(np.dot(weights, oracle_cost)))


def _mse(predicted, observed, weights):
    import numpy as np
    predicted = np.clip(predicted,0.,200.)
    if not np.isfinite(predicted).all():
        raise ValueError('Nonfinite forecast in MSE selection')
    return float(np.sum(weights*np.mean(((predicted-observed)/90.)**2,axis=1)))


def _torch_setup():
    import torch
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)


def _network(width, seed):
    import torch
    torch.manual_seed(seed)
    return torch.nn.Sequential(torch.nn.Linear(8, width), torch.nn.ReLU(),
        torch.nn.Linear(width, width), torch.nn.ReLU(), torch.nn.Linear(width, 30)).to(dtype=torch.float64)


def _mse_fit(base, width, seed, tx, tu, vx, vu, tw, vw, train_banks, val_banks):
    import copy
    import time
    import torch
    started = time.perf_counter()
    model = dict(base, kind='torch', model=_network(width, seed))
    x = torch.as_tensor(_features(tx, model), dtype=torch.float64)
    y = torch.as_tensor(tu/90., dtype=torch.float64)
    weights = torch.as_tensor(tw, dtype=torch.float64)
    optimizer = torch.optim.Adam(model['model'].parameters(), lr=.001)
    curve, best, state, selected_epoch, stale = [], float('inf'), None, 0, 0
    for epoch in range(1, 501):
        model['model'].train(); optimizer.zero_grad(set_to_none=True)
        loss = (weights*((model['model'](x)-y)**2).mean(dim=1)).sum()
        if not torch.isfinite(loss):
            raise ValueError('Nonfinite MSE training loss')
        loss.backward(); optimizer.step()
        val = _mse(_forecast(model,vx),vu,vw)
        train = _mse(_forecast(model,tx),tu,tw)
        curve.append(dict(epoch=epoch,training_normalized_mse=train,validation_normalized_mse=val))
        if val < best:
            best, state, selected_epoch, stale = val, copy.deepcopy(model['model'].state_dict()), epoch, 0
        else:
            stale += 1
        if stale >= 60:
            break
    if state is None:
        raise ValueError('No finite complete MSE update')
    model['model'].load_state_dict(state)
    metadata = dict(seed=seed,widths=[width,width],completed_updates=len(curve),selected_epoch=selected_epoch,
        parameter_count=sum(parameter.numel() for parameter in model['model'].parameters()),
        stop_reason='validation_patience60' if stale>=60 else 'update_cap500',loss_curve=curve,
        validation=_metrics(_forecast(model, vx),vu,vw,val_banks),
        training=_metrics(_forecast(model, tx),tu,tw,train_banks))
    metadata['training_seconds'] = time.perf_counter()-started
    return model, metadata


def _dfl_fit(initial, seed, tx, tu, vx, vu, tw, vw, train_banks, val_banks):
    import copy
    import time
    import torch
    started = time.perf_counter()
    torch.manual_seed(seed)
    model = dict(initial, model=copy.deepcopy(initial['model']))
    x = torch.as_tensor(_features(tx, model), dtype=torch.float64)
    y = torch.as_tensor(tu/90., dtype=torch.float64)
    weights = torch.as_tensor(tw, dtype=torch.float64)
    loads = [torch.as_tensor(bank, dtype=torch.float64) for bank in train_banks]
    truth = [torch.as_tensor(_costs(u,bank), dtype=torch.float64) for u,bank in zip(tu,train_banks)]
    optimizer = torch.optim.Adam(model['model'].parameters(), lr=.001)
    curve, best, state, selected_epoch = [], float('inf'), None, 0
    for epoch in range(1, 201):
        tau = 1.-.9*(epoch-1)/199.  # Fixed linear anneal, money units1 -> .1.
        model['model'].train(); optimizer.zero_grad(set_to_none=True)
        normalized = model['model'](x)
        forecast_u = torch.clamp(90.*normalized,min=0.,max=200.)
        objective = normalized.new_zeros(())
        for i, (bank, actual) in enumerate(zip(loads,truth)):
            predicted_cost = (.2+forecast_u[i]/900.) @ bank.T + .5/900.*(bank*bank).sum(dim=1)
            soft_selection = torch.softmax(-predicted_cost/tau, dim=0)
            objective = objective + weights[i]*(soft_selection*actual).sum()
        mse = (weights*((normalized-y)**2).mean(dim=1)).sum()
        loss = objective+.01*mse
        if not torch.isfinite(loss):
            raise ValueError('Nonfinite decision-focused training loss')
        loss.backward(); optimizer.step()
        val = _metrics(_forecast(model,vx),vu,vw,val_banks)
        curve.append(dict(epoch=epoch,tau=tau,training_soft_true_cost=float(objective.detach()),
            training_normalized_mse=float(mse.detach()),training_total_loss=float(loss.detach()),
            validation_decision_cost=val['decision_cost'],validation_normalized_mse=val['normalized_mse']))
        if val['decision_cost'] < best:
            best, state, selected_epoch = val['decision_cost'], copy.deepcopy(model['model'].state_dict()), epoch
    if state is None:
        raise ValueError('No finite complete decision-focused update')
    model['model'].load_state_dict(state)
    metadata = dict(seed=seed,widths=[128,128],warm_start='same-seed selected large MSE',
        parameter_count=sum(parameter.numel() for parameter in model['model'].parameters()),
        completed_updates=200,selected_epoch=selected_epoch,stop_reason='update_cap200',loss_curve=curve,
        validation=_metrics(_forecast(model,vx),vu,vw,val_banks),
        training=_metrics(_forecast(model,tx),tu,tw,train_banks),
        selection='validation hard finite-bank decision cost; ties earliest epoch',
        training_surrogate='softmax expected observed-U true cost using torch.clamp forecastU[0,200], matching evaluation, plus .01 raw normalized MSE')
    metadata['training_seconds'] = time.perf_counter()-started
    return model, metadata


def _capacity(base, tx, conditional_u, groups):
    """Diagnostic only: privileged noiseless labels; never promote this model.

    Success means interpolation of this small fixed subset, not universal model
    adequacy, identifiability, generalization, or a useful downstream advantage.
    """
    import torch
    x = tx[:32]; target = conditional_u[:32]/90.
    model = dict(base,kind='torch',blind=False,model=_network(256,17))
    inputs = torch.as_tensor(_features(x,model),dtype=torch.float64)
    truth = torch.as_tensor(target,dtype=torch.float64)
    weights = torch.as_tensor(_weights(groups[:32]),dtype=torch.float64)
    optimizer = torch.optim.Adam(model['model'].parameters(),lr=.001)
    curve, passed = [], False
    for update in range(1,1501):
        model['model'].train(); optimizer.zero_grad(set_to_none=True)
        loss = (weights*((model['model'](inputs)-truth)**2).mean(dim=1)).sum()
        if not torch.isfinite(loss):
            return dict(passed=False,completed_updates=update-1,loss_curve=curve,
                        failure='nonfinite diagnostic loss',privileged_labels=True)
        loss.backward(); optimizer.step()
        with torch.no_grad():
            measured = (weights*((model['model'](inputs)-truth)**2).mean(dim=1)).sum().sqrt()
            if not torch.isfinite(measured):
                return dict(passed=False,completed_updates=update,loss_curve=curve,
                    failure='nonfinite diagnostic post-update RMSE',privileged_labels=True)
            rmse = float(measured)
        curve.append(dict(update=update,normalized_train_rmse=rmse))
        if rmse <= .01:
            passed=True; break
    return dict(passed=passed,completed_updates=len(curve),loss_curve=curve,
        final_normalized_train_rmse=curve[-1]['normalized_train_rmse'],required_rmse=.01,
        rows=32,widths=[256,256],seed=17,max_updates=1500,privileged_labels=True,
        included_in_main_model_selection=False,
        failure=None if passed else 'capacity/optimization diagnostic threshold not reached; no adequacy claim')


def fit_models(trainX, trainU, valX, valU, *, train_banks, val_banks,
               conditional_trainU, train_groups=None, val_groups=None):
    """Fit the fixed menu using caller-paid new physical banks, never test data.

    Outputs contain model objects plus metadata, not a disk serialization format.
    Selection: forecast MSE for all forecast learners; hard decision cost for DFL.
    The blind pair zeros every observable standardized context, deliberately
    testing the value of context information while retaining shared bank policy.
    Group identifiers must keep all aliases/variants of a physical group together.
    """
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.multioutput import MultiOutputRegressor
    tx,tu=_arrays(trainX,trainU); vx,vu=_arrays(valX,valU)
    _,conditional=_arrays(tx,conditional_trainU)
    if len(tx)<32:
        raise ValueError('At least32 training rows required by frozen capacity diagnostic')
    tg=_groups(train_groups,len(tx)); vg=_groups(val_groups,len(vx))
    if train_groups is not None and val_groups is not None and set(tg)&set(vg):
        raise ValueError('Training/validation physical group overlap')
    tw=_weights(tg); vw=_weights(vg)
    tb=_banks(train_banks,len(tx)); vb=_banks(val_banks,len(vx))
    mean=np.sum(tw[:,None]*tx,axis=0)
    scale=np.sqrt(np.sum(tw[:,None]*(tx-mean)**2,axis=0)); scale[scale<1e-12]=1.
    base=dict(x_mean=mean,x_scale=scale,target_scale=90.,blind=False,quadratic=False)
    models={}; candidates={}; selections={}
    models['mean']=dict(base,kind='mean',mean_u=np.sum(tw[:,None]*tu,axis=0))
    candidates['mean']=[dict(validation=_metrics(_forecast(models['mean'],vx),vu,vw,vb))]
    selections['mean']=dict(candidate_index=0,criterion='training group-weighted mean; no selection')
    for name,quadratic in (('ridge',False),('quadratic_ridge',True)):
        rows=[]; fitted=[]
        for alpha in (.01,1.,100.):
            model=dict(base,kind='sklearn',quadratic=quadratic,model=Ridge(alpha=alpha))
            model['model'].fit(_features(tx,model),tu/90.,sample_weight=tw*len(tx))
            fitted.append(model); rows.append(dict(alpha=alpha,
                validation=_metrics(_forecast(model,vx),vu,vw,vb),training=_metrics(_forecast(model,tx),tu,tw,tb)))
        winner=min(range(len(rows)),key=lambda i:(rows[i]['validation']['normalized_mse'],i))
        models[name]=fitted[winner]; candidates[name]=rows
        selections[name]=dict(candidate_index=winner,criterion='validation normalized MSE; ties menu order')
    rows=[]; fitted=[]
    for depth in (3,6):
        estimator=HistGradientBoostingRegressor(max_depth=depth,max_leaf_nodes=None,max_iter=200,
            learning_rate=.05,l2_regularization=1.,early_stopping=False,random_state=17)
        model=dict(base,kind='sklearn',model=MultiOutputRegressor(estimator,n_jobs=1))
        model['model'].fit(_features(tx,model),tu/90.,sample_weight=tw*len(tx))
        fitted.append(model); rows.append(dict(max_depth=depth,max_iter=200,learning_rate=.05,l2=1.,
            validation=_metrics(_forecast(model,vx),vu,vw,vb),training=_metrics(_forecast(model,tx),tu,tw,tb)))
    winner=min(range(len(rows)),key=lambda i:(rows[i]['validation']['normalized_mse'],i))
    models['boosted_trees']=fitted[winner]; candidates['boosted_trees']=rows
    selections['boosted_trees']=dict(candidate_index=winner,criterion='validation normalized MSE; ties depth order')
    _torch_setup()
    seed_models={}
    for name,width,blind in (('neural_small_mse',32,False),('neural_large_mse',128,False),('blind_large_mse',128,True)):
        rows=[]; fitted=[]
        for seed in (17,29):
            model,row=_mse_fit(dict(base,blind=blind),width,seed,tx,tu,vx,vu,tw,vw,tb,vb)
            rows.append(row); fitted.append(model); seed_models[name,seed]=model
        winner=min(range(len(rows)),key=lambda i:(rows[i]['validation']['normalized_mse'],i))
        models[name]=fitted[winner]; candidates[name]=rows
        selections[name]=dict(candidate_index=winner,seed=rows[winner]['seed'],criterion='validation normalized MSE; ties seed order')
    for name,initial_name in (('neural_large_dfl','neural_large_mse'),('blind_large_dfl','blind_large_mse')):
        rows=[]; fitted=[]
        for seed in (17,29):
            model,row=_dfl_fit(seed_models[initial_name,seed],seed,tx,tu,vx,vu,tw,vw,tb,vb)
            rows.append(row); fitted.append(model)
        winner=min(range(len(rows)),key=lambda i:(rows[i]['validation']['decision_cost'],i))
        models[name]=fitted[winner]; candidates[name]=rows
        selections[name]=dict(candidate_index=winner,seed=rows[winner]['seed'],criterion='validation hard decision cost; ties seed order')
    diagnostic=_capacity(base,tx,conditional,tg)
    return dict(models=models,candidates=candidates,selection=selections,capacity_diagnostic=diagnostic,
        policy=dict(target='realized U; conditional_U diagnostic only',target_scale=90.,
            weighting='each physical group equally; each row within group equally; each period equally',
            forecast_clip=[0.,200.],validation_only_selection=True,test_data_used=False,
            decision_cost='(.2+U/900) dot L + .5/900 sum(L²)',
            known_b=1/900,known_a=.2,df_temperature='linear1.0->0.1 over200 updates',
            expected_conditional_noise_normalized_mse=.01*sum(1-.6**(2*(period+1)) for period in range(30))/30.,
            noise_floor_scope='Known-DGP expected out-of-sample conditional-mean risk with zero-start AR; not a finite-training lower bound',
            diagnostic_scope='first32 training rows; noiseless privileged labels; no universal generalization claim'))
