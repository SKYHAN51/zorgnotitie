"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mic, ClipboardCheck, LayoutGrid } from "lucide-react";

const ITEMS = [
  { href: "/", label: "Opnemen", icon: Mic, match: (p: string) => p === "/" },
  {
    href: null,
    label: "Controleren",
    icon: ClipboardCheck,
    match: (p: string) => p.startsWith("/review"),
  },
  {
    href: "/dashboard",
    label: "Teamoverzicht",
    icon: LayoutGrid,
    match: (p: string) => p.startsWith("/dashboard"),
  },
] as const;

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="max-w-3xl mx-auto px-6 flex items-center gap-6 h-14">
        <span className="font-semibold text-slate-900 tracking-tight">ZorgNotitie</span>
        <div className="flex items-center gap-1 ml-auto">
          {ITEMS.map((item) => {
            const active = item.match(pathname ?? "");
            const Icon = item.icon;
            const content = (
              <span
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal-50 text-teal-700"
                    : item.href
                      ? "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                      : "text-slate-300 cursor-default"
                }`}
              >
                <Icon size={16} />
                {item.label}
              </span>
            );
            return item.href ? (
              <Link key={item.label} href={item.href}>
                {content}
              </Link>
            ) : (
              <span key={item.label}>{content}</span>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
