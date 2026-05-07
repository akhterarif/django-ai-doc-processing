import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../context/AuthContext";
import ProtectedRoute from "../components/ProtectedRoute";
import LoadingSpinner from "../components/LoadingSpinner";
import Link from "next/link";

export default function DashboardPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (token) {
      fetchDocuments();
    }
  }, [token]);

  const fetchDocuments = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/documents/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch documents");
      }

      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      UPLOADED: "bg-yellow-100 text-yellow-800",
      PROCESSING: "bg-blue-100 text-blue-800",
      COMPLETED: "bg-green-100 text-green-800",
      FAILED: "bg-red-100 text-red-800",
    };

    return (
      <span
        className={`px-3 py-1 rounded-full text-xs font-semibold ${statusClasses[status] || "bg-gray-100 text-gray-800"}`}
      >
        {status || "Unknown"}
      </span>
    );
  };

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Documents</h1>
          <Link href="/documents/upload">
            <button className="bg-blue-600 text-white hover:bg-blue-700 px-6 py-2 rounded-lg font-medium transition">
              Upload Document
            </button>
          </Link>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg border border-red-300">
            {error}
          </div>
        )}

        {loading ? (
          <LoadingSpinner fullScreen={true} />
        ) : documents.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg mb-4">
              You haven't uploaded any documents yet.
            </p>
            <Link href="/documents/upload">
              <button className="bg-blue-600 text-white hover:bg-blue-700 px-6 py-2 rounded-lg font-medium transition">
                Upload Your First Document
              </button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate">
                  {doc.file_name || "Untitled"}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Uploaded: {new Date(doc.created_at).toLocaleDateString()}
                </p>
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs text-gray-500">
                    {(doc.file_size / 1024).toFixed(2)} KB
                  </span>
                  {getStatusBadge(doc.status)}
                </div>
                <Link href={`/documents/${doc.id}`}>
                  <button className="w-full bg-gray-100 text-gray-900 hover:bg-gray-200 px-4 py-2 rounded-lg font-medium transition">
                    View Details
                  </button>
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
