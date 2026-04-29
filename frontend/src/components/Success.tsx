import { useState } from "react";

interface Props {
  coupon: string;
  productUrl?: string;
  /** ISO-8601 expiry timestamp returned by the API — e.g. "2026-04-29T14:30:00+01:00" */
  expiresAt?: string;
}

function formatExpiry(iso: string): { label: string; urgent: boolean } {
  const expiry = new Date(iso);
  const now = new Date();
  const msLeft = expiry.getTime() - now.getTime();
  const hoursLeft = msLeft / (1000 * 60 * 60);

  const formatted = expiry.toLocaleString("en-NG", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return {
    label: `Expires ${formatted}`,
    urgent: hoursLeft < 4,   // turn red when fewer than 4 hours remain
  };
}

export default function Success({
  coupon,
  productUrl = "#",
  expiresAt,
}: Props) {
  const [copied, setCopied] = useState(false);

  const expiry = expiresAt ? formatExpiry(expiresAt) : null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(coupon);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      const el = document.getElementById("coupon-code");
      if (el) {
        const range = document.createRange();
        range.selectNode(el);
        window.getSelection()?.removeAllRanges();
        window.getSelection()?.addRange(range);
      }
    }
  };

  return (
    <div className="animate-slide-up w-full max-w-md text-center">
      {/* Celebration icon */}
      <div className="flex justify-center mb-6">
        <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center shadow-lg">
          <span className="text-4xl">🎉</span>
        </div>
      </div>

      <h1 className="text-2xl font-bold text-brand-dark mb-2">
        You're Verified!
      </h1>
      <p className="text-brand-powder text-sm mb-8">
        Your exclusive student discount code is ready. Copy it and use it at checkout.
      </p>

      {/* Coupon card */}
      <div className="relative bg-gradient-to-br from-brand-dark to-brand-navy rounded-2xl p-6 mb-3 shadow-xl overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-white/5 -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-24 h-24 rounded-full bg-white/5 translate-y-1/2 -translate-x-1/2" />

        <p className="text-brand-powder/70 text-xs uppercase tracking-widest mb-3">
          Discount Code
        </p>
        <p
          id="coupon-code"
          className="text-white text-3xl font-bold tracking-wider font-mono mb-4"
        >
          {coupon}
        </p>
        <button
          onClick={handleCopy}
          className="flex items-center gap-2 mx-auto bg-white/10 hover:bg-white/20
            text-white text-sm font-medium px-4 py-2 rounded-lg transition-all duration-200"
        >
          {copied ? (
            <>
              <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Copy Code
            </>
          )}
        </button>
      </div>

      {/* Expiry badge */}
      {expiry && (
        <div
          className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full mb-4
            ${expiry.urgent
              ? "bg-red-100 text-red-600 border border-red-200"
              : "bg-amber-50 text-amber-700 border border-amber-200"
            }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx="12" cy="12" r="10"/>
            <path strokeLinecap="round" d="M12 6v6l4 2"/>
          </svg>
          {expiry.label}
        </div>
      )}

      {/* Instruction */}
      <p className="text-brand-powder text-xs mb-6">
        Paste this code at Selar checkout to apply your discount.
      </p>

      {/* CTA */}
      <a
        href={productUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="block w-full py-4 bg-green-600 hover:bg-green-700 text-white font-bold
          rounded-xl transition-all duration-200 shadow-md hover:shadow-lg text-sm"
      >
        Go to Store and Redeem →
      </a>

      <p className="mt-4 text-xs text-brand-powder/60">
        This code is unique to your student email and can only be used once.
      </p>
    </div>
  );
}
