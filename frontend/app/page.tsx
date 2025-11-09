import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-8 p-8">
        <div>
          <h1 className="text-5xl font-bold mb-4">FSD Studio</h1>
          <p className="text-xl text-muted-foreground">
            Your creative dashboard for managing projects
          </p>
        </div>

        <div className="flex gap-4 items-center justify-center flex-col sm:flex-row">
          <Link
            href="/auth/login"
            className="px-8 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity font-medium"
          >
            Get Started
          </Link>
          <Link
            href="/studio"
            className="px-8 py-3 bg-secondary text-secondary-foreground rounded-lg hover:opacity-90 transition-opacity font-medium"
          >
            Go to Studio
          </Link>
        </div>
      </div>
    </div>
  );
}
