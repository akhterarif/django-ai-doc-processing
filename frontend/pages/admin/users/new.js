import React, { useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../../../context/AuthContext";
import ProtectedRoute from "../../../components/ProtectedRoute";
import LoadingSpinner from "../../../components/LoadingSpinner";
import Link from "next/link";

export default function AdminUserCreatePage() {
  const router = useRouter();
  const { token } = useAuth();

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    role: "HR",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        "http://localhost:8000/api/accounts/users/",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.email?.[0] || "Failed to create user");
      }

      setSuccess("User created successfully.");
      setFormData({ first_name: "", last_name: "", email: "", password: "", role: "HR" });
      router.push("/admin/users");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Link href="/admin/users">
          <button className="text-blue-600 hover:text-blue-700 mb-6 font-medium">
            ← Back to Users
          </button>
        </Link>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Add User</h1>

          {error && (
            <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg border border-red-300">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg border border-green-300">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value="ADMIN">Admin</option>
                <option value="HR">HR</option>
                <option value="ACCOUNTANT">Accountant</option>
                <option value="LEGAL">Legal</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <LoadingSpinner size="sm" />
                  Creating...
                </>
              ) : (
                "Create User"
              )}
            </button>
          </form>
        </div>
      </div>
    </ProtectedRoute>
  );
}
