import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/features/auth/AuthContext";
import { Header } from "@/components/ui/Header";

export const metadata: Metadata = {
  title: "RippleGuard — Explainable Open-Source Dependency Risk & Scenario Analysis",
  description:
    "Simulate downstream exposure from compromised software dependencies, evaluate counterfactual mitigations, and prioritize engineering repair with mathematical rigor.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-navy-950 text-slate-100 antialiased min-h-screen flex flex-col selection:bg-teal-500 selection:text-navy-950">
        <AuthProvider>
          <Header />
          <main className="flex-1 flex flex-col">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
