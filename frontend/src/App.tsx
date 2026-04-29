import VerifyPage from "./pages/VerifyPage";

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const campaignSlug = params.get("c") ?? "";

  return <VerifyPage campaignSlug={campaignSlug} />;
}
