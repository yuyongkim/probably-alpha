from __future__ import annotations

from datetime import datetime


def _fmt_number(value: object) -> str:
    try:
        return f'{float(value):,.2f}'
    except (TypeError, ValueError):
        return '-'


def build_briefing(date_dir: str, sectors: list[dict], recs: list[dict]) -> dict:
    top_sector = sectors[0]['sector'] if sectors else 'N/A'
    top_sector_score = sectors[0].get('leader_score', 0) if sectors else 0

    lead = recs[0] if recs else None
    if lead:
        lead_name = lead.get('name') or lead.get('symbol') or 'N/A'
        risk_plan = lead.get('risk_plan') or {}
        why = lead.get('why') or {}
        message_en = (
            f'{date_dir} after-close view: top leader sector is {top_sector} '
            f'(score {_fmt_number(top_sector_score)}). '
            f'Best-ranked setup is {lead_name} ({lead.get("symbol", "-")}) '
            f'[{lead.get("conviction", "-")}], '
            f'EPS={why.get("eps_status", "-")}, '
            f'least_resistance={why.get("least_resistance", "-")}, '
            f'entry={_fmt_number(risk_plan.get("entry"))}, '
            f'stop={_fmt_number(risk_plan.get("stop"))}, '
            f'target={_fmt_number(risk_plan.get("target"))}.'
        )
        message_ko = (
            f'{date_dir} 장마감 기준: 최상위 주도섹터는 {top_sector} '
            f'(점수 {_fmt_number(top_sector_score)}) 입니다. '
            f'최상위 후보는 {lead_name} ({lead.get("symbol", "-")}) '
            f'[{lead.get("conviction", "-")}], '
            f'EPS={why.get("eps_status", "-")}, '
            f'최소저항={why.get("least_resistance", "-")}, '
            f'진입={_fmt_number(risk_plan.get("entry"))}, '
            f'손절={_fmt_number(risk_plan.get("stop"))}, '
            f'목표={_fmt_number(risk_plan.get("target"))} 입니다.'
        )
    else:
        message_en = (
            f'{date_dir} after-close view: no stock passed the final recommendation gate. '
            'Recheck EPS, least-resistance, and sector-leadership conditions.'
        )
        message_ko = (
            f'{date_dir} 장마감 기준: 최종 추천 게이트를 통과한 종목이 없습니다. '
            'EPS, 최소저항, 섹터 리더십 조건을 다시 확인하세요.'
        )

    return {
        'as_of': datetime.now().isoformat(timespec='seconds'),
        'date_dir': date_dir,
        'headline': 'Minervini Daily Briefing',
        'message_ko': message_ko,
        'message_en': message_en,
        'recommendation_count': len(recs),
    }
