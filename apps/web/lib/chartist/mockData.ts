// Barrel — original ~680 LoC mock bundle split by domain on 2026-04-23.
// New per-domain modules live under `lib/chartist/mock/`.
// Public surface is unchanged — all prior
// `from "@/lib/chartist/mockData"` imports continue to resolve.
//
// Values lifted directly from _integration_mockup.html so the
// non-Today Chartist sub-sections render at full density even before
// live APIs exist. Keep in sync with the mockup — do not fabricate numbers.

export * from "./mock/common";
export * from "./mock/flow";
export * from "./mock/themes";
export * from "./mock/technicals";
export * from "./mock/ops";
export * from "./mock/wizards";
