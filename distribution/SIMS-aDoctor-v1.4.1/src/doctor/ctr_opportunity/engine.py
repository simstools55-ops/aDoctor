from __future__ import annotations
from datetime import datetime, timezone

class CtrOpportunityEngine:
    def __init__(self, policy):
        self.policy=policy; self.t=policy["thresholds"]

    def assess(self, medical_record):
        obs=self._latest(medical_record)
        if obs is None: return self._insufficient("Search Console観察データがありません。")
        facts=obs.get("facts",{}); m=dict(facts.get("metrics",facts))
        impressions=float(m.get("impressions",0)); clicks=float(m.get("clicks",0)); ctr=float(m.get("ctr",0))
        position=m.get("position"); position=float(position) if position is not None else None
        low=bool(m.get("low_sample",False)); expected=self._expected(position)
        gap=((ctr-expected)/expected) if expected else 0.0
        winner=self._winner(facts); recent=self._recent_title_change(medical_record)
        protections={"winner_query_protected":bool(winner),"winner_query":winner,"recent_title_change":recent,"body_rewrite_allowed":False}
        reasons=[]
        if low or impressions<self.t["minimum_impressions"] or clicks<self.t["minimum_clicks"] or position is None:
            c,conf,sev="INSUFFICIENT_DATA",45,"INFO"; reasons.append("表示回数・クリック数または順位データが不足しています。")
        elif recent:
            c,conf,sev="RECENT_CHANGE_OBSERVATION",78,"INFO"; reasons.append("最近タイトル変更があるため、追加測定を優先します。")
        elif winner:
            c,conf,sev="WINNER_QUERY_PROTECTED",88,"MILD"; reasons.append("主要流入クエリを保護する必要があります。")
        elif not self.t["position_opportunity_min"]<=position<=self.t["position_opportunity_max"]:
            c,conf,sev="HEALTHY_CTR",75,"INFO"; reasons.append("現在順位はCTR改善優先帯ではありません。")
        elif gap<=self.t["critical_ctr_gap_ratio"]:
            c,conf,sev="HIGH_CTR_OPPORTUNITY",94,"SEVERE"; reasons.append("順位に対してCTRが大幅に下回っています。")
        elif gap<=self.t["ctr_gap_ratio"]:
            c,conf,sev="CTR_OPPORTUNITY",88,"MODERATE"; reasons.append("順位に対してCTRが期待値を下回っています。")
        else:
            c,conf,sev="HEALTHY_CTR",82,"INFO"; reasons.append("現在のCTRは順位期待値の範囲内です。")
        if position is not None and position<=self.t["strong_position_max"]: reasons.append("上位表示されているため、タイトル改善の影響が大きい可能性があります。")
        if gap<0: reasons.append(f"順位別期待CTRとの差は{abs(round(gap*100,1))}%です。")
        return {"classification":c,"confidence":conf,"severity":sev,"reasons":reasons,
          "metrics":{"clicks":clicks,"impressions":impressions,"ctr":round(ctr,6),"position":position,"expected_ctr":round(expected,6) if expected is not None else None,"ctr_gap_ratio":round(gap,4),"low_sample":low},
          "protections":protections,
          "trace":{"search_observation_id":obs.get("observation_id"),"finding_ids":[x["finding_id"] for x in medical_record.get("findings",[]) if x.get("finding_id")],"treatment_history_observation_ids":[x["observation_id"] for x in medical_record.get("observations",[]) if x.get("observation_type")=="TREATMENT_HISTORY" and x.get("observation_id")]}}
    def _expected(self,position):
        if position is None:return None
        for x in self.policy["expected_ctr_by_position"]:
            if position<=x["position_max"]: return float(x["expected_ctr"])
    def _winner(self,facts):
        qs=list(facts.get("queries",[])); total=sum(float(x.get("clicks",0)) for x in qs)
        if total<=0:return None
        w=max(qs,key=lambda x:float(x.get("clicks",0)),default=None); share=float(w.get("clicks",0))/total if w else 0
        return {"query":w.get("query"),"click_share":round(share,4),"clicks":float(w.get("clicks",0))} if w and share>=self.t["winner_query_click_share"] else None
    def _recent_title_change(self,record):
        now=datetime.now(timezone.utc)
        for x in reversed(record.get("observations",[])):
            if x.get("observation_type")!="TREATMENT_HISTORY":continue
            tr=x.get("facts",{}).get("treatment",{}); changed=set(tr.get("changed_fields",[]))
            if not changed.intersection({"title","seo_title"}):continue
            raw=tr.get("completed_at")
            if not raw:continue
            try:dt=datetime.fromisoformat(raw)
            except ValueError:continue
            if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
            return (now-dt.astimezone(timezone.utc)).days<self.t["recent_title_change_days"]
        return False
    @staticmethod
    def _latest(record):
        xs=[x for x in record.get("observations",[]) if x.get("observation_type") in {"SEARCH_CONSOLE","SINGLE_CASE_REQUEST","CURRENT_PERFORMANCE"}]
        return xs[-1] if xs else None
    @staticmethod
    def _insufficient(reason):
        return {"classification":"INSUFFICIENT_DATA","confidence":35,"severity":"INFO","reasons":[reason],"metrics":{"clicks":0.0,"impressions":0.0,"ctr":0.0,"position":None,"expected_ctr":None,"ctr_gap_ratio":0.0,"low_sample":True},"protections":{"winner_query_protected":False,"winner_query":None,"recent_title_change":False,"body_rewrite_allowed":False},"trace":{"search_observation_id":None,"finding_ids":[],"treatment_history_observation_ids":[]}}
