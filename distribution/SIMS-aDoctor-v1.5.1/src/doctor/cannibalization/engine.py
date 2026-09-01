from __future__ import annotations
from typing import Any

class CannibalizationEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy=policy; self.t=policy['thresholds']

    def assess(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        observation=self._latest_cross_article_observation(medical_record)
        if observation is None:
            return self._follow_up('比較対象となるサイト内記事データがありません。')
        facts=observation.get('facts',{})
        current=dict(facts.get('current_article',{}))
        candidates=list(facts.get('candidate_articles',[]))
        if not candidates:
            return self._no_cannibal(observation,'競合候補記事は確認されませんでした。')
        evaluated=[self._evaluate_candidate(current,item) for item in candidates]
        eligible=[x for x in evaluated if x['shared_query_count']>=self.t['minimum_shared_queries'] and x['candidate_impressions']>=self.t['minimum_candidate_impressions']]
        if not eligible:
            result=self._follow_up('共有クエリ数または候補記事の表示回数が不足しています。')
            result['candidate_articles']=evaluated; result['trace']['cross_article_observation_id']=observation.get('observation_id')
            return result
        strongest=max(eligible,key=self._risk_key)
        winner=strongest.get('winner_query')
        q=strongest['query_overlap']; serp=strongest['serp_overlap']; intent=strongest['intent_similarity']; weak=strongest['weaker_traffic_ratio']
        reasons=[]
        if q>=self.t['merge_query_overlap'] and serp>=self.t['merge_serp_overlap'] and intent>=self.t['same_intent_min'] and weak<=self.t['weak_article_traffic_ratio']:
            classification,confidence,severity='MERGE_CANDIDATE',95,'SEVERE'; reasons.append('検索意図とSERPが強く重複し、片方の記事の流入が著しく弱い状態です。')
        elif q>=self.t['confirmed_query_overlap'] and intent<=self.t['role_separation_intent_max']:
            classification,confidence,severity='ROLE_SEPARATION_RECOMMENDED',91,'MODERATE'; reasons.append('クエリは重複していますが、検索意図の役割を分けられる可能性があります。')
        elif q>=self.t['confirmed_query_overlap'] and serp>=self.t['confirmed_serp_overlap'] and intent>=self.t['same_intent_min']:
            classification,confidence,severity='CONFIRMED_CANNIBALIZATION',93,'SEVERE'; reasons.append('共通クエリ、SERP、検索意図の重複が同時に確認されました。')
        elif q>=self.t['possible_query_overlap']:
            classification,confidence,severity='POSSIBLE_CANNIBALIZATION',82,'MODERATE'; reasons.append('一定の共通クエリがあり、追加観察が必要です。')
        else:
            classification,confidence,severity='NO_CANNIBALIZATION',85,'INFO'; reasons.append('重大な記事間競合は確認されませんでした。')
        if winner: reasons.append('主要流入クエリを保護し、統合や役割変更は慎重に判断します。')
        reasons += [f"最大共通クエリ率は{round(q*100,1)}%です。",f"SERP一致率は{round(serp*100,1)}%です。",f"検索意図一致率は{round(intent*100,1)}%です。"]
        return {'classification':classification,'confidence':confidence,'severity':severity,'reasons':reasons,
          'metrics':{'candidate_count':len(candidates),'eligible_candidate_count':len(eligible),'maximum_query_overlap':round(q,4),'maximum_serp_overlap':round(serp,4),'maximum_intent_similarity':round(intent,4),'weakest_traffic_ratio':round(weak,4)},
          'protections':{'winner_query_protected':bool(winner),'winner_query':winner,'merge_allowed':False,'delete_allowed':False,'redirect_allowed':False,'noindex_allowed':False},
          'candidate_articles':evaluated,
          'trace':{'cross_article_observation_id':observation.get('observation_id'),'finding_ids':[x['finding_id'] for x in medical_record.get('findings',[]) if x.get('finding_id')]}}

    def _evaluate_candidate(self,current,candidate):
        shared=set(candidate.get('shared_queries',[])); current_queries=set(current.get('queries',[])); candidate_queries=set(candidate.get('queries',[]))
        union=current_queries|candidate_queries
        query_overlap=float(candidate.get('query_overlap',len(shared)/len(union) if union else 0))
        current_traffic=float(current.get('clicks',0))+float(current.get('impressions',0))*0.01
        candidate_traffic=float(candidate.get('clicks',0))+float(candidate.get('impressions',0))*0.01
        stronger=max(current_traffic,candidate_traffic); weaker=min(current_traffic,candidate_traffic)
        ratio=weaker/stronger if stronger>0 else 1.0
        winner=self._winner_query(current.get('query_metrics',[])+candidate.get('query_metrics',[]))
        return {'article_id':candidate.get('article_id'),'article_url':candidate.get('article_url'),'article_title':candidate.get('article_title'),'shared_query_count':len(shared),'query_overlap':round(query_overlap,4),'serp_overlap':round(float(candidate.get('serp_overlap',0)),4),'intent_similarity':round(float(candidate.get('intent_similarity',0)),4),'current_position':current.get('position'),'candidate_position':candidate.get('position'),'current_ctr':current.get('ctr'),'candidate_ctr':candidate.get('ctr'),'current_clicks':float(current.get('clicks',0)),'candidate_clicks':float(candidate.get('clicks',0)),'candidate_impressions':float(candidate.get('impressions',0)),'weaker_traffic_ratio':round(ratio,4),'winner_query':winner}

    def _winner_query(self,items):
        total=sum(float(x.get('clicks',0)) for x in items)
        if total<=0:return None
        winner=max(items,key=lambda x:float(x.get('clicks',0)),default=None); share=float(winner.get('clicks',0))/total if winner else 0
        return {'query':winner.get('query'),'click_share':round(share,4),'clicks':float(winner.get('clicks',0))} if winner and share>=self.t['winner_query_click_share'] else None
    @staticmethod
    def _risk_key(x): return (x['query_overlap']+x['serp_overlap']+x['intent_similarity'], -x['weaker_traffic_ratio'])
    @staticmethod
    def _latest_cross_article_observation(record):
        xs=[x for x in record.get('observations',[]) if x.get('observation_type') in {'CROSS_ARTICLE','CANNIBALIZATION_INPUT'}]
        return xs[-1] if xs else None
    def _no_cannibal(self,obs,reason):
        return {'classification':'NO_CANNIBALIZATION','confidence':80,'severity':'INFO','reasons':[reason],'metrics':{'candidate_count':0,'eligible_candidate_count':0,'maximum_query_overlap':0.0,'maximum_serp_overlap':0.0,'maximum_intent_similarity':0.0,'weakest_traffic_ratio':1.0},'protections':{'winner_query_protected':False,'winner_query':None,'merge_allowed':False,'delete_allowed':False,'redirect_allowed':False,'noindex_allowed':False},'candidate_articles':[],'trace':{'cross_article_observation_id':obs.get('observation_id'),'finding_ids':[]}}
    def _follow_up(self,reason):
        return {'classification':'FOLLOW_UP_REQUIRED','confidence':45,'severity':'INFO','reasons':[reason],'metrics':{'candidate_count':0,'eligible_candidate_count':0,'maximum_query_overlap':0.0,'maximum_serp_overlap':0.0,'maximum_intent_similarity':0.0,'weakest_traffic_ratio':1.0},'protections':{'winner_query_protected':False,'winner_query':None,'merge_allowed':False,'delete_allowed':False,'redirect_allowed':False,'noindex_allowed':False},'candidate_articles':[],'trace':{'cross_article_observation_id':None,'finding_ids':[]}}
