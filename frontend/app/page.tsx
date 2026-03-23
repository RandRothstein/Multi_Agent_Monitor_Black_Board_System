import ChatWindow from "@/components/ChatWindow";

export default function Home() {
  return (
    <main className="max-w-3xl mx-auto mt-10">
      <h1 className="text-2xl font-bold mb-4">
        Multi-Agent Supervisor Dashboard
      </h1>

      <ChatWindow />
    </main>
  );
}