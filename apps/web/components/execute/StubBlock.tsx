// StubBlock — mockup `.stub` placeholder card used across Execute sub-pages.
interface Props {
  icon: string;
  title: string;
  desc: string;
  chips?: string[];
}

export function StubBlock({ icon, title, desc, chips }: Props) {
  return (
    <div className="stub">
      <div className="stub-icon">{icon}</div>
      <div className="stub-title">{title}</div>
      <div className="stub-desc">{desc}</div>
      {chips && chips.length > 0 ? (
        <div className="stub-chips">
          {chips.map((c) => <span key={c} className="chip">{c}</span>)}
        </div>
      ) : null}
    </div>
  );
}
