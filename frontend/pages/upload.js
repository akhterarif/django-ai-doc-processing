import { useState } from "react";
import { useRouter } from "next/router";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    const form = new FormData();
    form.append("file", file);

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/documents/upload`,
      {
        method: "POST",
        body: form,
      },
    );
    const data = await res.json();
    if (res.ok) {
      setMessage("Uploaded! Document ID: " + data.id);
      router.push("/");
    } else {
      setMessage("Upload failed");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="max-w-3xl mx-auto mb-8">
        <h1 className="text-3xl font-bold text-center">Upload Document</h1>
      </header>
      <main className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Upload
          </button>
        </form>
        {message && <p className="mt-4">{message}</p>}
      </main>
    </div>
  );
}
