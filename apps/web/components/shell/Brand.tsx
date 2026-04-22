// Brand mark + wordmark — α glyph on accent swatch + "Probably Alpha".
// Used in TopNav (and potentially auth screens later).
import Link from "next/link";

export function Brand() {
  return (
    <Link href="/" className="brand">
      <span className="brand-mark" aria-hidden>
        α
      </span>
      <span>Probably Alpha</span>
    </Link>
  );
}
