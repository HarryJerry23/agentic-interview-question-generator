import { derivePipeline } from "../lib/pipelineState.js";

// Always-visible, plain-language view of where the run is. Renders from the first frame (even with
// zero events) so the run view is never blank, and narrates the current step in one sentence — the
// transparency the graph alone didn't give. The react-flow graph below is optional visual detail.
export default function PipelineStepper({ events, workflow }) {
  const { now, stages } = derivePipeline(events, workflow);
  return (
    <div className="card stepper-card">
      <div className="stepper-now">{now}</div>
      <ol className="stepper">
        {stages.map((s, i) => (
          <li key={s.key} className={"step step-" + s.status}>
            <span className="step-dot">{s.status === "done" ? "✓" : i + 1}</span>
            <span className="step-label">{s.label}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
