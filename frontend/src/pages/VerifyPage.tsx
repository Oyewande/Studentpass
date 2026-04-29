import { useState, useEffect } from "react";
import EmailForm from "../components/EmailForm";
import OTPForm from "../components/OTPForm";
import Success from "../components/Success";
import { getCampaignInfo, CampaignInfo } from "../services/api";

type Step = "email" | "otp" | "success";

interface VerifyState {
  step: Step;
  email: string;
  coupon: string;
  lookupToken: string;
  expiresAt: string;
}

interface Props {
  campaignSlug: string;
}

export default function VerifyPage({ campaignSlug }: Props) {
  const [campaign, setCampaign] = useState<CampaignInfo | null>(null);
  const [campaignLoading, setCampaignLoading] = useState(true);
  const [campaignError, setCampaignError] = useState("");

  const [state, setState] = useState<VerifyState>({
    step: "email",
    email: "",
    coupon: "",
    lookupToken: "",
    expiresAt: "",
  });

  useEffect(() => {
    if (!campaignSlug) {
      setCampaignLoading(false);
      setCampaignError("No campaign specified.");
      return;
    }
    getCampaignInfo(campaignSlug).then((result) => {
      setCampaignLoading(false);
      if (result.ok) {
        setCampaign(result.data);
      } else {
        setCampaignError(result.error);
      }
    });
  }, [campaignSlug]);

  const goToOTP = (email: string) =>
    setState((s) => ({ ...s, step: "otp", email }));

  const goToSuccess = (coupon: string, lookupToken: string, expiresAt: string) =>
    setState((s) => ({ ...s, step: "success", coupon, lookupToken, expiresAt }));

  const goBack = () => setState((s) => ({ ...s, step: "email" }));

  return (
    <div
      className="min-h-screen bg-gradient-to-br from-brand-mint via-white to-brand-mint
        flex flex-col items-center justify-center px-4 py-12"
    >
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl p-8 sm:p-10">

        {/* Loading state */}
        {campaignLoading && (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <svg className="animate-spin h-8 w-8 text-brand-navy" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            <p className="text-brand-powder text-sm">Loading…</p>
          </div>
        )}

        {/* Campaign not found */}
        {!campaignLoading && campaignError && (
          <div className="flex flex-col items-center justify-center py-12 gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-red-100 flex items-center justify-center">
              <span className="text-3xl">🔒</span>
            </div>
            <h1 className="text-xl font-bold text-brand-dark">Campaign Not Found</h1>
            <p className="text-brand-powder text-sm">
              This discount link is invalid or has expired. Please contact the organiser for a valid link.
            </p>
          </div>
        )}

        {/* Main verification flow */}
        {!campaignLoading && campaign && (
          <>
            {/* Progress dots */}
            <div className="flex justify-center gap-2 mb-8">
              {(["email", "otp", "success"] as Step[]).map((s) => (
                <div
                  key={s}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    s === state.step
                      ? "w-8 bg-brand-navy"
                      : state.step === "success" || (state.step === "otp" && s === "email")
                      ? "w-4 bg-brand-powder"
                      : "w-4 bg-brand-powder/30"
                  }`}
                />
              ))}
            </div>

            {state.step === "email" && (
              <EmailForm
                onNext={goToOTP}
                campaign={campaign}
                campaignSlug={campaignSlug}
              />
            )}
            {state.step === "otp" && (
              <OTPForm
                email={state.email}
                campaignSlug={campaignSlug}
                onSuccess={goToSuccess}
                onBack={goBack}
              />
            )}
            {state.step === "success" && (
              <Success
                coupon={state.coupon}
                productUrl={campaign.product_url}
                expiresAt={state.expiresAt}
              />
            )}
          </>
        )}
      </div>

      <p className="mt-6 text-xs text-brand-powder/60 text-center">
        Powered by <span className="font-semibold text-brand-powder">StudentPass</span> · Student Verification
      </p>
    </div>
  );
}
