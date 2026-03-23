export interface Finding {
  agent_name: string;
  severity_score: number;
  finding_summary: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  findings?: Finding[];
}