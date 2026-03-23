export async function analyzeQuery(query: string) {
  const res = await fetch("http://localhost:8000/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  return res.json();
}