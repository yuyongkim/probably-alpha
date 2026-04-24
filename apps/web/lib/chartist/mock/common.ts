// Shared primitives for mock heatmaps and cells.
// Values lifted from _integration_mockup.html — keep in sync, do not fabricate.

export type Hm = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface HeatCell {
  v: string;
  h: Hm;
}

export interface HeatRow {
  name: string;
  cells: HeatCell[];
}
