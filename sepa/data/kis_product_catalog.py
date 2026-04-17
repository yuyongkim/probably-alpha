from __future__ import annotations

from functools import lru_cache


_CATALOG: tuple[dict, ...] = (
    {
        'family_id': 'domestic_stock',
        'label_ko': '국내주식',
        'label_en': 'Domestic Stocks',
        'market': 'KR',
        'asset_class': 'equity',
        'examples_folders': ['domestic_stock'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': True,
        'project_info_support': True,
        'project_backtest_support': True,
        'recommended_now': True,
        'notes': '국내 현물 주식은 KIS 샘플에서 시세/실시간/주문 예제가 가장 풍부합니다.',
    },
    {
        'family_id': 'domestic_etf_etn',
        'label_ko': '국내 ETF/ETN',
        'label_en': 'Domestic ETF/ETN',
        'market': 'KR',
        'asset_class': 'fund',
        'examples_folders': ['etfetn', 'domestic_stock'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': True,
        'project_info_support': True,
        'project_backtest_support': True,
        'recommended_now': True,
        'notes': 'ETF/ETN 시세는 etfetn 폴더, 현물 주문은 domestic_stock 주문 흐름으로 연결하는 구조입니다.',
    },
    {
        'family_id': 'overseas_stock',
        'label_ko': '해외주식',
        'label_en': 'Overseas Stocks',
        'market': 'US/Global',
        'asset_class': 'equity',
        'examples_folders': ['overseas_stock'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': True,
        'project_info_support': False,
        'project_backtest_support': False,
        'recommended_now': False,
        'notes': 'KIS 샘플에는 시세/실시간/주문 예제가 있으나, 현재 프로젝트에는 아직 전용 데이터 적재/백테스트를 붙이지 않았습니다.',
    },
    {
        'family_id': 'domestic_bond',
        'label_ko': '국내채권',
        'label_en': 'Domestic Bonds',
        'market': 'KR',
        'asset_class': 'bond',
        'examples_folders': ['domestic_bond'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': True,
        'project_info_support': False,
        'project_backtest_support': False,
        'recommended_now': False,
        'notes': 'KIS 샘플에는 장내채권 시세/주문 예제가 있지만, 현재 프로젝트 백테스트 엔진은 채권 체결 모델을 아직 반영하지 않습니다.',
    },
    {
        'family_id': 'domestic_futureoption',
        'label_ko': '국내선물옵션',
        'label_en': 'Domestic Futures/Options',
        'market': 'KR',
        'asset_class': 'derivative',
        'examples_folders': ['domestic_futureoption'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': True,
        'project_info_support': False,
        'project_backtest_support': False,
        'recommended_now': False,
        'notes': '주문 예제는 있으나 증거금, 만기, 야간 세션 모델이 필요해 현재 프로젝트에는 아직 넣지 않았습니다.',
    },
    {
        'family_id': 'overseas_futureoption',
        'label_ko': '해외선물옵션',
        'label_en': 'Overseas Futures/Options',
        'market': 'Global',
        'asset_class': 'derivative',
        'examples_folders': ['overseas_futureoption'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': True,
        'project_info_support': False,
        'project_backtest_support': False,
        'recommended_now': False,
        'notes': 'KIS 샘플에 주문/정정취소/실시간 통보까지 있으나, 현재 프로젝트는 아직 현물 중심입니다.',
    },
    {
        'family_id': 'elw',
        'label_ko': 'ELW',
        'label_en': 'ELW',
        'market': 'KR',
        'asset_class': 'structured',
        'examples_folders': ['elw'],
        'kis_quote_support': True,
        'kis_realtime_support': True,
        'kis_order_support': False,
        'project_info_support': False,
        'project_backtest_support': False,
        'recommended_now': False,
        'notes': '공식 샘플 저장소 기준으로 ELW는 시세/실시간 예제가 보이고 주문 예제는 확인되지 않았습니다.',
    },
)


@lru_cache(maxsize=1)
def load_kis_product_catalog() -> list[dict]:
    return [dict(item) for item in _CATALOG]


def filter_kis_product_catalog(
    *,
    orderable_only: bool = False,
    backtestable_only: bool = False,
    project_supported_only: bool = False,
) -> list[dict]:
    items = load_kis_product_catalog()
    if orderable_only:
        items = [item for item in items if item.get('kis_order_support')]
    if backtestable_only:
        items = [item for item in items if item.get('project_backtest_support')]
    if project_supported_only:
        items = [item for item in items if item.get('project_info_support') or item.get('project_backtest_support')]
    return items
