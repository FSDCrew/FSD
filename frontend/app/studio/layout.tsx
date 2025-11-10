import "aws-amplify/auth/enable-oauth-listener";
import ProtectedRoute from "@/components/ProtectedRoute"; // Adjust the path as needed

export default function studioLayout({children}: {children: React.ReactNode}) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  );
}