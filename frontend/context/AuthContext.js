import React, { createContext, useContext, useEffect, useState } from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    if (storedToken) {
      setToken(storedToken);
      // Validate token by fetching user profile
      fetchUserProfile(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async (authToken) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/accounts/profile/",
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        },
      );
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token invalid, clear it
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setToken(null);
      }
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/accounts/auth/token/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access);
      if (data.refresh) {
        localStorage.setItem("refresh_token", data.refresh);
      }
      setToken(data.access);
      setUser(data.user);
      return true;
    } catch (error) {
      throw error;
    }
  };

  const register = async (first_name, last_name, email, password) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/accounts/register/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ first_name, last_name, email, password }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || errorData.email?.[0] || "Registration failed",
        );
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access);
      if (data.refresh) {
        localStorage.setItem("refresh_token", data.refresh);
      }
      setToken(data.access);
      setUser(data.user);
      return true;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    isAdmin: user?.role === 'ADMIN',
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
