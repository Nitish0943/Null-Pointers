import * as React from "react"
import { cn } from "@/utils/cn"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "danger" | "ghost" | "outline";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    let variantStyles = "bg-muted text-muted-foreground border-border hover:bg-muted/80";
    
    if (variant === "primary") variantStyles = "bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20 hover:scale-[1.02] hover:bg-primary/90";
    if (variant === "danger") variantStyles = "bg-danger text-white border-danger hover:bg-danger/90 shadow-lg shadow-danger/20";
    if (variant === "ghost") variantStyles = "bg-transparent text-foreground hover:bg-accent/10 hover:text-accent border-transparent";
    if (variant === "outline") variantStyles = "bg-transparent text-foreground border-border hover:bg-muted/10";

    let sizeStyles = "h-10 px-4 py-2 text-[10px]";
    if (size === "sm") sizeStyles = "h-8 rounded-lg px-3 text-[9px]";
    if (size === "lg") sizeStyles = "h-12 rounded-2xl px-8 text-xs";
    if (size === "icon") sizeStyles = "h-10 w-10 p-2 flex items-center justify-center";

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-xl border font-black uppercase tracking-[0.2em] transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50",
          variantStyles,
          sizeStyles,
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
