import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "@layouts/mainLayout";

function Dashboard() {
  return <h2>Dashboard page</h2>;
}

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
