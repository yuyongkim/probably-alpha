from __future__ import annotations

from sepa.data.kis_product_catalog import filter_kis_product_catalog


def kis_product_catalog_payload(
    *,
    orderable_only: bool = False,
    backtestable_only: bool = False,
    project_supported_only: bool = False,
) -> dict:
    items = filter_kis_product_catalog(
        orderable_only=orderable_only,
        backtestable_only=backtestable_only,
        project_supported_only=project_supported_only,
    )
    return {
        'count': len(items),
        'summary': {
            'kis_orderable_count': sum(1 for item in items if item.get('kis_order_support')),
            'project_info_count': sum(1 for item in items if item.get('project_info_support')),
            'project_backtestable_count': sum(1 for item in items if item.get('project_backtest_support')),
            'recommended_now_count': sum(1 for item in items if item.get('recommended_now')),
        },
        'items': items,
    }
