#!/opt/conda/bin/python
"""Run a public build/query under the documented filesystem permissions; no scoring."""
import argparse,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("stage",choices=["build","query"])
p.add_argument("--corpus",default="/task/data/corpus")
p.add_argument("--index-dir",default="/work/runtime-check/index")
p.add_argument("--queries")
p.add_argument("--output",default="/work/runtime-check/output/results.jsonl")
a=p.parse_args()
if os.geteuid()!=0:p.error("Invoke this development-only helper from the root development shell.")
index=Path(a.index_dir).resolve();parent=index.parent
if parent in [Path("/"),Path("/tmp"),Path("/app"),Path("/task")]:p.error("Choose an index inside a dedicated check directory, e.g. /work/runtime-check/index.")
parent.mkdir(parents=True,exist_ok=True);os.chown(parent,0,0);parent.chmod(0o711)
index.mkdir(exist_ok=True)
readonly=a.stage=="query"and Path("/task/docs/query-index-readonly").exists()
for f in [index,*index.rglob("*")]:
 if f.is_symlink():continue
 os.chown(f,0 if readonly else 10001,10001)
 f.chmod((0o550 if f.is_dir()else 0o440)if readonly else(0o750 if f.is_dir()else 0o640))
output=Path(a.output).resolve();output.parent.mkdir(parents=True,exist_ok=True);os.chown(output.parent,10001,10001);output.parent.chmod(0o750)
home=output.parent if readonly else index
for name in ["tmp","cache"]:
 f=home/name;f.mkdir(exist_ok=True);os.chown(f,10001,10001);f.chmod(0o700)
# Root can continue editing after the check; the submitted child cannot write /app.
for f in [Path("/app"),*Path("/app").rglob("*")]:
 if f.is_symlink():continue
 executable=bool(f.stat().st_mode&0o111)
 os.chown(f,0,10001);f.chmod(0o550 if f.is_dir()or executable else 0o440)
env={"HOME":str(home),"USER":"submission","LOGNAME":"submission","PATH":"/opt/conda/bin:/usr/local/bin:/usr/bin:/bin","LANG":"C.UTF-8","PYTHONUNBUFFERED":"1","PYTHONDONTWRITEBYTECODE":"1","HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","TMPDIR":str(home/"tmp"),"XDG_CACHE_HOME":str(home/"cache")}
for key in ["LD_LIBRARY_PATH","OPENROUTER_API_KEY","JINA_API_KEY","HTTP_PROXY","HTTPS_PROXY","NO_PROXY","http_proxy","https_proxy","no_proxy"]:
 if os.environ.get(key):env[key]=os.environ[key]
cmd=["/app/build.sh","--corpus",a.corpus,"--index-dir",str(index)]
if a.stage=="query":
 if not a.queries:p.error("--queries is required for query")
 cmd=["/app/run.sh","--index-dir",str(index),"--queries",a.queries,"--output",str(output)]
print("Public permission check: uid=10001, code read-only, index parent not writable; index="+str(index),file=sys.stderr)
raise SystemExit(subprocess.call(["/usr/bin/setpriv","--reuid=10001","--regid=10001","--clear-groups","--no-new-privs",*cmd],cwd="/app",env=env))
