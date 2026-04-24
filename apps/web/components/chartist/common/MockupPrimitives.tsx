// Barrel — original 500-line primitive bundle split on 2026-04-23.
// New per-component modules live under `./primitives/`.
// Public surface is unchanged — all prior
// `from "@/components/chartist/common/MockupPrimitives"` imports continue to
// resolve.
//
// Each primitive mirrors mockup CSS class names so that once `globals.css`
// has the matching rules, these render at full fidelity. Blocks are
// presentational — data is always passed in via props.

export { Breadcrumb } from "./primitives/Breadcrumb";
export { PageHeader } from "./primitives/PageHeader";
export { SummaryRow } from "./primitives/SummaryRow";
export type { SummaryCell } from "./primitives/SummaryRow";
export { Panel } from "./primitives/Panel";
export { Stub } from "./primitives/Stub";
export { QuoteStrip } from "./primitives/QuoteStrip";
export { Chip } from "./primitives/Chip";
export { Heatmap } from "./primitives/Heatmap";
export type { HeatCellProps } from "./primitives/Heatmap";
export { CondList } from "./primitives/CondList";
export type { CondRow } from "./primitives/CondList";
export { ActivityLog } from "./primitives/ActivityLog";
export type { LogItem } from "./primitives/ActivityLog";
export {
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
  toneColorNumber,
  signed,
} from "./primitives/helpers";
