// AskClaudePanel — mockup `.ai-panel` with example prompts.
interface Props {
  title: string;
  desc: string;
  examples: string[];
}

export function AskClaudePanel({ title, desc, examples }: Props) {
  return (
    <div className="ai-panel">
      <h3>{title}</h3>
      <p>{desc}</p>
      <div className="ai-examples">
        {examples.map((e) => (
          <div key={e} className="ai-example">{e}</div>
        ))}
      </div>
    </div>
  );
}
