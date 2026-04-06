import { createAnalysisRenderers } from './renderers/analysis.js?v=1775472534';
import { createBacktestRenderers } from './renderers/backtest.js?v=1775472534';
import { createDashboardRenderers } from './renderers/dashboard.js?v=1775472534';
import { createRecommendationRenderers } from './renderers/recommendations.js?v=1775472534';
import { createSectorGroupedRenderers } from './renderers/sector-grouped.js?v=1775472534';

export function createRenderers(actions) {
  return {
    ...createDashboardRenderers(actions),
    ...createRecommendationRenderers(actions),
    ...createBacktestRenderers(actions),
    ...createAnalysisRenderers(actions),
    ...createSectorGroupedRenderers(actions),
  };
}
