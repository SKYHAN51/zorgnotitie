import "./globals.css";
import Nav from "@/components/Nav";

export const metadata = {
  title: "ZorgNotitie",
  description: "Demo met synthetische gegevens. Geen medisch hulpmiddel. Geen klinische besluitvorming.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body className="bg-slate-50 min-h-screen antialiased text-slate-900">
        <div className="bg-amber-100 text-amber-900 text-sm text-center py-2 px-4">
          Demo met synthetische gegevens. Geen medisch hulpmiddel. Geen klinische besluitvorming.
        </div>
        <Nav />
        {children}
      </body>
    </html>
  );
}
