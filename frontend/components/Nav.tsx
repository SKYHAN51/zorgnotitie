"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mic, ClipboardCheck, LayoutGrid, Leaf } from "lucide-react";

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
    <nav className="bg-cream-50/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-3xl mx-auto px-6 flex items-center gap-6 h-16">
        <span className="flex items-center gap-1.5 font-semibold text-stone-800 tracking-tight">
          <Leaf size={18} className="text-sage-600" strokeWidth={2.25} />
          ZorgNotitie
        </span>
        <div className="flex items-center gap-1 ml-auto">
          {ITEMS.map((item) => {
            const active = item.match(pathname ?? "");
            const Icon = item.icon;
            const content = (
              <span
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-full text-sm font-medium transition-colors ${
                  active
                    ? "bg-sage-600 text-white shadow-softer"
                    : item.href
                      ? "text-stone-500 hover:text-stone-800 hover:bg-stone-900/5"
                      : "text-stone-300 cursor-default"
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
