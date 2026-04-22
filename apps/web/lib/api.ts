// Tiny fetch helper that unwraps the {ok, data, error} envelope.
// Server Components pass absolute URLs; `next` fetch cache is fine.

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";

interface Envelope<T> {
  ok: boolean;
  data: T | null;
  error: { code?: string; message?: string } | null;
}

export async function fetchEnvelope<T>(
  path: string,
  init?: RequestInit & { revalidate?: number },
): Promise<T> {
  const url = path.startsWith("http") ? path : `${BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    next: { revalidate: init?.revalidate ?? 60 },
  });
  if (!res.ok) throw new Error(`API ${res.status} ${url}`);
  const body = (await res.json()) as Envelope<T>;
  if (!body.ok || body.data == null) {
    throw new Error(body.error?.message ?? "API envelope error");
  }
  return body.data;
}
