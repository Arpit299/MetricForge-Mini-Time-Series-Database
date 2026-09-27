import argparse,json,math,os,sys,tempfile
from bisect import bisect_left,bisect_right
from collections import deque
from dataclasses import dataclass
from json import JSONDecodeError
from heapq import nsmallest
@dataclass(slots=True)
class Point:
    timestamp:float
    value:float
class Series:
    def __init__(self,name):
        self.name=name
        self.timestamps=[]
        self.values=[]
    def insert(self,timestamp,value):
        i=bisect_left(self.timestamps,timestamp)
        if i<len(self.timestamps) and self.timestamps[i]==timestamp:
            self.values[i]=value
            return False
        self.timestamps.insert(i,timestamp)
        self.values.insert(i,value)
        return True
    def range_points(self,start=None,end=None):
        left=0 if start is None else bisect_left(self.timestamps,start)
        right=len(self.timestamps) if end is None else bisect_right(self.timestamps,end)
        return [Point(self.timestamps[i],self.values[i]) for i in range(left,right)]
    def latest(self):
        if not self.timestamps:
            return None
        return Point(self.timestamps[-1],self.values[-1])
    def count(self):
        return len(self.timestamps)
    def stats(self,start=None,end=None):
        points=self.range_points(start,end)
        if not points:
            return {'count':0,'min':None,'max':None,'avg':None,'sum':0.0,'p50':None,'p95':None}
        values=[p.value for p in points]
        ordered=sorted(values)
        def pct(q):
            if len(ordered)==1:
                return ordered[0]
            pos=(len(ordered)-1)*q
            lo=math.floor(pos)
            hi=math.ceil(pos)
            if lo==hi:
                return ordered[lo]
            return ordered[lo]+(ordered[hi]-ordered[lo])*(pos-lo)
        total=sum(values)
        return {'count':len(values),'min':min(values),'max':max(values),'avg':total/len(values),'sum':total,'p50':pct(0.5),'p95':pct(0.95)}
    def rolling_mean(self,window,start=None,end=None):
        if window<=0:
            raise ValueError('window must be positive')
        points=self.range_points(start,end)
        q=deque()
        total=0.0
        result=[]
        for point in points:
            q.append(point.value)
            total+=point.value
            if len(q)>window:
                total-=q.popleft()
            result.append(Point(point.timestamp,total/len(q)))
        return result
    def bucket(self,start,end,bucket_size):
        if bucket_size<=0:
            raise ValueError('bucket size must be positive')
        points=self.range_points(start,end)
        buckets={}
        for point in points:
            index=math.floor((point.timestamp-start)/bucket_size)
            buckets.setdefault(index,[]).append(point.value)
        result=[]
        for index in sorted(buckets):
            values=buckets[index]
            bucket_start=start+index*bucket_size
            result.append({'start':bucket_start,'end':bucket_start+bucket_size,'count':len(values),'min':min(values),'max':max(values),'avg':sum(values)/len(values)})
        return result
class MetricForge:
    def __init__(self):
        self.series={}
    def create(self,name):
        if name not in self.series:
            self.series[name]=Series(name)
    def insert(self,name,timestamp,value):
        if not math.isfinite(timestamp) or not math.isfinite(value):
            raise ValueError('timestamp and value must be finite numbers')
        self.create(name)
        return self.series[name].insert(float(timestamp),float(value))
    def bulk_insert(self,name,points):
        added=0
        updated=0
        for timestamp,value in points:
            if self.insert(name,timestamp,value):
                added+=1
            else:
                updated+=1
        return {'added':added,'updated':updated}
    def query(self,name,start=None,end=None):
        if name not in self.series:
            raise KeyError(f'metric not found: {name}')
        return self.series[name].range_points(start,end)
    def stats(self,name,start=None,end=None):
        if name not in self.series:
            raise KeyError(f'metric not found: {name}')
        return self.series[name].stats(start,end)
    def latest(self,name):
        if name not in self.series:
            raise KeyError(f'metric not found: {name}')
        return self.series[name].latest()
    def rolling_mean(self,name,window,start=None,end=None):
        if name not in self.series:
            raise KeyError(f'metric not found: {name}')
        return self.series[name].rolling_mean(window,start,end)
    def bucket(self,name,start,end,bucket_size):
        if name not in self.series:
            raise KeyError(f'metric not found: {name}')
        return self.series[name].bucket(start,end,bucket_size)
    def top_k(self,name,k,start=None,end=None,largest=True):
        if name not in self.series:
            raise KeyError(f'metric not found: {name}')
        points=self.series[name].range_points(start,end)
        if k<=0:
            return []
        if largest:
            return sorted(points,key=lambda p:p.value,reverse=True)[:k]
        return nsmallest(k,points,key=lambda p:p.value)
    def list_metrics(self):
        return [{'name':name,'count':series.count(),'latest':None if series.latest() is None else {'timestamp':series.latest().timestamp,'value':series.latest().value}} for name,series in sorted(self.series.items())]
    def to_dict(self):
        return {'metrics':{name:[{'timestamp':t,'value':v} for t,v in zip(series.timestamps,series.values)] for name,series in self.series.items()}}
    @classmethod
    def from_dict(cls,data):
        db=cls()
        for name,points in data.get('metrics',{}).items():
            db.bulk_insert(name,[(float(p['timestamp']),float(p['value'])) for p in points])
        return db
    def save(self,path):
        with open(path,'w',encoding='utf-8') as f:
            json.dump(self.to_dict(),f,ensure_ascii=False,separators=(',',':'))
    @classmethod
    def load(cls,path):
        with open(path,'r',encoding='utf-8') as f:
            return cls.from_dict(json.load(f))
def point_dict(point):
    return None if point is None else {'timestamp':point.timestamp,'value':point.value}
def parse_points_csv(path):
    import csv
    rows=[]
    with open(path,newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if not {'timestamp','value'}.issubset(reader.fieldnames or set()):
            raise ValueError('CSV must contain timestamp and value columns')
        for row in reader:
            rows.append((float(row['timestamp']),float(row['value'])))
    return rows
def demo():
    db=MetricForge()
    db.bulk_insert('cpu',[(1,21),(2,25),(3,24),(4,31),(5,37),(6,33),(7,29)])
    db.bulk_insert('memory',[(1,48),(2,51),(3,49),(4,58),(5,61)])
    print(json.dumps({'metrics':db.list_metrics(),'cpu_stats':db.stats('cpu'),'cpu_query':[point_dict(p) for p in db.query('cpu',2,5)],'cpu_rolling_mean':[point_dict(p) for p in db.rolling_mean('cpu',3)],'cpu_buckets':db.bucket('cpu',1,7,2),'cpu_top3':[point_dict(p) for p in db.top_k('cpu',3)]},indent=2))
def self_test():
    db=MetricForge()
    assert db.bulk_insert('cpu',[(5,50),(1,10),(3,30),(2,20),(4,40)])=={'added':5,'updated':0}
    assert db.insert('cpu',3,35) is False
    assert [p.timestamp for p in db.query('cpu')]==[1.0,2.0,3.0,4.0,5.0]
    assert [p.value for p in db.query('cpu')]==[10.0,20.0,35.0,40.0,50.0]
    stats=db.stats('cpu')
    assert stats['count']==5 and stats['min']==10.0 and stats['max']==50.0 and stats['avg']==31.0 and stats['sum']==155.0
    assert db.latest('cpu').value==50.0
    assert [round(p.value,2) for p in db.rolling_mean('cpu',2)]==[10.0,15.0,27.5,37.5,45.0]
    buckets=db.bucket('cpu',1,5,2)
    assert [b['count'] for b in buckets]==[2,2,1]
    assert [p.value for p in db.top_k('cpu',2)]==[50.0,40.0]
    assert [p.value for p in db.top_k('cpu',2,largest=False)]==[10.0,20.0]
    with tempfile.TemporaryDirectory() as d:
        path=os.path.join(d,'metricforge.json')
        db.save(path)
        restored=MetricForge.load(path)
        assert restored.to_dict()==db.to_dict()
        csv_path=os.path.join(d,'points.csv')
        with open(csv_path,'w',encoding='utf-8',newline='') as f:
            f.write('timestamp,value\n6,60\n7,70\n')
        loaded=parse_points_csv(csv_path)
        assert loaded==[(6.0,60.0),(7.0,70.0)]
    assert db.list_metrics()[0]['name']=='cpu'
    print('SELF-TEST: PASS')
def build_parser():
    parser=argparse.ArgumentParser(prog='metricforge',description='Mini time-series database')
    parser.add_argument('--self-test',action='store_true')
    sub=parser.add_subparsers(dest='command')
    p=sub.add_parser('insert')
    p.add_argument('metric')
    p.add_argument('timestamp',type=float)
    p.add_argument('value',type=float)
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('import-csv')
    p.add_argument('metric')
    p.add_argument('csv_file')
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('query')
    p.add_argument('metric')
    p.add_argument('--start',type=float)
    p.add_argument('--end',type=float)
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('stats')
    p.add_argument('metric')
    p.add_argument('--start',type=float)
    p.add_argument('--end',type=float)
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('rolling')
    p.add_argument('metric')
    p.add_argument('window',type=int)
    p.add_argument('--start',type=float)
    p.add_argument('--end',type=float)
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('bucket')
    p.add_argument('metric')
    p.add_argument('start',type=float)
    p.add_argument('end',type=float)
    p.add_argument('bucket_size',type=float)
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('latest')
    p.add_argument('metric')
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('top')
    p.add_argument('metric')
    p.add_argument('k',type=int)
    p.add_argument('--smallest',action='store_true')
    p.add_argument('--start',type=float)
    p.add_argument('--end',type=float)
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('list')
    p.add_argument('--db',default='metricforge.json')
    p=sub.add_parser('demo')
    sub.add_parser('self-test')
    return parser
def load_db(path):
    return MetricForge.load(path) if os.path.exists(path) else MetricForge()
def main(argv=None):
    parser=build_parser()
    args=parser.parse_args(argv)
    if args.self_test or args.command is None or args.command=='self-test':
        self_test()
        return 0
    if args.command=='demo':
        demo()
        return 0
    if args.command=='insert':
        db=load_db(args.db)
        inserted=db.insert(args.metric,args.timestamp,args.value)
        db.save(args.db)
        print(json.dumps({'status':'inserted' if inserted else 'updated','metric':args.metric,'timestamp':args.timestamp,'value':args.value}))
        return 0
    if args.command=='import-csv':
        db=load_db(args.db)
        result=db.bulk_insert(args.metric,parse_points_csv(args.csv_file))
        db.save(args.db)
        print(json.dumps(result))
        return 0
    db=load_db(args.db)
    if args.command=='query':
        print(json.dumps([point_dict(p) for p in db.query(args.metric,args.start,args.end)],indent=2))
    elif args.command=='stats':
        print(json.dumps(db.stats(args.metric,args.start,args.end),indent=2))
    elif args.command=='rolling':
        print(json.dumps([point_dict(p) for p in db.rolling_mean(args.metric,args.window,args.start,args.end)],indent=2))
    elif args.command=='bucket':
        print(json.dumps(db.bucket(args.metric,args.start,args.end,args.bucket_size),indent=2))
    elif args.command=='latest':
        print(json.dumps(point_dict(db.latest(args.metric)),indent=2))
    elif args.command=='top':
        print(json.dumps([point_dict(p) for p in db.top_k(args.metric,args.k,args.start,args.end,not args.smallest)],indent=2))
    elif args.command=='list':
        print(json.dumps(db.list_metrics(),indent=2))
    return 0
if __name__=='__main__':
    try:
        sys.exit(main())
    except (ValueError,KeyError,FileNotFoundError,JSONDecodeError) as e:
        print(f'ERROR: {e}',file=sys.stderr)
        sys.exit(1)