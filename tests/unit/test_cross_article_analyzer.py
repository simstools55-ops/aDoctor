from pathlib import Path
import json

from src.doctor.cross_article import CrossArticleAnalyzer


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/observation/cross_article/cross_article_policy_v1.json")
    .read_text(encoding="utf-8")
)


def test_detects_merge_candidate():
    analyzer = CrossArticleAnalyzer(POLICY)
    primary = {
        "article_id": "A1", "url": "https://example.com/a1",
        "title": "Windows 11 Wi-Fi設定方法", "main_query": "windows 11 wifi 設定",
        "clicks": 100, "impressions": 3000, "ctr": 0.03, "position": 5,
        "queries": [
            {"query": "q1", "impressions": 1000},
            {"query": "q2", "impressions": 800},
            {"query": "q3", "impressions": 500},
            {"query": "q4", "impressions": 300},
        ],
    }
    candidate = {
        "article_id": "A2", "url": "https://example.com/a2",
        "title": "Windows 11のWi-Fi設定方法", "main_query": "windows 11 wifi 設定 方法",
        "clicks": 40, "impressions": 1800, "ctr": 0.02, "position": 8,
        "intent_similarity": 0.9,
        "queries": [
            {"query": "q1", "impressions": 700},
            {"query": "q2", "impressions": 500},
            {"query": "q3", "impressions": 300},
            {"query": "q5", "impressions": 200},
        ],
    }
    result = analyzer.analyze(primary_article=primary, candidate_articles=[candidate])
    assert result[0]["classification"] == "MERGE_CANDIDATE"
    assert result[0]["dominant_article_id"] == "A1"
