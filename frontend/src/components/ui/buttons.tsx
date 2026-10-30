// Кнопки (UI-DESIGN §15): синя (одна на екран), звичайна, м'яка, тиха, небезпечна; висоти 30 / 36 / 44.
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

type Variant = "primary" | "default" | "soft" | "quiet" | "danger";
type Size = 30 | 32 | 36 | 44;

export type ButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
  variant?: Variant;
  size?: Size;
  icon?: LucideIcon;
  /** Клавіша поруч із підписом: «Ctrl S», «N». */
  kbd?: string;
  wide?: boolean;
  children?: ReactNode;
};

const SIZE_CLASS: Record<Size, string> = { 30: "s30", 32: "", 36: "s36", 44: "s44" };
const ICON_SIZE: Record<Size, number> = { 30: 14, 32: 15, 36: 16, 44: 18 };

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "default", size = 32, icon: Icon, kbd, wide, className = "", children, type = "button", ...rest }, ref,
) {
  const cls = ["btn", variant === "default" ? "" : variant, SIZE_CLASS[size], wide ? "wide" : "", !children && Icon ? "icon" : "", className]
    .filter(Boolean).join(" ");
  return (
    <button ref={ref} type={type} className={cls} {...rest}>
      {Icon && <Icon size={ICON_SIZE[size]} strokeWidth={1.9} aria-hidden />}
      {children}
      {kbd && <kbd>{kbd}</kbd>}
    </button>
  );
});

export type IconButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
  icon: LucideIcon;
  /** Підпис для читача екрана й підказка при наведенні — обов'язковий. */
  label: string;
  size?: 28 | 32 | 36 | 44;
  quiet?: boolean;
  /** Лічильник у куті (історія, сповіщення). */
  count?: number;
};

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { icon: Icon, label, size = 32, quiet, count, className = "", type = "button", ...rest }, ref,
) {
  const cls = ["icon-btn", size === 32 ? "" : `s${size}`, quiet ? "quiet" : "", className].filter(Boolean).join(" ");
  return (
    <button ref={ref} type={type} className={cls} aria-label={label} title={label} {...rest} style={{ position: "relative", ...rest.style }}>
      <Icon size={size >= 36 ? 18 : 16} strokeWidth={1.9} aria-hidden />
      {!!count && <span className="ib-count" aria-hidden>{count > 99 ? "99+" : count}</span>}
    </button>
  );
});
