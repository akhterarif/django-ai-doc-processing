import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";

export default function DocumentDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/documents/${id}/`)
      .then((res) => res.json())
      .then((data) => {
        setDoc(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  if (loading) return <p>Loading...</p>;
  if (!doc) return <p>Document not found</p>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="max-w-3xl mx-auto mb-8">
        <h1 className="text-3xl font-bold">Document {id}</h1>
        <nav className="mt-4">
          <Link href="/" className="text-blue-500 hover:underline">
            Back to list
          </Link>
        </nav>
      </header>
      <main className="max-w-3xl mx-auto bg-white p-6 rounded shadow">
        <p>
          <strong>Status:</strong> {doc.status}
        </p>
        {doc.analysis && (
          <>
            <h2 className="text-xl font-semibold mt-4">Summary</h2>
            <p>{doc.analysis.summary}</p>
            <h3 className="mt-4 font-semibold">Key Points</h3>
            <ul className="list-disc ml-6">
              {doc.analysis.key_points.map((p, idx) => (
                <li key={idx}>{p}</li>
              ))}
            </ul>
            <h3 className="mt-4 font-semibold">Topics</h3>
            <ul className="list-disc ml-6">
              {doc.analysis.topics.map((t, idx) => (
                <li key={idx}>{t}</li>
              ))}
            </ul>
          </>
        )}
      </main>
    </div>
  );
}
