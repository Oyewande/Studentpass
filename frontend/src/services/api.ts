// In local dev: Vite proxies /api → localhost:8000 (see vite.config.ts)
// In production: VITE_API_URL is set to the Railway backend URL on Vercel
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

async function post<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) {
      const message =
        typeof json.error === "string"
          ? json.error
          : "Something went wrong. Please try again.";
      return { ok: false, error: message };
    }
    return { ok: true, data: json as T };
  } catch {
    return { ok: false, error: "Network error. Please check your connection." };
  }
}

export interface CampaignInfo {
  name: string;
  description: string;
  allowed_domains: string[];
  product_url: string;
}

export const getCampaignInfo = async (
  slug: string
): Promise<ApiResult<CampaignInfo>> => {
  try {
    const res = await fetch(`${BASE_URL}/campaign/${slug}/`);
    const json = await res.json();
    if (!res.ok) {
      return { ok: false, error: json.error ?? "Campaign not found." };
    }
    return { ok: true, data: json as CampaignInfo };
  } catch {
    return { ok: false, error: "Network error. Please check your connection." };
  }
};

export const requestOTP = (email: string, campaign: string) =>
  post<{ message: string }>("/request-otp/", { email, campaign });

export const verifyOTP = (email: string, otp: string, campaign: string) =>
  post<{ message: string; coupon: string; lookup_token: string; expires_at: string }>(
    "/verify-otp/",
    { email, otp, campaign }
  );

export const getCoupon = async (
  email: string,
  token: string
): Promise<ApiResult<{ coupon: string }>> => {
  try {
    const params = new URLSearchParams({ email, token });
    const res = await fetch(`${BASE_URL}/get-coupon/?${params.toString()}`);
    const json = await res.json();
    if (!res.ok) {
      return { ok: false, error: json.error ?? "Not found." };
    }
    return { ok: true, data: json };
  } catch {
    return { ok: false, error: "Network error. Please check your connection." };
  }
};
