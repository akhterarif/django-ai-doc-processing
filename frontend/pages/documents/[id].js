import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../../context/AuthContext";
import ProtectedRoute from "../../components/ProtectedRoute";
import LoadingSpinner from "../../components/LoadingSpinner";
import ReactMarkdown from "react-markdown";
import Link from "next/link";

export default function DocumentDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const { token } = useAuth();

  const [document, setDocument] = useState(null);
  const [documentLoading, setDocumentLoading] = useState(true);
  const [documentError, setDocumentError] = useState("");

  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState("");
  const [thinking, setThinking] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch document details
  useEffect(() => {
    if (id && token) {
      fetchDocument();
      fetchConversations();
    }
  }, [id, token]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchDocument = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/documents/${id}/`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!response.ok) throw new Error("Failed to fetch document");
      const data = await response.json();
      setDocument(data);
    } catch (err) {
      setDocumentError(err.message);
    } finally {
      setDocumentLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/documents/${id}/chat/list/`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (response.ok) {
        const data = await response.json();
        setConversations(Array.isArray(data) ? data : data.results || []);

        // Load previous conversations into messages
        const loadedMessages = [];
        const conversationsList = Array.isArray(data)
          ? data
          : data.results || [];

        // Sort conversations by ID (assuming higher ID = newer)
        conversationsList.sort((a, b) => a.id - b.id);

        conversationsList.forEach((conv) => {
          // Add user question
          loadedMessages.push({
            id: `q-${conv.id}`,
            role: "user",
            content: conv.question,
          });
          // Add assistant answer if completed
          if (conv.status === "COMPLETED" && conv.answer) {
            loadedMessages.push({
              id: `a-${conv.id}`,
              role: "assistant",
              content: conv.answer,
              sources: conv.sources || [],
            });
          }
        });
        setMessages(loadedMessages);
      }
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    }
  };

  const handleSendQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setSending(true);
    setThinking(true);
    setChatError("");

    try {
      // Create new conversation or use selected one
      const response = await fetch(
        `http://localhost:8000/api/documents/${id}/chat/`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: question.trim() }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to send question");
      }

      const data = await response.json();

      console.log("Created conversation:", data);

      // Add message to chat
      setMessages((prev) => [
        ...prev,
        { id: "q-" + Date.now(), role: "user", content: question },
      ]);

      setQuestion("");
      setSelectedConversation(data.conversation_id || data.id);

      // Poll for answer
      pollForAnswer(data.conversation_id || data.id);

      // Refresh conversations
      fetchConversations();
    } catch (err) {
      setChatError(err.message || "Failed to send question");
      setSending(false);
      setThinking(false);
    }
  };

  const pollForAnswer = async (conversationId, attempts = 0) => {
    if (attempts > 30) {
      // Stop after 30 attempts (5 minutes with 10s intervals)
      setChatError("Response timeout. Please try again.");
      setSending(false);
      setThinking(false);
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/documents/${id}/chat/${conversationId}/`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();

        if (data.status === "COMPLETED") {
          setMessages((prev) => [
            ...prev,
            {
              id: "a-" + conversationId,
              role: "assistant",
              content: data.answer,
              sources: data.sources_cited || [],
            },
          ]);
          setSending(false);
          setThinking(false);
        } else if (data.status === "FAILED") {
          setChatError("Failed to generate response. Please try again.");
          setSending(false);
          setThinking(false);
        } else {
          // Still processing, poll again
          setTimeout(() => pollForAnswer(conversationId, attempts + 1), 10000);
        }
      }
    } catch (err) {
      console.error("Polling error:", err);
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
        {status}
      </span>
    );
  };

  if (documentLoading) {
    return <LoadingSpinner fullScreen={true} />;
  }

  if (!document) {
    return (
      <ProtectedRoute>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600">
              Document Not Found
            </h1>
            <Link href="/dashboard">
              <button className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
                Back to Dashboard
              </button>
            </Link>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Link href="/dashboard">
          <button className="text-blue-600 hover:text-blue-700 mb-6 font-medium">
            ← Back to Documents
          </button>
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Document Info Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
              <h2 className="text-xl font-bold text-gray-900 mb-4 break-words">
                {document.file_name || "Untitled"}
              </h2>

              <div className="space-y-4 text-sm">
                <div>
                  <p className="text-gray-600 font-medium">Status</p>
                  <div className="mt-1">{getStatusBadge(document.status)}</div>
                </div>

                <div>
                  <p className="text-gray-600 font-medium">File Size</p>
                  <p className="text-gray-900">
                    {(document.file_size / 1024).toFixed(2)} KB
                  </p>
                </div>

                <div>
                  <p className="text-gray-600 font-medium">Uploaded</p>
                  <p className="text-gray-900">
                    {new Date(document.created_at).toLocaleDateString()}
                  </p>
                </div>

                {document && (
                  <>
                    {document.doc_type && (
                      <div>
                        <p className="text-gray-600 font-medium">
                          Document Type
                        </p>
                        <p className="text-gray-900 capitalize">
                          {document.doc_type}
                        </p>
                      </div>
                    )}

                    {document.summary && (
                      <div>
                        <p className="text-gray-600 font-medium">Summary</p>
                        <p className="text-gray-700 text-xs leading-relaxed mt-1">
                          {document.summary}
                        </p>
                      </div>
                    )}

                    {document.key_points && document.key_points.length > 0 && (
                      <div>
                        <p className="text-gray-600 font-medium mb-2">
                          Key Points
                        </p>
                        <ul className="list-disc list-inside space-y-1 text-xs text-gray-700">
                          {document.key_points.map((point, idx) => (
                            <li key={idx}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Main Content - Analysis and Chat */}
          <div className="lg:col-span-2 space-y-8">
            {/* Analysis Section */}
            {document.analysis && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  Analysis
                </h3>

                {document.summary && (
                  <div className="mb-6">
                    <h4 className="font-semibold text-gray-900 mb-2">
                      Summary
                    </h4>
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {document.summary}
                    </p>
                  </div>
                )}

                {document.key_points && document.key_points.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">
                      Key Points
                    </h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                      {document.key_points.map((point, idx) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Chat Section */}
            <div
              className="bg-white rounded-lg shadow-md p-6 flex flex-col"
              style={{ height: "500px" }}
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900">
                  Chat with Document
                </h3>
                <button
                  onClick={fetchConversations}
                  className="bg-gray-200 text-gray-900 hover:bg-gray-300 px-3 py-1 rounded text-sm font-medium transition"
                  title="Refresh conversation history"
                >
                  ↻ Refresh
                </button>
              </div>

              {chatError && (
                <div className="mb-4 p-3 bg-red-100 text-red-700 rounded border border-red-300 text-sm">
                  {chatError}
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto mb-4 space-y-4">
                {messages.length === 0 && !thinking ? (
                  <p className="text-gray-500 text-sm text-center py-8">
                    Ask a question about this document to get started...
                  </p>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${
                        msg.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          msg.role === "user"
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-900"
                        }`}
                      >
                        {msg.role === "assistant" ? (
                          <div className="prose prose-sm text-sm text-gray-900">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                          </div>
                        ) : (
                          <p className="text-sm">{msg.content}</p>
                        )}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-2 text-xs border-t border-gray-300 pt-2 opacity-75">
                            <p className="font-semibold">Sources:</p>
                            {msg.sources.map((src, idx) => (
                              <p key={idx}>
                                •{" "}
                                {typeof src === "string"
                                  ? src
                                  : src.chunk?.slice(0, 100) || "Reference"}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
                {thinking && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-900 px-4 py-3 rounded-lg max-w-xs lg:max-w-md">
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1">
                          <span
                            className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                            style={{ animationDelay: "0s" }}
                          ></span>
                          <span
                            className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          ></span>
                          <span
                            className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                            style={{ animationDelay: "0.4s" }}
                          ></span>
                        </div>
                        <span className="text-sm font-medium">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendQuestion} className="border-t pt-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a question about the document..."
                    disabled={sending || document.status !== "COMPLETED"}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <button
                    type="submit"
                    disabled={
                      sending ||
                      !question.trim() ||
                      document.status !== "COMPLETED"
                    }
                    className="bg-blue-600 text-white hover:bg-blue-700 px-4 py-2 rounded-lg font-medium disabled:bg-gray-400 transition"
                  >
                    {sending ? <LoadingSpinner size="sm" /> : "Send"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
