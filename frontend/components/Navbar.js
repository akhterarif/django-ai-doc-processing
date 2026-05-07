import React from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "../context/AuthContext";

export const Navbar = () => {
  const { isAuthenticated, user, logout, isAdmin } = useAuth();
  const router = useRouter();
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/">
              <span className="text-2xl font-bold text-blue-600">DocAI</span>
            </Link>
          </div>

          {/* Navigation Links */}
          {isAuthenticated && (
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <span
                  className={`px-3 py-2 rounded-md text-sm font-medium ${router.pathname === "/dashboard" ? "bg-blue-100 text-blue-700" : "text-gray-700 hover:text-blue-700"}`}
                >
                  Documents
                </span>
              </Link>

              {isAdmin && (
                <Link href="/admin/users">
                  <span
                    className={`px-3 py-2 rounded-md text-sm font-medium ${router.pathname.startsWith("/admin") ? "bg-blue-100 text-blue-700" : "text-gray-700 hover:text-blue-700"}`}
                  >
                    Admin
                  </span>
                </Link>
              )}

              {/* User Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="text-gray-700 hover:text-blue-700 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  {user?.first_name || "User"} ▼
                </button>

                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50">
                    <div className="px-4 py-2 border-b text-sm text-gray-600">
                      {user?.email}
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Login/Register Links for unauthenticated users */}
          {!isAuthenticated && (
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <span className="text-gray-700 hover:text-blue-700 px-3 py-2 rounded-md text-sm font-medium">
                  Login
                </span>
              </Link>
              <Link href="/register">
                <span className="bg-blue-600 text-white hover:bg-blue-700 px-4 py-2 rounded-md text-sm font-medium">
                  Register
                </span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
