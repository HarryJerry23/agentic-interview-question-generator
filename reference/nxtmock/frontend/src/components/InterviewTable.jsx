import { useState } from "react";

// Mock Interview review queue (Feature 11, Part 3). Renders the under-evidenced harvested questions
// for the exception-only human gate: approve (publish) or reject (with a reason that teaches the
// self-evolving SKILL.md). Anything left untouched is approved on submit.
export default function InterviewTable({ rows, decisions = {}, onDecide, onReset, readOnly = false }) {
  if (!rows?.length) return null;
  return (
    <div className="card interview-queue-card">
      <table className="interview-queue">
        <thead>
          <tr>
            <th>#</th><th>Interview question</th><th>Outcome</th>
            <th>Companies</th><th>Sources</th>{!readOnly && <th>Review</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const d = decisions[r.qid];
            const cls = d?.action === "reject" ? "row-rejected" : d?.action ? "row-approved" : "";
            return (
              <tr key={r.qid} className={cls}>
                <td>{i + 1}</td>
                <td className="iq-question">{r.question_text}</td>
                <td><code>{r.outcome || "—"}</code></td>
                <td>
                  {(r.companies || []).length === 0 ? "—" : r.companies.map((c, j) => (
                    <span key={j}>
                      {j > 0 ? ", " : ""}
                      {c.url ? <a href={c.url} target="_blank" rel="noreferrer">{c.name}</a> : c.name}
                    </span>
                  ))}
                </td>
                <td className="iq-sources">
                  {(r.source_urls || []).map((u, j) => (
                    <span key={j}>{j > 0 ? " · " : ""}<a href={u} target="_blank" rel="noreferrer">src{j + 1}</a></span>
                  ))}
                </td>
                {!readOnly && (
                  <td>
                    {d?.action ? (
                      <span className="iq-decided">
                        {d.action === "reject" ? "✕ rejected" : "✓ approved"}{" "}
                        <button className="btn btn-sm btn-ghost" onClick={() => onReset(r.qid)}>Change ↺</button>
                      </span>
                    ) : (
                      <ReviewControls row={r} onDecide={onDecide} />
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ReviewControls({ row, onDecide }) {
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  if (rejecting) {
    return (
      <span className="iq-reject">
        <input className="iq-reason" placeholder="Why reject? (teaches the verifier)"
          value={reason} onChange={(e) => setReason(e.target.value)} />
        <button className="btn btn-sm" disabled={!reason.trim()}
          onClick={() => onDecide({ qid: row.qid, action: "reject", reason: reason.trim() })}>Confirm</button>
        <button className="btn btn-sm btn-ghost" onClick={() => setRejecting(false)}>Cancel</button>
      </span>
    );
  }
  return (
    <span className="iq-actions">
      <button className="btn btn-sm btn-primary" onClick={() => onDecide({ qid: row.qid, action: "approve" })}>Approve</button>
      <button className="btn btn-sm" onClick={() => setRejecting(true)}>Reject</button>
    </span>
  );
}
