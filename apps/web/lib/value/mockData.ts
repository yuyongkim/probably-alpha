// Barrel — original ~390 LoC value mock bundle split by domain on 2026-04-23.
// New per-domain modules live under `lib/value/mock/`.
// Public surface is unchanged — all prior `from "@/lib/value/mockData"`
// imports continue to resolve.
//
// Values extracted from _integration_mockup.html.

export * from "./mock/screens";
export * from "./mock/quality";
export * from "./mock/events";
export * from "./mock/market";
