const base =
  "inline-flex items-center justify-center rounded-control font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50";

const variants = {
  primary:
    "bg-primary text-white not-disabled:hover:brightness-95 not-disabled:active:brightness-90",
  secondary:
    "border border-primary bg-card text-primary not-disabled:hover:bg-primary-tint",
};

const sizes = {
  small: "h-8 px-3 text-xs",
  medium: "h-11 px-5 text-sm",
};

export function buttonClassName(
  variant: keyof typeof variants = "primary",
  size: keyof typeof sizes = "medium"
) {
  return `${base} ${variants[variant]} ${sizes[size]}`;
}
