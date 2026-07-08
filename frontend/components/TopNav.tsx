import Link from "next/link";

export function TopNav({ panel = false }: { panel?: boolean }) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-outline-variant bg-surface shadow-sm">
      <nav className="mx-auto flex h-20 max-w-container-max items-center justify-between px-margin-mobile md:px-margin-desktop">
        <div className="flex items-center gap-12">
          <Link href="/cars/xuv700" className="text-xl font-bold text-primary">
            AutoElite
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            <Link
              href="/cars/xuv700"
              className="text-sm font-medium text-primary"
            >
              Catalog
            </Link>
            <span className="text-sm font-medium text-secondary">Features</span>
            <span className="text-sm font-medium text-secondary">Financing</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          {panel ? (
            <div className="hidden flex-col items-end md:flex">
              <span className="text-sm font-bold text-primary">Consultant Panel</span>
              <span className="font-mono text-[11px] uppercase text-on-secondary-container">
                Logged in: Vikram Singh
              </span>
            </div>
          ) : null}
          <Link
            href="/consultant"
            className="rounded-full bg-primary px-5 py-2 text-sm font-medium text-on-primary transition hover:opacity-90 md:px-6"
          >
            Consultant Login
          </Link>
        </div>
      </nav>
    </header>
  );
}
