import Link from "next/link";
import { useEffect, useState } from "react";

export default function Home() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/documents`)
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched documents:", data);

        setDocuments(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="max-w-3xl mx-auto mb-8">
        <h1 className="text-3xl font-bold text-center">
          Document Intelligence
        </h1>
        <nav className="mt-4 text-center">
          <Link href="/upload" className="text-blue-500 hover:underline">
            Upload new document
          </Link>
        </nav>
      </header>

      <main className="max-w-3xl mx-auto">
        {loading ? (
          <p>Loading...</p>
        ) : documents.length === 0 ? (
          <p>No documents yet. Upload one!</p>
        ) : (
          <ul className="space-y-4">
            {documents.map((doc) => (
              <li key={doc.id} className="p-4 bg-white rounded shadow">
                <p>ID: {doc.id}</p>
                <p>Status: {doc.status}</p>
                {doc.analysis && (
                  <p>Summary: {doc.analysis.summary.substring(0, 100)}...</p>
                )}
                <Link
                  href={`/documents/${doc.id}`}
                  className="text-blue-500 hover:underline"
                >
                  View details
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
