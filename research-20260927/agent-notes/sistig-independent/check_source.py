"""Independent read-only audit of pinned source rows and derived finite graph; no adapter import."""
import sys, importlib.abc
class NoSolver(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'mip', 'gurobipy'}:
            raise AssertionError('Native optimizer import forbidden in source audit')
sys.meta_path.insert(0, NoSolver())
import io, json, math, hashlib, zipfile, collections
from pathlib import Path
import openpyxl
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[3]
ZIP=ROOT.parent/'research-20260927/agent-notes/public-data/sistig-26088190-v1.zip'
DATA=ROOT/'data/public/sistig_26088190_v1/hildenbrand_native_cases.json'
doc=json.loads(DATA.read_text()); src=doc['source_data']; pre='10__data/20__Selected_transport_operators/020__Hildenbrand/'
checks=collections.Counter()
def ok(test, label):
    if not test: raise AssertionError(label)
    checks[label.split(':')[0]]+=1
def close(a,b,label): ok(abs(a-b)<=1e-10*max(1,abs(a),abs(b)),label)
def stamp(x):
    d,h,m,s=map(int,x.split(':'));return 86400*d+3600*h+60*m+s
def duration(x):
    h,m,s=map(int,x.split(':'));return 3600*h+60*m+s
with zipfile.ZipFile(ZIP) as z:
    raw={}
    for file,key in [('trip_set.xlsx','service_trips'),('bus_stops.xlsx','stops'),('itineraries.xlsx','itineraries'),('bus_route_info.xlsx','routes')]:
        ws=openpyxl.load_workbook(io.BytesIO(z.read(pre+file)),data_only=True,read_only=True).active
        rows=list(ws.values);header=rows[0];raw[key]=[dict(zip(header,r)) for r in rows[1:]]
        ok(len(raw[key])==len(src[key]),'workbook-row-count:'+key)
        for rownum,(r,p) in enumerate(zip(raw[key],src[key]),2):
            ok(any(v is not None for v in r.values()),'no-blank-source-row:'+key)
            ok(p['source_excel_physical_row']==rownum,'physical-row:'+key)
            for k,v in r.items():ok(p[k]==v,'exact-source-field:'+key+':'+k)
    mat=loadmat(io.BytesIO(z.read(pre+'deadhead_trip_matrix.mat')),squeeze_me=True,struct_as_record=False)['deadhead_trip_matrix']
    order=list(map(int,mat.bus_stop_id));ok(order==src['deadhead_stop_order_source'],'matrix-order')
    arcs={}
    for i,o in enumerate(order):
        for j,t in enumerate(order):
            a=src['deadhead_arcs_directed_row_major'][i*len(order)+j]
            ok((a['origin_stop_id'],a['destination_stop_id'])==(o,t),'directed-endpoints')
            for k,n in [('distance_m_source','distances'),('time_sec_source','times'),('height_difference_m_source','height_difference')]:ok(a[k]==float(getattr(mat,n)[i,j]),'exact-matrix-cell:'+k)
            arcs[o,t]=(float(mat.distances[i,j]),int(mat.times[i,j]))
    for p in doc['source_archive_provenance']['member_provenance']:
        b=z.read(p['member_path']);zi=z.getinfo(p['member_path'])
        ok(len(b)==p['uncompressed_bytes'],'member-size');ok(hashlib.sha256(b).hexdigest()==p['sha256'],'member-hash');ok(f'{zi.CRC:08x}'==p['crc32_hex'],'member-crc')
trips={f"H{int(t['trip_id']):04d}":t for t in raw['service_trips']}; depots={s['id'] for s in raw['stops'] if s['b_depot']}; stops={s['id']:s for s in raw['stops']}; its={i['id']:i for i in raw['itineraries']}
for tid,t in trips.items():
    ok(stamp(t['dep_time'])==t['dep_time_sec'] and stamp(t['arr_time'])==t['arr_time_sec'],'trip-time-exact')
    ok(duration(t['duration'])==t['arr_time_sec']-t['dep_time_sec'],'duration-exact')
    for k in ('bus_route_id','dep_stop_id','arr_stop_id','distance','height','num_bus_stops','bool_service'):ok(t[k]==its[t['itinerary_id']][k],'itinerary-consistency:'+k)
    ok(t['dep_stop_id'] not in depots and t['arr_stop_id'] not in depots,'no-service-at-either-depot')
for (o,t),(_,sec) in arcs.items():
    ok(sec%30==0 and sec>=0,'half-minute-directed-time')
    i,j=order.index(o),order.index(t)
    close(float(mat.height_difference[i,j]),stops[t]['height']-stops[o]['height'],'matrix-orientation-height')
def leg(o,t,start,wait_end=None):
    dist,sec=arcs[o,t]
    if wait_end is None:return {'origin':f'P{o}','destination':f'P{t}','depart_min':start/60,'arrive_min':(start+sec)/60,'energy_kwh':.96*dist/1000+16*sec/3600}
    return {'origin':f'P{o}','destination':f'P{o}','depart_min':start/60,'arrive_min':wait_end/60,'energy_kwh':16*(wait_end-start)/3600}
variants=[]
for variant in doc['native_cases']:
    depot=variant['selected_depot_id']; expected={}
    for tid,t in trips.items():
        sd=t['dep_time_sec'];se=t['arr_time_sec'];o=t['dep_stop_id'];e=t['arr_stop_id']
        pd=sd-arcs[depot,o][1]
        if pd>=0:expected['pullout',None,tid]=([leg(depot,o,pd)],None)
        if se+arcs[e,depot][1]<=108000:expected['pullin',tid,None]=([leg(e,depot,se)],None)
        for uid,u in trips.items():
            if tid==uid:continue
            ud=u['dep_time_sec'];a=u['dep_stop_id']; arrive=se+arcs[e,a][1]
            if 0<=se<=arrive<=ud<=108000:
                legs=[leg(e,a,se)]
                if arrive<ud:legs.append(leg(a,a,arrive,ud))
                expected['direct',tid,uid]=(legs,None)
            inward=se+arcs[e,depot][1]; outward=ud-arcs[depot,a][1]
            if 0<=se<=inward<=outward<=ud<=108000:expected['depot',tid,uid]=([leg(e,depot,se),leg(depot,a,outward)],1)
    actual={(m['kind'],m['before'],m['after']):m for m in variant['movement_modes']}
    ok(len(actual)==len(variant['movement_modes']),'unique-mode-keys')
    ok(set(actual)==set(expected),'exact-complete-finite-mode-set')
    prov={p['movement_id']:p for p in variant['movement_provenance']}; waits=0
    for key,(legs,split) in expected.items():
        m=actual[key];ok(m['depot_split']==split,'depot-split');ok(len(m['legs'])==len(legs),'leg-count')
        p=prov[m['id']];ok((p['kind'],p['before'],p['after'])==key,'provenance-mode')
        for got,want,pl in zip(m['legs'],legs,p['legs']):
            for k in ('origin','destination','depart_min','arrive_min'):ok(got[k]==want[k],'exact-native-leg:'+k)
            close(got['energy_kwh'],want['energy_kwh'],'modeled-leg-energy')
            ok(got['depart_min']*60==pl['depart_sec'] and got['arrive_min']*60==pl['arrive_sec'],'provenance-time')
            close(got['energy_kwh'],pl['modeled_energy_kwh'],'provenance-energy')
            if pl['leg_role']=='off_depot_stationary_wait':
                waits+=1;ok(pl['origin_stop_id'] not in depots and pl['destination_stop_id'] not in depots,'wait-not-depot');ok(pl['source_member'] is None and pl['source_distance_m']==0,'wait-not-source-travel')
            else:
                a=arcs[pl['origin_stop_id'],pl['destination_stop_id']];ok(pl['source_distance_m']==a[0] and pl['source_travel_time_sec']==a[1],'provenance-directed-source')
    for q in variant['trips']:
        t=trips[q['native']['id']];energy=1.2*t['distance']+16*(t['arr_time_sec']-t['dep_time_sec'])/3600
        close(q['native']['energy_kwh'],energy,'service-modeled-energy');ok(q['native']['start_min']*60==t['dep_time_sec'] and q['native']['end_min']*60==t['arr_time_sec'],'service-native-time')
    # Independent constructive existence check using original rows and matrix only.
    jobs=[]
    for tid,t in trips.items():
        e=1.2*t['distance']+16*(t['arr_time_sec']-t['dep_time_sec'])/3600
        for o,a in [(depot,t['dep_stop_id']),(t['arr_stop_id'],depot)]:
            di,se=arcs[o,a];e+=.96*di/1000+16*se/3600
        ok(0<e<=400,'constructive-single-bus-energy')
        jobs.append(((t['arr_time_sec']+arcs[t['arr_stop_id'],depot][1])/60,tid,e))
    cursor=0;total=0
    for release,tid,e in sorted(jobs):cursor=max(release,cursor)+e/6;total+=e
    ok(cursor<=1800,'constructive-serial-deadline')
    recorded=variant['preflight_witness_and_dimensions'];close(cursor,recorded['last_terminal_charge_end_min'],'constructive-last-end');close(total,recorded['total_terminal_charge_kwh'],'constructive-energy-total')
    variants.append({'depot':depot,'movement_counts':dict(collections.Counter(k[0] for k in expected)),'movement_legs_checked':sum(len(m['legs']) for m in actual.values()),'off_depot_waits_checked':waits,'independent_constructive_energy_kwh':total,'independent_constructive_final_charge_min':cursor,'candidate_charge_variables_at_max_vehicles':recorded['candidate_charge_variables_at_max_vehicles']})
with ZIP.open('rb') as f:
    h=hashlib.file_digest(f,'sha256').hexdigest()
ok(h==doc['source_archive_provenance']['archive_sha256'],'archive-sha256')
result={'classification':'independent no-solver source, arithmetic and finite-graph audit; not optimization or performance evidence','solver_imported':False,'input_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'source_archive_sha256':h,'checks':dict(checks),'check_count':sum(checks.values()),'service_count':len(trips),'source_departure_range_sec':[min(t['dep_time_sec'] for t in trips.values()),max(t['dep_time_sec'] for t in trips.values())],'latest_arrival_sec':max(t['arr_time_sec'] for t in trips.values()),'matrix_offdiagonal_half_not_whole_minutes':sum(sec%60!=0 for (o,t),(_,sec) in arcs.items() if o!=t),'variants':variants}
out=Path(__file__).with_name('source-check.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
