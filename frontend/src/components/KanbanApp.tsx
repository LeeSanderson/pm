"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";
type SubmitState = "idle" | "login" | "logout";

type SessionResponse = {
  username: string;
};

const getErrorMessage = async (response: Response, fallback: string) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
};

export const KanbanApp = () => {
  const [authStatus, setAuthStatus] = useState<AuthStatus>("loading");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [username, setUsername] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const loadSession = async () => {
      try {
        const response = await fetch("/api/auth/session", {
          credentials: "same-origin",
        });

        if (!isMounted) {
          return;
        }

        if (response.ok) {
          const payload = (await response.json()) as SessionResponse;
          setUsername(payload.username);
          setAuthStatus("authenticated");
          setErrorMessage(null);
          return;
        }

        if (response.status === 401) {
          setUsername(null);
          setAuthStatus("unauthenticated");
          setErrorMessage(null);
          return;
        }

        setUsername(null);
        setAuthStatus("unauthenticated");
        setErrorMessage(await getErrorMessage(response, "Unable to verify session."));
      } catch {
        if (!isMounted) {
          return;
        }

        setUsername(null);
        setAuthStatus("unauthenticated");
        setErrorMessage("Unable to reach the server.");
      }
    };

    void loadSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogin = async (nextUsername: string, password: string) => {
    setSubmitState("login");
    setErrorMessage(null);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: nextUsername, password }),
      });

      if (!response.ok) {
        setAuthStatus("unauthenticated");
        setErrorMessage(await getErrorMessage(response, "Unable to sign in."));
        return;
      }

      const payload = (await response.json()) as SessionResponse;
      setUsername(payload.username);
      setAuthStatus("authenticated");
    } catch {
      setAuthStatus("unauthenticated");
      setErrorMessage("Unable to sign in.");
    } finally {
      setSubmitState("idle");
    }
  };

  const handleLogout = async () => {
    setSubmitState("logout");
    setErrorMessage(null);

    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });

      if (!response.ok) {
        setErrorMessage(await getErrorMessage(response, "Unable to sign out."));
        return;
      }

      setUsername(null);
      setAuthStatus("unauthenticated");
    } catch {
      setErrorMessage("Unable to sign out.");
    } finally {
      setSubmitState("idle");
    }
  };

  if (authStatus === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6 py-10">
        <div className="rounded-[28px] border border-[var(--stroke)] bg-white/90 px-8 py-10 text-center shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Checking session
          </p>
          <p className="mt-4 text-sm text-[var(--gray-text)]">
            Loading your workspace.
          </p>
        </div>
      </main>
    );
  }

  if (authStatus === "authenticated" && username) {
    return (
      <KanbanBoard
        username={username}
        onLogout={handleLogout}
        isLoggingOut={submitState === "logout"}
      />
    );
  }

  return (
    <LoginForm
      onSubmit={handleLogin}
      isSubmitting={submitState === "login"}
      errorMessage={errorMessage}
    />
  );
};