import "./globals.css";
import Nav from "@/components/Nav";
import BackgroundDecor from "@/components/BackgroundDecor";

export const metadata = {
  title: "ZorgNotitie",
  description: "Demo met synthetische gegevens. Geen medisch hulpmiddel. Geen klinische besluitvorming.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body className="bg-cream-50 min-h-screen antialiased text-stone-800">
        <BackgroundDecor />
        <div className="bg-amber-50 border-b border-amber-200 text-amber-800 text-sm text-center py-2 px-4">
          Demo met synthetische gegevens. Geen medisch hulpmiddel. Geen klinische besluitvorming.
        </div>
        <Nav />
        {children}
      </body>
    </html>
  );
}
