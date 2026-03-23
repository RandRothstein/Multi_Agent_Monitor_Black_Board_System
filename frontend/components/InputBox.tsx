"use client";

import { useState } from "react";

export default function InputBox({ onSend }: { onSend: (q: string) => void }) {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  return (
    <div className="flex gap-2 mt-4">
      <input
        className="flex-1 border p-2 rounded"
        placeholder="Ask about SKU..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />

      <button
        onClick={handleSubmit}
        className="bg-blue-500 text-white px-4 rounded"
      >
        Send
      </button>
    </div>
  );
}