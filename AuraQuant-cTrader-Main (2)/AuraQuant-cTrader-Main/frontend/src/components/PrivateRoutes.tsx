import { Outlet } from "react-router-dom";

const ProtectedRoute = () => {
    // This component is now a simple pass-through.
    // The protection logic has been moved to a layout component in App.tsx
    // for better compatibility with the React Router v6 rendering order.
    return <Outlet />;
};

export default ProtectedRoute;
