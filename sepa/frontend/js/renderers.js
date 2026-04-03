import { createAnalysisRenderers } from './renderers/analysis.js';
import { createBacktestRenderers } from './renderers/backtest.js';
import { createDashboardRenderers } from './renderers/dashboard.js';
import { createRecommendationRenderers } from './renderers/recommendations.js';
import { createSectorGroupedRenderers } from './renderers/sector-grouped.js';

export function createRenderers(actions) {
  return {
    ...createDashboardRenderers(actions),
    ...createRecommendationRenderers(actions),
    ...createBacktestRenderers(actions),
    ...createAnalysisRenderers(actions),
    ...createSectorGroupedRenderers(actions),
  };
}
