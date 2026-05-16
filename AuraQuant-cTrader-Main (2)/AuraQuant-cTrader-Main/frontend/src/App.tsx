import { lazy, Suspense } from 'react';
// Providers
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";

// Page Components (Lazy Loaded)
const Index = lazy(() => import('./pages/Index'));
const Marketplace = lazy(() => import('./pages/Marketplace'));
const RobotDetails = lazy(() => import('./pages/RobotDetails'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Products = lazy(() => import('./pages/Products'));
const Academy = lazy(() => import('./pages/Academy'));
const About = lazy(() => import('./pages/About'));
const Contact = lazy(() => import('./pages/Contact'));
const Login = lazy(() => import('./pages/LoginPage'));
const Register = lazy(() => import('./pages/RegisterPage'));
const Blog = lazy(() => import('./pages/Blog'));
const Documentation = lazy(() => import('./pages/Documentation'));
const Support = lazy(() => import('./pages/Support'));
const Status = lazy(() => import('./pages/Status'));
const Downloads = lazy(() => import('./pages/Downloads'));
const Partners = lazy(() => import('./pages/Partners'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Community = lazy(() => import('./pages/Community'));
const Onboarding = lazy(() => import('./pages/Onboarding'));
const NotFound = lazy(() => import('./pages/NotFound'));
const MyAccounts = lazy(() => import('./pages/MyAccounts'));
const TradingHistory = lazy(() => import('./pages/TradingHistory'));
const VerifyEmailSent = lazy(() => import('./pages/VerifyEmailSentPage'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmailPage'));


const queryClient = new QueryClient();

// Simple loading fallback component
const LoadingFallback = () => (
  <div className="w-full h-screen flex items-center justify-center bg-background">
    <div className="text-foreground">Carregando...</div>
  </div>
);

// New Private Layout Component
const PrivateLayout = () => {
  const { isAuthenticated, isInitialized } = useAuth();

  // Wait until the auth state is initialized
  if (!isInitialized) {
    // You can render a loading spinner here if you want
    return null; 
  }

  // If not authenticated, redirect to the login page
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If authenticated, render the child routes
  return <Outlet />; 
};


const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Sonner />
        <BrowserRouter>
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Index />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/verify-email-sent" element={<VerifyEmailSent />} />
              <Route path="/verify-email" element={<VerifyEmail />} />
              <Route path="/marketplace" element={<Marketplace />} />
              <Route path="/marketplace/strategy/:id" element={<RobotDetails />} />
              <Route path="/products" element={<Products />} />
              <Route path="/academy" element={<Academy />} />
              <Route path="/about" element={<About />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/documentation" element={<Documentation />} />
              <Route path="/support" element={<Support />} />
              <Route path="/status" element={<Status />} />
              <Route path="/downloads" element={<Downloads />} />
              <Route path="/partners" element={<Partners />} />
              <Route path="/community" element={<Community />} />

              {/* Protected Routes using the new PrivateLayout */}
              <Route element={<PrivateLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/my-accounts" element={<MyAccounts />} />
                <Route path="/trading-history" element={<TradingHistory />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/onboarding" element={<Onboarding />} />
              </Route>

              {/* Catch-all Not Found Route */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
