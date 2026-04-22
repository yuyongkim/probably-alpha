// ChatFab — bottom-right circular α button. Hides while the panel is open
// so the two don't stack visually on top of each other.
"use client";

import { useChatFab } from "@/lib/chatFab";

export function ChatFab() {
  const open = useChatFab((s) => s.open);
  const toggle = useChatFab((s) => s.toggle);
  if (open) return null;
  return (
    <button
      type="button"
      className="chat-fab"
      aria-label="Open Alpha assistant"
      onClick={toggle}
    >
      α
    </button>
  );
}
