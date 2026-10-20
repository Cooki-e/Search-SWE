"""MKQA/RocketQA answer-token hit metric, matching the published evaluation."""
import json
import math
import unicodedata
import regex

TOKEN = regex.compile(r"[\p{L}\p{N}\p{M}]+|[^\p{Z}\p{C}]",regex.UNICODE|regex.MULTILINE|regex.IGNORECASE)

def tokens(text):
 return [m.group().lower() for m in TOKEN.finditer(unicodedata.normalize("NFD",text))]

def has_answer(aliases,text):
 words=tokens(text)
 for alias in aliases:
  a=tokens(alias)
  if not a:raise ValueError("Empty answer alias")
  if any(words[i:i+len(a)]==a for i in range(len(words)-len(a)+1)):return True
 return False

def read_jsonl(path):
 with open(path,encoding="utf-8") as f:
  return [json.loads(line) for line in f if line.strip()]

def validate_results(results,queries,corpus_size):
 if len(results)!=len(queries):raise ValueError("Query coverage mismatch")
 for q,row in zip(queries,results):
  if row.get("id")!=q["id"]:raise ValueError("Query ID/order mismatch")
  indices,scores=row.get("indices"),row.get("scores")
  if not isinstance(indices,list) or len(indices)!=min(100,corpus_size):raise ValueError("Expected exactly top100 corpus positions")
  if len(set(indices))!=len(indices) or any(type(i)is not int or i<0 or i>=corpus_size for i in indices):raise ValueError("Invalid/duplicate corpus position")
  if not isinstance(scores,list) or len(scores)!=len(indices) or any(type(v)not in (int,float) or not math.isfinite(v) for v in scores):raise ValueError("Invalid score")
  if any(scores[i]<scores[i+1] or (scores[i]==scores[i+1] and indices[i]>indices[i+1]) for i in range(len(scores)-1)):raise ValueError("Invalid ranking or tie order")

def score_results(corpus,queries,answers,results):
 import pyarrow.parquet as pq
 table=pq.ParquetFile(corpus)
 n=table.metadata.num_rows
 validate_results(results,queries,n)
 labels={str(x["id"]):x["answers"] for x in answers}
 if len(labels)!=len(answers) or set(labels)!={q["id"] for q in queries}:raise ValueError("Answer/query coverage mismatch")
 wanted={i for row in results for i in row["indices"]}
 texts={}
 offset=0
 for batch in table.iter_batches(batch_size=16384,columns=["title","text"]):
  rows=batch.to_pydict()
  for j in range(batch.num_rows):
   pos=offset+j
   if pos in wanted:texts[pos]=rows["title"][j]+"\n"+rows["text"][j]
  offset+=batch.num_rows
 first=[]
 for q,result in zip(queries,results):
  rank=next((i+1 for i,pos in enumerate(result["indices"]) if has_answer(labels[q["id"]],texts[pos])),None)
  first.append({"id":q["id"],"first_answer_rank":rank})
 return {"valid":True,"query_count":len(queries),"corpus_count":n,
  "recall@20":sum(x["first_answer_rank"] is not None and x["first_answer_rank"]<=20 for x in first)/len(first),
  "recall@100":sum(x["first_answer_rank"] is not None for x in first)/len(first),"per_query":first}

def improvement_score(recall,baseline):
 if not all(math.isfinite(x) and 0<=x<=1 for x in [recall,baseline]) or baseline>=1:raise ValueError("Invalid measured baseline or metric")
 return min(1.0,max(0.0,(recall-baseline)/(1.0-baseline)))
