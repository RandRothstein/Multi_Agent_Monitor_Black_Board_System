"use client";

import { useState } from "react";
import { analyzeQuery } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import { Message } from "@/types";

export default function ChatWindow() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);

    const handleSend = async (query: string) => {
        // 1. Add User Message
        const userMsg: Message = { role: "user", content: query };
        setMessages((prev) => [...prev, userMsg]);

        setLoading(true);

        try {
            // 2. Fetch API Data
            const res = await analyzeQuery(query);

            // 3. Add Assistant Message with Findings
            const botMsg: Message = {
                role: "assistant",
                content: `Analysis for SKU: ${res.sku}`,
                findings: res.findings,
            };

            setMessages((prev) => [...prev, botMsg]);
        } catch (err) {
            // 4. Handle Errors
            setMessages((prev) => [
                ...prev,
                { 
                    role: "assistant", 
                    content: "Error processing request." 
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[80vh] border rounded p-4">
            {/* Chat History Area */}
            <div className="flex-1 overflow-y-auto space-y-4">
                {messages.map((msg, idx) => (
                    <MessageBubble key={idx} message={msg} />
                ))}
                
                {loading && (
                    <div className="text-sm text-gray-500 italic animate-pulse">
                        Thinking...
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="mt-4">
                <InputBox onSend={handleSend} />
            </div>
        </div>
    );
}