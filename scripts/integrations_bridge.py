#!/usr/bin/env python3
"""Scoped Cognee transport. Retrieval is evidence, never authorization."""
import json,re,urllib.error,urllib.parse,urllib.request

class ProviderError(RuntimeError):
    def __init__(self,status,kind="provider"):
        self.status=status
        super().__init__("Cognee request failed: "+kind+"; HTTP "+str(status))

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

class CogneeClient:
    def __init__(self,base_url,key,timeout=45):
        u=urllib.parse.urlsplit(base_url)
        local=u.hostname in ("localhost","127.0.0.1","::1")
        if (u.scheme!="https" and not (u.scheme=="http" and local)) or not u.hostname:
            raise ValueError("HTTPS required except loopback OSS")
        if u.username or u.password or u.query or u.fragment or u.path not in ("","/"):
            raise ValueError("Base URL must contain only scheme and host")
        if not isinstance(key,str) or not key.strip():raise ValueError("COGNEE_API_KEY required")
        self.base_url=base_url.rstrip("/")
        self._key=key
        self.timeout=timeout
        self._opener=urllib.request.build_opener(NoRedirect())
    def __repr__(self):
        return "CogneeClient(base_url="+repr(self.base_url)+", key=REDACTED)"
    def request(self,method,path,payload=None):
        if method not in ("GET","POST") or not path.startswith("/"):
            raise ValueError("Unsupported request")
        body=None if payload is None else json.dumps(payload).encode("utf-8")
        req=urllib.request.Request(self.base_url+path,data=body,method=method,
            headers={"X-Api-Key":self._key,"Accept":"application/json","Content-Type":"application/json"})
        try:
            with self._opener.open(req,timeout=self.timeout) as response:
                raw=response.read(2_000_001)
                if len(raw)>2_000_000:raise ProviderError(response.status,"response_limit")
                return json.loads(raw)
        except urllib.error.HTTPError as error:
            raise ProviderError(error.code) from None
        except (urllib.error.URLError,TimeoutError,OSError):
            raise ProviderError(None,"transport") from None
        except (json.JSONDecodeError,UnicodeDecodeError):
            raise ProviderError(None,"invalid_json") from None
    @staticmethod
    def dataset(name):
        if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}",name):
            raise ValueError("Explicit dataset name required")
        return name
    def add_text(self,texts,dataset):
        name=self.dataset(dataset)
        if not isinstance(texts,list) or not texts or any(not isinstance(x,str) or not x.strip() for x in texts):
            raise ValueError("Nonempty text list required")
        return self.request("POST","/api/v1/add_text",{"textData":texts,"datasetName":name})
    def cognify(self,dataset):
        return self.request("POST","/api/v1/cognify",{"datasets":[self.dataset(dataset)],"runInBackground":True})
    def recall(self,query,dataset):
        name=self.dataset(dataset)
        if not isinstance(query,str) or not query.strip():raise ValueError("Query required")
        return self.request("POST","/api/v1/recall",{"query":query,"datasets":[name],
            "searchType":"CHUNKS_LEXICAL","onlyContext":True,"topK":5})
