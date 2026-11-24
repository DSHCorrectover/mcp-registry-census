#!/usr/bin/env python3
# census probe v2 python 版：分片前台跑，每片落盘（防504丢数据）
# 方法学不变：每端点1次良性initialize，零注入，12s超时（requests底层默认带）
import json, sys, time, concurrent.futures as cf, urllib.request, urllib.error, ssl

def probe(url):
    r = {"url":url, "ts":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status":0, "sid":False, "auth":"", "serverInfo":False}
    try:
        req = urllib.request.Request(url, method="POST", data=json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcp-session-audit","version":"0.2"}}}).encode(), headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=12) as res:
            r["status"]=res.status
            h=res.headers
            r["sid"]=bool(h.get("Mcp-Session-Id") or h.get("mcp-session-id"))
            r["auth"]=h.get("WWW-Authenticate") or ""
            body=res.read(65536).decode("utf-8","replace")
            try:
                j=json.loads(body); r["serverInfo"]=bool((j.get("result") or {}).get("serverInfo")); r["err"]=(j.get("error") or {}).get("code")
            except Exception: r["note"]=body[:60].replace("\n"," ")
    except urllib.error.HTTPError as e:
        r["status"]=e.code; r["auth"]=(e.headers or {}).get("WWW-Authenticate") or ""
    except Exception as e:
        r["note"]="ERR:"+type(e).__name__
    # verdicts（VECTORS.md 口径）
    r["v1"] = "exposure" if (r["status"]==200 and r["serverInfo"] and not r["auth"]) else ("proper-auth-challenge" if (r["status"]==401 and r["auth"]) else ("no-mcp" if (r["status"] in (200,400,426) and not r["serverInfo"]) else ("ambiguous" if r["status"]==200 else ("blocked-403" if r["status"]==403 else "unreachable"))))
    r["v2"] = "no-session-binding(exposure,MAY)" if (r["status"]==200 and r["serverInfo"] and not r["sid"]) else ("session-bound" if (r["sid"] and r["status"]==200) else "n/a")
    r["v4"] = "rfc9728-posed" if (r["status"]==401 and "resource_metadata" in r["auth"]) else ("401-no-metadata" if r["status"]==401 else "n/a")
    r["v6"] = "violation" if url.startswith("http://") else "https-ok"
    return r

def main(shard):
    urls=open(sys.argv[2] if len(sys.argv)>2 else "endpoints-batch1.txt").read().split()
    chunk=urls[(shard-1)*100 : shard*100]
    out=[]
    with cf.ThreadPoolExecutor(8) as ex:
        for r in ex.map(probe, chunk): out.append(r)
    # 序列化与落盘分离（14:2x 失误修正落地）
    payload=json.dumps({"shard":shard,"method":"one benign initialize per endpoint; no injection","results":out}, ensure_ascii=False, indent=1)
    from collections import defaultdict
    dom403=defaultdict(lambda:[0,0])
    for r in out:
        dom=r["url"].split("/")[2] if "/" in r["url"] else "?"
        dom403[dom][1]+=1
        if r.get("status")==403: dom403[dom][0]+=1
    for r in out:
        if r.get("v1")=="blocked-403":
            dom=r["url"].split("/")[2]
            c,t=dom403[dom]
            r["blocked_source"]="platform-firewall" if t>=3 and c/t>=0.8 else "server-auth"
    pref=sys.argv[3] if len(sys.argv)>3 else ""
    open(f"shards/{pref}shard-{shard:02d}.json","w").write(payload)
    v1={}
    for r in out: v1[r["v1"]]=v1.get(r["v1"],0)+1
    print("shard",shard,"n",len(out),"V1:",v1)

if __name__=="__main__": main(int(sys.argv[1]))
