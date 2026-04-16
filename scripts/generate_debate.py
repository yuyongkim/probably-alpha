"""Generate trader debate JSON from current market data.

Usage:
    python scripts/generate_debate.py              # latest date
    python scripts/generate_debate.py 20260325     # specific date

Collects dashboard data from the API and builds a structured debate
payload that the trader-debate.html page can display.
The analysis is rule-based (no LLM), but designed to be replaced with
LLM-generated content when pasted from Claude Code.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

API_BASE = "http://127.0.0.1:8000"


def fetch(endpoint: str) -> dict | list:
    url = f"{API_BASE}{endpoint}"
    with urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_market_data(date_dir: str | None = None) -> dict:
    query = f"?date_dir={date_dir}" if date_dir else ""
    try:
        dashboard = fetch(f"/api/dashboard{query}")
    except URLError:
        from sepa.api.services_dashboard import dashboard_payload
        dashboard = dashboard_payload(date_dir)

    sectors = dashboard.get("sectors", {}).get("items", [])
    stocks = dashboard.get("stocks", {}).get("items", [])
    recs = dashboard.get("recommendations", {}).get("items", [])
    summary = dashboard.get("summary", {})
    briefing = dashboard.get("briefing", {}).get("items", {})

    confirmed = [s for s in sectors if s.get("leadership_ready") or s.get("sector_bucket") == "confirmed_leader"]
    watchlist = [s for s in sectors if s.get("sector_bucket") == "watchlist"]

    return {
        "date_dir": summary.get("date_dir", ""),
        "counts": summary.get("counts", {}),
        "briefing_ko": briefing.get("message_ko", ""),
        "confirmed_sectors": confirmed,
        "watchlist_sectors": watchlist,
        "all_sectors": sectors,
        "stocks": stocks,
        "recommendations": recs,
    }


def build_debate_prompt(data: dict) -> str:
    """Build a prompt that can be pasted to Claude Code for LLM-quality debate."""
    date = data["date_dir"]
    counts = data["counts"]
    confirmed = data["confirmed_sectors"]
    watchlist = data["watchlist_sectors"][:7]
    stocks = data["stocks"][:15]
    recs = data["recommendations"][:5]

    lines = [
        f"# {date} 장마감 기준 트레이더 6인 토론 생성 요청",
        "",
        "아래 데이터를 기반으로 6명의 전설적 트레이더(Ed Seykota, Stan Druckenmiller, Paul Tudor Jones, William O'Neil, Nicolas Darvas, Jesse Livermore)가 토론하는 내용을 한국어로 작성해주세요.",
        "",
        "## 시장 데이터",
        f"- Alpha 통과: {counts.get('alpha', 0)}개",
        f"- VCP (Beta): {counts.get('beta', 0)}개",
        f"- 추천: {counts.get('picks', 0)}개",
        "",
        "### 확정 주도 섹터",
    ]
    for s in confirmed:
        lines.append(f"- {s['sector']}: score={s['leader_score']}, alpha_ratio={s.get('alpha_ratio',0)}, avg_ret120={round(s.get('avg_ret120',0)*100,1)}%")

    lines.append("")
    lines.append("### 워치리스트 섹터")
    for s in watchlist:
        lines.append(f"- {s['sector']}: score={s['leader_score']}, alpha_ratio={s.get('alpha_ratio',0)}, avg_ret120={round(s.get('avg_ret120',0)*100,1)}%")

    lines.append("")
    lines.append("### 상위 종목")
    for s in stocks:
        lines.append(f"- {s.get('name','')}({s['symbol']}, {s['sector']}): leader_score={s['leader_stock_score']}, alpha={s.get('alpha_score',0)}, beta={s.get('beta_confidence',0)}, ret120={s.get('ret120_pct',0)}%")

    lines.append("")
    lines.append("### 추천")
    for r in recs:
        lines.append(f"- {r.get('symbol')}: conviction={r.get('conviction')}, score={r.get('recommendation_score')}, R/R={r.get('risk_plan',{}).get('rr_ratio')}")

    lines.append("")
    lines.append("## 출력 형식")
    lines.append("아래 JSON 구조로 출력해주세요:")
    lines.append("""
```json
{
  "date": "YYYYMMDD",
  "generated_at": "ISO timestamp",
  "market_summary": "시장 개요 1-2문장",
  "traders": [
    {
      "name": "트레이더명",
      "name_en": "English name",
      "style": "투자 스타일",
      "diagnosis": "시장 진단 2-3문장",
      "picks": [
        {"symbol": "종목코드", "name": "종목명", "reason": "선택 이유"}
      ],
      "risk": "주요 리스크 1-2문장"
    }
  ],
  "consensus": [
    {"topic": "주제", "detail": "합의 내용", "supporters": 6}
  ],
  "disagreements": [
    {"topic": "주제", "bull": ["찬성 트레이더"], "bear": ["반대 트레이더"], "detail": "내용"}
  ],
  "allocation": [
    {"priority": 1, "symbol": "종목코드", "name": "종목명", "weight": "20%", "reason": "근거"}
  ],
  "risk_rules": ["리스크 규칙 1", "리스크 규칙 2"],
  "moderator_comment": "사회자 코멘트"
}
```
""")
    return "\n".join(lines)


def build_rule_based_debate(data: dict) -> dict:
    """Fallback: generate a rule-based debate without LLM."""
    date = data["date_dir"]
    confirmed = data["confirmed_sectors"]
    watchlist = data["watchlist_sectors"][:7]
    stocks = data["stocks"]
    recs = data["recommendations"][:5]
    counts = data["counts"]

    confirmed_names = [s["sector"] for s in confirmed]
    top_stock = stocks[0] if stocks else {}
    top_ret = top_stock.get("ret120_pct", 0)
    upgrade_candidate = next((s for s in watchlist if s.get("alpha_ratio", 0) >= 0.5), None)

    narrow = len(confirmed) <= 1
    euphoria = top_ret > 300
    has_upgrade = upgrade_candidate is not None

    def diag(trader_style, focus):
        parts = []
        if narrow:
            parts.append(f"확정 주도 섹터가 {len(confirmed)}개로 시장 폭이 좁습니다.")
        if euphoria:
            parts.append(f"최상위 종목 {top_stock.get('name','')}의 120일 수익률 +{top_ret:.0f}%는 극단적 수준입니다.")
        if has_upgrade:
            parts.append(f"{upgrade_candidate['sector']}(alpha_ratio {upgrade_candidate['alpha_ratio']:.0%})이 확정 섹터 승격 직전입니다.")
        parts.append(focus)
        return " ".join(parts[:3])

    # Build per-trader analysis
    traders = [
        {
            "name": "Ed Seykota",
            "name_en": "Ed Seykota",
            "style": "추세 추종 / 시스템 트레이딩",
            "diagnosis": diag("trend", "추세가 살아있는 한 시스템을 따르되, 포지션 사이즈를 극도로 제한해야 합니다."),
            "picks": [
                {"symbol": stocks[2]["symbol"], "name": stocks[2].get("name", ""), "reason": f"alpha {stocks[2].get('alpha_score',0):.1f}, 추세 명확"} if len(stocks) > 2 else {},
                {"symbol": stocks[3]["symbol"], "name": stocks[3].get("name", ""), "reason": f"beta {stocks[3].get('beta_confidence',0):.2f}, 변동성 관리 가능"} if len(stocks) > 3 else {},
            ],
            "risk": f"ret120 +{top_ret:.0f}%는 추세의 극단입니다. 총 자산 1~2% 이상 리스크 노출 금지.",
        },
        {
            "name": "Stan Druckenmiller",
            "name_en": "Stan Druckenmiller",
            "style": "탑다운 매크로 / 섹터 집중",
            "diagnosis": diag("macro", "섹터 확산 초입으로 판단하며, 차기 주도 섹터에 선제적 포지션을 구축할 시점입니다."),
            "picks": [
                {"symbol": (watchlist[0].get("sector","") if watchlist else ""), "name": f"{watchlist[0]['sector']} 대표주" if watchlist else "", "reason": f"alpha_ratio {watchlist[0].get('alpha_ratio',0):.0%}, 섹터 승격 임박"} if watchlist else {},
                {"symbol": stocks[12]["symbol"] if len(stocks) > 12 else "", "name": stocks[12].get("name","") if len(stocks) > 12 else "", "reason": "비금속 섹터 매크로 연결"} if len(stocks) > 12 else {},
            ],
            "risk": "섹터 로테이션이 실패할 경우 시장 전체가 급격히 냉각될 수 있습니다.",
        },
        {
            "name": "Paul Tudor Jones",
            "name_en": "Paul Tudor Jones",
            "style": "역추세 / 리스크-리워드 / 변곡점",
            "diagnosis": diag("contrarian", "추천 종목 전부 conviction A, R/R 동일은 시스템 과신 가능성을 시사합니다. 진입보다 수익 확보 구간입니다."),
            "picks": [
                {"symbol": stocks[2]["symbol"], "name": stocks[2].get("name",""), "reason": f"ret120 +{stocks[2].get('ret120_pct',0):.1f}%로 상승폭 절제, 하방 리스크 제한적"} if len(stocks) > 2 else {},
            ],
            "risk": f"+{top_ret:.0f}%급 종목 신규 진입은 리스크/리워드가 극도로 불리합니다. 평균 회귀 시 -20~30% 급락 가능.",
        },
        {
            "name": "William O'Neil",
            "name_en": "William O'Neil",
            "style": "CAN SLIM / 주도주 / 섹터 RS",
            "diagnosis": diag("canslim", f"VCP {counts.get('beta',0)}개는 건전한 베이스 형성 종목이 충분하다는 의미이고, 시장 방향(M)은 긍정적입니다."),
            "picks": [
                {"symbol": stocks[1]["symbol"], "name": stocks[1].get("name",""), "reason": f"주도 섹터 2번 주도주, alpha {stocks[1].get('alpha_score',0):.1f}"} if len(stocks) > 1 else {},
                {"symbol": stocks[4]["symbol"], "name": stocks[4].get("name",""), "reason": f"beta {stocks[4].get('beta_confidence',0):.2f}, VCP 패턴 매수 적합"} if len(stocks) > 4 else {},
            ],
            "risk": f"1번 주도주가 클라이맥스 톱(climax top) 신호를 보일 경우 섹터 전체 동반 조정 가능.",
        },
        {
            "name": "Nicolas Darvas",
            "name_en": "Nicolas Darvas",
            "style": "박스 이론 / 신고가 돌파",
            "diagnosis": diag("box", f"Alpha {counts.get('alpha',0)}개 종목이 상승 박스를 형성 중이고, 박스 상단 돌파 대기 종목이 풍부합니다."),
            "picks": [
                {"symbol": stocks[4]["symbol"], "name": stocks[4].get("name",""), "reason": f"ret120 +{stocks[4].get('ret120_pct',0):.1f}%, 박스 돌파 초기 단계"} if len(stocks) > 4 else {},
                {"symbol": stocks[13]["symbol"] if len(stocks) > 13 else "", "name": stocks[13].get("name","") if len(stocks) > 13 else "", "reason": "워치리스트 섹터, 섹터 승격 시 박스 확장 기대"} if len(stocks) > 13 else {},
            ],
            "risk": "beta 6~7대 종목은 박스 하단 이탈 시 급속 하락합니다. 이탈 즉시 손절이 원칙.",
        },
        {
            "name": "Jesse Livermore",
            "name_en": "Jesse Livermore",
            "style": "추세 확인 / 피라미딩 / 핵심 포인트",
            "diagnosis": diag("livermore", "최소 저항선이 상방으로 명확하며, 차기 섹터 승격이 핵심 포인트(pivotal point)입니다."),
            "picks": [
                {"symbol": stocks[0]["symbol"], "name": stocks[0].get("name",""), "reason": "추세의 왕. 신규 진입이 아닌 기존 포지션 피라미딩 관점"} if stocks else {},
                {"symbol": stocks[10]["symbol"] if len(stocks) > 10 else "", "name": stocks[10].get("name","") if len(stocks) > 10 else "", "reason": "섹터 확정 승격 시점 진입이 리버모어 방식"} if len(stocks) > 10 else {},
            ],
            "risk": "거짓 돌파가 최대 적. 워치리스트 섹터 미승격 시 관련 포지션 즉시 청산.",
        },
    ]

    # Clean empty picks
    for t in traders:
        t["picks"] = [p for p in t["picks"] if p.get("symbol")]

    # Consensus
    consensus = [
        {"topic": "주도 섹터", "detail": f"{', '.join(confirmed_names)}이 현재 시장의 확정 주도 섹터", "supporters": 6},
        {"topic": "리스크 관리", "detail": f"ret120 +{top_ret:.0f}%급 종목은 포지션 극도 제한 필수", "supporters": 6},
    ]
    if has_upgrade:
        consensus.append({"topic": "차기 주도 후보", "detail": f"{upgrade_candidate['sector']}(alpha_ratio {upgrade_candidate['alpha_ratio']:.0%})이 가장 유력", "supporters": 4})

    # Disagreements
    disagreements = [
        {
            "topic": f"{top_stock.get('name','')} 신규 진입",
            "bull": ["Seykota", "O'Neil"],
            "bear": ["Jones", "Livermore"],
            "detail": "추세 추종 vs 클라이맥스 경고",
        },
    ]
    if has_upgrade:
        disagreements.append({
            "topic": "섹터 확산 선제 베팅",
            "bull": ["Druckenmiller", "Darvas"],
            "bear": ["Livermore", "Seykota"],
            "detail": "선제 진입 vs 확인 후 진입",
        })

    # Allocation
    allocation = []
    if len(stocks) > 1:
        allocation.append({"priority": 1, "symbol": stocks[1]["symbol"], "name": stocks[1].get("name",""), "weight": "20%", "reason": "주도주 중 변동성 대비 모멘텀 최적"})
    if len(stocks) > 3:
        allocation.append({"priority": 2, "symbol": stocks[3]["symbol"], "name": stocks[3].get("name",""), "weight": "15%", "reason": "alpha 상위, beta 관리 가능"})
    if len(stocks) > 2:
        allocation.append({"priority": 3, "symbol": stocks[2]["symbol"], "name": stocks[2].get("name",""), "weight": "15%", "reason": "R/R 양호, Jones 인정"})
    if len(stocks) > 4:
        allocation.append({"priority": 4, "symbol": stocks[4]["symbol"], "name": stocks[4].get("name",""), "weight": "10%", "reason": "박스 돌파 초기"})
    allocation.append({"priority": 9, "symbol": "CASH", "name": "현금", "weight": "20%", "reason": "Jones 경고 존중, 급락 시 매수 기회"})

    risk_rules = [
        "개별 종목 손절선: 매수가 대비 -7~8%",
        f"{top_stock.get('name','')}: 기보유자 트레일링 스톱 -15%, 신규 진입 비추천",
        "VCP 종목 수 150개 이하 시 전체 포지션 30% 축소",
    ]
    if has_upgrade:
        risk_rules.append(f"{upgrade_candidate['sector']} alpha_ratio 50% 이하 하락 시 관련 포지션 청산")

    return {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "source": "rule-based",
        "market_summary": data.get("briefing_ko", "")[:300] or f"{date} 장마감 기준 분석",
        "traders": traders,
        "consensus": consensus,
        "disagreements": disagreements,
        "allocation": allocation,
        "risk_rules": risk_rules,
        "moderator_comment": f"6인의 전설적 트레이더가 공통으로 강조하는 것: 리스크 관리 없는 수익 추구는 도박입니다. 현재 시장은 기회가 풍부하지만 +{top_ret:.0f}% 수익률이 눈을 멀게 해서는 안 됩니다.",
    }


def main():
    date_dir = sys.argv[1] if len(sys.argv) > 1 else None
    data = collect_market_data(date_dir)
    resolved_date = data["date_dir"]

    # Generate rule-based debate
    debate = build_rule_based_debate(data)

    # Save to daily signals folder
    out_dir = ROOT / f"data/daily-signals/{resolved_date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "trader-debate.json"
    out_path.write_text(json.dumps(debate, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also save prompt for LLM generation
    prompt_path = out_dir / "trader-debate-prompt.txt"
    prompt_path.write_text(build_debate_prompt(data), encoding="utf-8")

    print(f"[OK] {out_path}")
    print(f"[OK] {prompt_path}")
    print(f"     date={resolved_date} | traders=6 | consensus={len(debate['consensus'])} | disagreements={len(debate['disagreements'])}")
    print()
    print("LLM으로 더 좋은 토론을 만들려면:")
    print(f"  1. {prompt_path} 내용을 Claude Code에 붙여넣기")
    print(f"  2. 결과 JSON을 {out_path} 에 저장")


if __name__ == "__main__":
    main()
