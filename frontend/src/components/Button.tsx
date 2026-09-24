import { ButtonHTMLAttributes } from "react";

export default function Button({
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
