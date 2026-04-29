import { useState, FormEvent } from "react";
import { requestOTP, CampaignInfo } from "../services/api";

interface Props {
  onNext: (email: string) => void;
  campaign: CampaignInfo;
  campaignSlug: string;
}

export default function EmailForm({ onNext, campaign, campaignSlug }: Props) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const domain = email.includes("@") ? email.split("@")[1].toLowerCase() : "";
  const domainValid = campaign.allowed_domains.includes(domain);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await requestOTP(email.trim().toLowerCase(), campaignSlug);
    setLoading(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }
    onNext(email.trim().toLowerCase());
  };

  return (
    <div className="animate-slide-up w-full max-w-md">
      {/* Icon */}
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-2xl bg-brand-navy flex items-center justify-center shadow-lg">
          <span className="text-3xl">🎓</span>
        </div>
      </div>

      <h1 className="text-2xl font-bold text-brand-dark text-center mb-2">
        {campaign.name}
      </h1>
      <p className="text-brand-powder text-center mb-2 text-sm leading-relaxed">
        {campaign.description || "Verify your university email to unlock your exclusive discount code."}
      </p>
      <p className="text-brand-navy font-medium text-center mb-8 text-xs">
        {campaign.allowed_domains.join(" · ")}
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-brand-dark mb-1.5"
          >
            School Email Address
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError("");
            }}
            placeholder={`yourname@${campaign.allowed_domains[0] ?? "university.edu.ng"}`}
            required
            className={`w-full px-4 py-3 rounded-xl border text-brand-dark placeholder-brand-powder/60
              bg-white text-sm transition-all outline-none
              focus:ring-2 focus:ring-brand-navy focus:border-transparent
              ${error ? "border-red-400 bg-red-50" : "border-brand-powder/40"}`}
          />

          {/* Domain indicator */}
          {email.includes("@") && (
            <p
              className={`mt-1.5 text-xs flex items-center gap-1 ${domainValid ? "text-green-600" : "text-red-500"
                }`}
            >
              {domainValid ? "✓ Recognised university domain" : "✗ Unrecognised domain"}
            </p>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl px-4 py-3">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !email}
          className="w-full py-3.5 bg-brand-dark hover:bg-brand-navy text-white font-semibold
            rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Sending OTP…
            </>
          ) : (
            <>Send Verification Code</>
          )}
        </button>
      </form>
    </div>
  );
}
