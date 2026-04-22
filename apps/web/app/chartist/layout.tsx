export default function ChartistLayout({ children }: { children: React.ReactNode }) {
  return (
    <section>
      <div className="text-xs uppercase tracking-widest text-[color:var(--muted)] mb-2">Chartist</div>
      {children}
    </section>
  );
}
