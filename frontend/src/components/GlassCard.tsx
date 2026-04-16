import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  bordered?: boolean;
  accentBar?: boolean;
}

const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, hoverEffect = true, bordered = true, accentBar = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative p-6 md:p-8 overflow-hidden transition-[border-color] duration-150",
          bordered && "border border-[var(--border)]",
          hoverEffect && "hover:border-[var(--border-hover)]",
          className
        )}
        {...props}
      >
        {accentBar && (
          <div className="absolute top-0 left-0 h-[2px] w-16 bg-[var(--accent)]" />
        )}
        {children}
      </div>
    );
  }
);
GlassCard.displayName = "GlassCard";

export default GlassCard;
