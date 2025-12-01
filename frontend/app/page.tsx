import Link from "next/link";
import Image from 'next/image'

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-8 p-8">
        <div className="flex flex-col items-center space-y-4">
          <Image 
            src="/logo-black.png" 
            alt="Company Logo" 
            width={300} 
            height={100}
            className="mx-auto"
          />
          <p className="text-xl text-muted-foreground">
            Your Marketing Studio
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
