import { Message } from "@/types";
import AgentTrace from "./AgentTrace";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`p-3 rounded ${isUser ? "bg-blue-100" : "bg-gray-100"}`}>
      <div className="font-semibold mb-1">
        {isUser ? "You" : "Supervisor"}
      </div>

      <div>{message.content}</div>

      {message.findings && (
        <AgentTrace findings={message.findings} />
      )}
    </div>
  );
}