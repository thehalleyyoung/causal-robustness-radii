import json, pathlib, math
import numpy as np
from causalcert.radius import analyze
from causalcert.radius.estimate import ols_hc3

def run():
    records=[]
    graph=np.array([[0,1,1],[0,0,1],[0,0,0]],dtype=np.int8)
    for seed in range(8100,8112):
        rng=np.random.default_rng(seed); x=rng.normal(size=120); z=rng.normal(size=120); y=2*x+z+rng.normal(size=120)
        for offset in [0.,1e8]:
            data=np.column_stack([z-offset,x+offset,y]); result=analyze(graph,data,1,2,max_k=1)
            centered=np.column_stack([np.ones(120),data[:,1]-data[:,1].mean(),data[:,0]-data[:,0].mean()])
            beta,se=ols_hc3(y,centered)
            b=result['baseline']
            records.append({'seed':seed,'offset':offset,'baseline':b,'radius_claim':result['radius_claim'],'centered_beta':float(beta[1]),'centered_se':float(se[1])})
    return records
if __name__=='__main__':
    import sys
    def clean(v):
        if isinstance(v,float) and not math.isfinite(v):return None
        if isinstance(v,list):return [clean(x) for x in v]
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
        return v
    pathlib.Path(sys.argv[1]).write_text(json.dumps(clean(run()),indent=2,allow_nan=False)+'\n')
