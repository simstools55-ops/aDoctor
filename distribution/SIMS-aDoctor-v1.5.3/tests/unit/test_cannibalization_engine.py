from pathlib import Path
import json
from src.doctor.cannibalization import CannibalizationEngine
ROOT=Path(__file__).resolve().parents[2]
def load():return json.loads((ROOT/'tests/fixtures/cannibalization/medical_record.json').read_text())
def policy():return json.loads((ROOT/'knowledge/cannibalization/cannibalization_policy_v1.json').read_text())
def test_merge_candidate():
 r=CannibalizationEngine(policy()).assess(load()); assert r['classification']=='MERGE_CANDIDATE'; assert r['protections']['merge_allowed'] is False
def test_role_separation():
 d=load(); d['observations'][0]['facts']['candidate_articles'][0]['intent_similarity']=0.40
 assert CannibalizationEngine(policy()).assess(d)['classification']=='ROLE_SEPARATION_RECOMMENDED'
def test_possible():
 d=load(); c=d['observations'][0]['facts']['candidate_articles'][0]; c['query_overlap']=0.48;c['serp_overlap']=0.2;c['intent_similarity']=0.65
 assert CannibalizationEngine(policy()).assess(d)['classification']=='POSSIBLE_CANNIBALIZATION'
def test_followup_without_candidates():
 d=load();d['observations'][0]['facts']['candidate_articles']=[{'article_id':'A2','impressions':10,'shared_queries':['q']}]
 assert CannibalizationEngine(policy()).assess(d)['classification']=='FOLLOW_UP_REQUIRED'
