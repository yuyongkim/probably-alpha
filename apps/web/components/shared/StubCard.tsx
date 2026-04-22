// StubCard — mockup `.stub` placeholder with icon, title, desc, optional chips.

interface Props {
  icon?: string;
  title: string;
  desc: string;
  chips?: string[];
}

export function StubCard({ icon, title, desc, chips }: Props) {
  return (
    <div className="stub">
      {icon ? <div className="stub-icon">{icon}</div> : null}
      <div className="stub-title">{title}</div>
      <div className="stub-desc">{desc}</div>
      {chips && chips.length > 0 ? (
        <div className="stub-chips">
          {chips.map((c) => (
            <span key={c} className="chip">
              {c}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
