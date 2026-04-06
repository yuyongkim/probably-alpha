import { createAnalysisRenderers } from './renderers/analysis.js?v=1775484394';
import { createBacktestRenderers } from './renderers/backtest.js?v=1775484394';
import { createDashboardRenderers } from './renderers/dashboard.js?v=1775484394';
import { createRecommendationRenderers } from './renderers/recommendations.js?v=1775484394';
import { createSectorGroupedRenderers } from './renderers/sector-grouped.js?v=1775484394';

export function createRenderers(actions) {
  return {
    ...createDashboardRenderers(actions),
    ...createRecommendationRenderers(actions),
    ...createBacktestRenderers(actions),
    ...createAnalysisRenderers(actions),
    ...createSectorGroupedRenderers(actions),
  };
}
