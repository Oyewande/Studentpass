import { useState, useRef, FormEvent, KeyboardEvent, ClipboardEvent } from "react";
import { verifyOTP } from "../services/api";

interface Props {
  email: string;
  campaignSlug: string;
  onSuccess: (coupon: string, lookupToken: string, expiresAt: string) => void;
  onBack: () => void;
}

export default function OTPForm({ email, campaignSlug, onSuccess, onBack }: Props) {
  const [digits, setDigits] = useState<string[]>(Array(6).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const otp = digits.join("");
  const isComplete = otp.length === 6 && digits.every((d) => d !== "");

  const handleDigitChange = (index: number, value: string) => {
    const char = value.replace(/\D/g, "").slice(-1);
    const newDigits = [...digits];
    newDigits[index] = char;
    setDigits(newDigits);
    setError("");

    if (char && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted) {
      const newDigits = Array(6).fill("").map((_, i) => pasted[i] || "");
      setDigits(newDigits);
      inputRefs.current[Math.min(pasted.length, 5)]?.focus();
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isComplete) return;
    setError("");
    setLoading(true);

    const result = await verifyOTP(email, otp, campaignSlug);
    setLoading(false);

    if (!result.ok) {
      setError(result.error);
      setDigits(Array(6).fill(""));
      inputRefs.current[0]?.focus();
      return;
    }
    onSuccess(result.data.coupon, result.data.lookup_token, result.data.expires_at ?? "");
  };

  const startResendCooldown = () => {
    setResendCooldown(60);
    const t = setInterval(() => {
      setResendCooldown((c) => {
        if (c <= 1) { clearInterval(t); return 0; }
        return c - 1;
      });
    }, 1000);
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    const { requestOTP } = await import("../services/api");
    await requestOTP(email, campaignSlug);
    startResendCooldown();
    setError("");
    setDigits(Array(6).fill(""));
    inputRefs.current[0]?.focus();
  };

  return (
    <div className="animate-slide-up w-full max-w-md">
      {/* Icon */}
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-2xl bg-brand-navy flex items-center justify-center shadow-lg">
          <span className="text-3xl">📬</span>
        </div>
      </div>

      <h1 className="text-2xl font-bold text-brand-dark text-center mb-2">
        Check Your Inbox
      </h1>
      <p className="text-brand-powder text-center mb-2 text-sm">
        We sent a 6-digit code to
      </p>
      <p className="text-brand-navy font-semibold text-center mb-8 text-sm">
        {email}
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 6-digit OTP input */}
        <div className="flex justify-center gap-2 sm:gap-3">
          {digits.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              onPaste={handlePaste}
              autoFocus={i === 0}
              className={`w-11 h-14 text-center text-xl font-bold rounded-xl border-2
                text-brand-dark outline-none transition-all
                focus:border-brand-navy focus:ring-2 focus:ring-brand-navy/20
                ${digit ? "border-brand-navy bg-brand-mint" : "border-brand-powder/40 bg-white"}
                ${error ? "border-red-400 bg-red-50" : ""}`}
            />
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl px-4 py-3 text-center">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !isComplete}
          className="w-full py-3.5 bg-brand-dark hover:bg-brand-navy text-white font-semibold
            rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              Verifying…
            </>
          ) : (
            "Unlock My Discount"
          )}
        </button>
      </form>

      <div className="mt-4 text-center space-y-2">
        <button
          onClick={handleResend}
          disabled={resendCooldown > 0}
          className="text-sm text-brand-navy hover:underline disabled:text-brand-powder disabled:no-underline disabled:cursor-not-allowed"
        >
          {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend code"}
        </button>
        <div>
          <button
            onClick={onBack}
            className="text-sm text-brand-powder hover:text-brand-dark transition-colors"
          >
            ← Use a different email
          </button>
        </div>
      </div>
    </div>
  );
}
