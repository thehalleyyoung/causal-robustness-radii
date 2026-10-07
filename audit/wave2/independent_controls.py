"""Independent centered statsmodels oracle and brute-deletion cut oracle."""
import itertools,json,pathlib
import numpy as np
import statsmodels.api as sm
from causalcert.radius.estimate import ols_hc3
from causalcert.radius.search import min_directed_cut
from causalcert.radius.graph import is_acyclic

def reachable(edges,x,y):
    seen={x}
    while True:
        expanded=seen|{v for u,v in edges if u in seen}
        if expanded==seen:return y in seen
        seen=expanded

def cuts():
    checked=0; failures=[]; pairs=list(itertools.combinations(range(4),2))
    for states in itertools.product(range(3),repeat=6):
        edges=[(u,v) if s==1 else (v,u) for (u,v),s in zip(pairs,states) if s]
        pa=[sum(1<<u for u,v in edges if v==k) for k in range(4)]
        if not is_acyclic(pa):continue
        for x,y in itertools.permutations(range(4),2):
            remaining=[i for i in range(4) if i not in (x,y)]
            for flags in itertools.product([False,True],repeat=2):
                observed={x,y}|{i for i,f in zip(remaining,flags) if f}
                editable=[e for e in edges if set(e)<=observed]
                expected=None
                for k in range(len(editable)+1):
                    if any(not reachable(set(edges)-set(c),x,y) for c in itertools.combinations(editable,k)):
                        expected=k;break
                got=min_directed_cut(pa,x,y,sum(1<<v for v in observed));checked+=1
                if got!=expected:failures.append([edges,x,y,sorted(observed),expected,got])
    return {'checked':checked,'failures':failures}

def regressions():
    rows=[]
    for seed in range(8200,8212):
        rng=np.random.default_rng(seed);x=rng.normal(size=120);z=rng.normal(size=120);y=2*x+z+rng.normal(size=120)
        for offset in [0.,1e14]:
            X=np.column_stack([np.ones(120),x+offset,z-offset]);centered=X.copy();centered[:,1:]-=X[0,1:]
            ref=sm.OLS(y,centered).fit(cov_type='HC3');b,se=ols_hc3(y,X)
            rows.append({'seed':seed,'offset':offset,'beta_error':float(abs(b[1]-ref.params[1])),'se_error':float(abs(se[1]-ref.bse[1]))})
    negative={}
    for name,X in {'duplicated':np.column_stack([np.ones(120),x,x]),'unit_leverage':np.column_stack([np.ones(120),np.arange(120)==1])}.items():
        try:ols_hc3(y,X);negative[name]='UNEXPECTED_ACCEPT'
        except ValueError as e:negative[name]=str(e)
    return {'rows':rows,'negative_controls':negative}
if __name__=='__main__':
    out={'regressions':regressions(),'cuts':cuts()}
    pathlib.Path(__file__).with_name('independent-controls.json').write_text(json.dumps(out,indent=2)+'\n')
    assert not out['cuts']['failures']
    assert max(r['beta_error'] for r in out['regressions']['rows'])<1e-6
    assert max(r['se_error'] for r in out['regressions']['rows'])<1e-6
    assert 'UNEXPECTED_ACCEPT' not in out['regressions']['negative_controls'].values()
    print(json.dumps({'cut_checks':out['cuts']['checked'],'cut_failures':len(out['cuts']['failures']),'max_beta_error':max(r['beta_error'] for r in out['regressions']['rows']),'max_se_error':max(r['se_error'] for r in out['regressions']['rows']),'negative_controls':out['regressions']['negative_controls']},indent=2))
