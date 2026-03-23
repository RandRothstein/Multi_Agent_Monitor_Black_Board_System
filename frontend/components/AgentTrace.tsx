import { Finding } from "@/types";

export default function AgentTrace({ findings }: { findings: Finding[] }) {
  return (
    <div className="mt-3 border rounded p-3 bg-white">
      <h3 className="font-semibold text-sm mb-2">Agent Analysis</h3>

      {findings.map((f, idx) => (
        <div key={idx} className="mb-2 p-2 border rounded">
          <div><b>Agent:</b> {f.agent_name}</div>
          <div><b>Severity:</b> {f.severity_score}</div>
          <div className="text-sm mt-1">{f.finding_summary}</div>
        </div>
      ))}
    </div>
  );
}