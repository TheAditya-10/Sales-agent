import { Activity, BadgeIndianRupee, Radio, Shield, Sparkles, Volume2 } from "lucide-react";
import { ChatWidget } from "@/components/ChatWidget";
import { TopNav } from "@/components/TopNav";

const carContext =
  "Mahindra XUV700 India, current-generation SUV, variants MX, AX Series, AX7 Luxury, petrol mStallion 2.0L, diesel mHawk 2.2L, ADAS, Skyroof, Sony 3D sound, Indian ex-showroom and on-road pricing context.";

const variants = [
  {
    label: "Essential",
    name: "MX Series",
    description: "The foundation of high-performance driving.",
    price: "₹13.99 Lakh",
    features: [
      { icon: Activity, text: "2.0L Turbo / 2.2L Diesel" },
      { icon: Radio, text: "Touchscreen Infotainment" },
    ],
  },
  {
    label: "Most Popular",
    name: "AX Series",
    description: "Adrenox intelligence for a connected experience.",
    price: "₹16.49 Lakh",
    active: true,
    features: [
      { icon: Shield, text: "ADAS Level 1" },
      { icon: Sparkles, text: "Skyroof Technology" },
    ],
  },
  {
    label: "Elite",
    name: "AX7 Luxury",
    description: "The pinnacle of engineering and comfort.",
    price: "₹23.99 Lakh",
    features: [
      { icon: Sparkles, text: "ADAS Level 2 suite" },
      { icon: Volume2, text: "Sony 3D Sound System" },
    ],
  },
];

const specs = [
  ["Engine Displacement", "2.0 L", "2.2 L"],
  ["Max Power", "147 kW (200 PS) @ 5000 r/min", "136 kW (185 PS) @ 3500 r/min"],
  ["Max Torque", "380 Nm @ 1750-3000 r/min", "420 Nm @ 1600-2800 r/min"],
  ["Transmission", "6-Speed MT / 6-Speed AT", "6-Speed MT / 6-Speed AT / AWD"],
];

export default function Xuv700Page() {
  return (
    <main className="min-h-screen bg-background text-on-background">
      <TopNav />

      <section className="relative flex min-h-[80vh] w-full flex-col items-center justify-center overflow-hidden py-section-gap">
        <div className="absolute inset-0 z-0">
          <img
            alt="White Mahindra XUV700 in premium studio lighting"
            className="h-full w-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDnhzBw-AAazQdvuWl6vY6kIeCRpaeMookKOoJ0OvYW-V1A-Jtntk6YOP9aOlU9XJqlAVe3Gcdph7EPmi9wgd8981pRIhVFmvSvEtQptdrL5v6qHq3Mw6AVFhDezg8Wf_zZT1Gj6z0VhkE6iwZyEz4a4z6LZnRIRlXRpsUJ5i215_5WQUACOONbnCTwhY-XmfzgsrikzxCE72lzQHAjIQcj2DWrb6Vph4iWZeFjAgMEjILEau6lGeft6w"
          />
        </div>
        <div className="relative z-10 mx-auto flex h-full w-full max-w-container-max items-end px-margin-mobile md:px-margin-desktop">
          <div className="max-w-xl rounded-lg border border-outline-variant bg-surface/80 p-8 shadow-fintech-lg backdrop-blur-md md:p-10">
            <span className="mb-2 block font-mono text-xs font-medium uppercase text-secondary">
              Premium Performance
            </span>
            <h1 className="mb-4 text-4xl font-bold leading-tight text-primary md:text-5xl">
              Mahindra XUV700
            </h1>
            <p className="mb-6 text-lg leading-8 text-on-surface-variant">
              Experience the future of mobility with world-class ADAS and luxurious performance.
              Starting at ₹13.99 Lakh.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row">
              <button className="rounded-lg bg-primary px-8 py-4 text-sm font-medium text-on-primary shadow-fintech-lg transition active:opacity-80">
                Book Test Drive
              </button>
              <a
                href="#variants"
                className="rounded-lg border border-outline px-8 py-4 text-center text-sm font-medium text-primary transition hover:bg-surface-variant"
              >
                Explore Variants
              </a>
            </div>
          </div>
        </div>
      </section>

      <section id="variants" className="mx-auto max-w-container-max px-margin-mobile py-section-gap md:px-margin-desktop">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-semibold text-primary">Sophisticated Variants</h2>
          <p className="mx-auto max-w-2xl text-secondary">
            Choose the configuration that matches your lifestyle, from city commuting to long-range luxury.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-gutter md:grid-cols-3">
          {variants.map((variant) => (
            <article
              key={variant.name}
              className={`relative overflow-hidden rounded-lg border p-stack-lg transition ${
                variant.active
                  ? "border-primary bg-primary-container text-white shadow-fintech-lg"
                  : "border-outline-variant bg-white shadow-fintech hover:shadow-fintech-lg"
              }`}
            >
              {variant.active ? (
                <div className="absolute -right-4 -top-4 h-32 w-32 rounded-full bg-primary opacity-20 blur-2xl" />
              ) : null}
              <span
                className={`mb-6 inline-block rounded-full px-3 py-1 font-mono text-[10px] uppercase ${
                  variant.active ? "bg-primary text-on-primary" : "bg-surface-container-high text-primary"
                }`}
              >
                {variant.label}
              </span>
              <h3 className={`mb-2 text-xl font-semibold ${variant.active ? "text-white" : "text-primary"}`}>
                {variant.name}
              </h3>
              <p className={`mb-6 h-12 ${variant.active ? "text-on-primary-container" : "text-secondary"}`}>
                {variant.description}
              </p>
              <div className="mb-8 space-y-4">
                {variant.features.map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-2">
                    <Icon size={18} className={variant.active ? "text-white" : "text-primary"} />
                    <span className={variant.active ? "text-sm text-white" : "text-sm text-on-surface"}>
                      {text}
                    </span>
                  </div>
                ))}
              </div>
              <div className={`border-t pt-6 ${variant.active ? "border-on-primary-container" : "border-outline-variant"}`}>
                <span className={`block font-mono text-xs uppercase ${variant.active ? "text-on-primary-container" : "text-secondary"}`}>
                  Starting at
                </span>
                <span className={`text-xl font-semibold ${variant.active ? "text-white" : "text-primary"}`}>
                  {variant.price}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="bg-surface-container-low py-section-gap">
        <div className="mx-auto max-w-container-max px-margin-mobile md:px-margin-desktop">
          <h2 className="mb-12 text-center text-3xl font-semibold text-primary">
            Technical Specifications
          </h2>
          <div className="overflow-hidden rounded-lg border border-outline-variant bg-white shadow-fintech">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-outline-variant bg-surface-container">
                    <th className="px-8 py-6 font-mono text-xs uppercase text-secondary">Feature</th>
                    <th className="px-8 py-6 font-mono text-xs uppercase text-secondary">
                      mStallion Turbo Petrol
                    </th>
                    <th className="px-8 py-6 font-mono text-xs uppercase text-secondary">mHawk Diesel</th>
                  </tr>
                </thead>
                <tbody className="text-on-surface">
                  {specs.map(([feature, petrol, diesel]) => (
                    <tr key={feature} className="border-b border-outline-variant transition hover:bg-surface-bright">
                      <td className="px-8 py-6 font-semibold">{feature}</td>
                      <td className="px-8 py-6">{petrol}</td>
                      <td className="px-8 py-6">{diesel}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-container-max grid-cols-1 gap-gutter px-margin-mobile py-section-gap md:grid-cols-[1.2fr_0.8fr] md:px-margin-desktop">
        <div>
          <p className="mb-2 font-mono text-xs uppercase text-secondary">AI assisted retail</p>
          <h2 className="mb-4 text-3xl font-semibold text-primary">Every answer stays attached to this car.</h2>
          <p className="max-w-2xl leading-7 text-on-surface-variant">
            The widget silently injects the XUV700 catalog context into every request, so the buyer
            can ask natural questions about ADAS, variants, competitors, or price without repeating
            the model name.
          </p>
        </div>
        <div className="rounded-lg border border-outline-variant bg-white p-stack-lg shadow-fintech">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-container text-primary">
              <BadgeIndianRupee size={20} />
            </div>
            <div>
              <p className="font-mono text-xs uppercase text-secondary">Demo sources</p>
              <p className="font-semibold text-primary">Mahindra, CarWale, CarDekho, ZigWheels</p>
            </div>
          </div>
          <p className="text-sm leading-6 text-on-surface-variant">
            If retrieval cannot confirm a claim, the backend returns a transparent fallback instead of a fabricated number.
          </p>
        </div>
      </section>

      <footer className="bg-surface-container">
        <div className="mx-auto flex max-w-container-max flex-col items-center justify-between gap-8 px-margin-mobile py-section-gap md:flex-row md:px-margin-desktop">
          <div className="text-3xl font-semibold text-primary">AutoElite</div>
          <div className="flex flex-wrap justify-center gap-6 text-sm font-medium text-on-secondary-container">
            <span>Privacy Policy</span>
            <span>Terms of Service</span>
            <span>Contact</span>
            <span>Careers</span>
          </div>
          <div className="text-sm text-on-surface">© 2026 AutoElite Fintech.</div>
        </div>
      </footer>

      <ChatWidget carContext={carContext} />
    </main>
  );
}
