import * as React from "react"
import { cn } from "@/utils/cn"

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "primary" | "danger" | "success" | "outline";
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    let variantStyles = "bg-muted/10 text-muted-foreground border-border";
    
    if (variant === "primary") variantStyles = "bg-primary/10 text-primary border-primary/20 glow-primary";
    if (variant === "danger") variantStyles = "bg-danger/10 text-danger border-danger/20";
    if (variant === "success") variantStyles = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    if (variant === "outline") variantStyles = "bg-transparent text-foreground border-border";

    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest transition-colors",
          variantStyles,
          className
        )}
        {...props}
      />
    )
  }
)
Badge.displayName = "Badge"

export { Badge }
