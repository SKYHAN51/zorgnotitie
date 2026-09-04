import { Leaf } from "lucide-react";

/** Purely decorative — very low-opacity leaf motif so pages don't feel
 * empty. Fixed behind all content, never intercepts clicks or affects
 * layout/reading order (aria-hidden, pointer-events-none). */
export default function BackgroundDecor() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none" aria-hidden="true">
      <Leaf
        className="absolute -right-24 -top-16 text-sage-600/[0.06] rotate-[18deg]"
        size={420}
        strokeWidth={1}
      />
      <Leaf
        className="absolute -left-32 bottom-[-4rem] text-sage-600/[0.05] -rotate-[24deg]"
        size={380}
        strokeWidth={1}
      />
      <Leaf
        className="absolute left-1/2 top-1/3 text-sage-600/[0.03] rotate-[8deg]"
        size={260}
        strokeWidth={1}
      />
    </div>
  );
}
