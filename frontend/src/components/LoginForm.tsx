"use client";

import { useState, type FormEvent } from "react";

type LoginFormProps = {
  onSubmit: (username: string, password: string) => Promise<void> | void;
  isSubmitting: boolean;
  errorMessage: string | null;
};

export const LoginForm = ({
  onSubmit,
  isSubmitting,
  errorMessage,
}: LoginFormProps) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit(username.trim(), password);
  };

  return (
    <div className="relative overflow-hidden bg-[var(--surface)]">
      <div className="pointer-events-none absolute left-0 top-0 h-[360px] w-[360px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.2)_0%,_rgba(32,157,215,0.05)_55%,_transparent_72%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[420px] w-[420px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.14)_0%,_rgba(117,57,145,0.04)_55%,_transparent_76%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1200px] items-center justify-center px-6 py-12">
        <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-[32px] border border-[var(--stroke)] bg-white/85 p-8 shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Project Management MVP
            </p>
            <h1 className="mt-4 font-display text-4xl font-semibold text-[var(--navy-dark)]">
              Sign in to continue
            </h1>
            <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--gray-text)]">
              This MVP uses a single demo account before the persistent backend
              board is wired in. Once signed in, you will land on the current
              Kanban workspace.
            </p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Username
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  user
                </p>
              </div>
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Password
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--secondary-purple)]">
                  password
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-[32px] border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label
                  className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]"
                  htmlFor="username"
                >
                  Username
                </label>
                <input
                  id="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  className="mt-3 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                  autoComplete="username"
                  required
                />
              </div>
              <div>
                <label
                  className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]"
                  htmlFor="password"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="mt-3 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                  autoComplete="current-password"
                  required
                />
              </div>

              {errorMessage ? (
                <div
                  className="rounded-2xl border border-[rgba(117,57,145,0.2)] bg-[rgba(117,57,145,0.08)] px-4 py-3 text-sm text-[var(--navy-dark)]"
                  role="alert"
                >
                  {errorMessage}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? "Signing in..." : "Sign in"}
              </button>
            </form>
          </section>
        </div>
      </main>
    </div>
  );
};