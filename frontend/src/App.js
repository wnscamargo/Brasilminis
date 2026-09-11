import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";

import { AuthProvider } from "@/context/AuthContext";
import { SiteConfigProvider } from "@/context/SiteConfigContext";
import { CartProvider } from "@/context/CartContext";
import { FavoritesProvider } from "@/context/FavoritesContext";
import { ProtectedRoute, ScrollToTop } from "@/components/Guards";
import MaintenanceGate from "@/components/MaintenanceGate";
import Layout from "@/components/layout/Layout";
import UnderConstruction from "@/pages/UnderConstruction";

import Home from "@/pages/Home";
import Catalog from "@/pages/Catalog";
import ProductDetail from "@/pages/ProductDetail";
import Cart from "@/pages/Cart";
import Checkout from "@/pages/Checkout";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Account from "@/pages/Account";
import Favorites from "@/pages/Favorites";
import Brands from "@/pages/Brands";
import Contact from "@/pages/Contact";
import { ForgotPassword, ResetPassword } from "@/pages/PasswordRecovery";

import AdminLayout from "@/pages/admin/AdminLayout";
import Dashboard from "@/pages/admin/Dashboard";
import AdminProducts from "@/pages/admin/AdminProducts";
import AdminCategories from "@/pages/admin/AdminCategories";
import AdminBrands from "@/pages/admin/AdminBrands";
import AdminOrders from "@/pages/admin/AdminOrders";
import AdminCustomers from "@/pages/admin/AdminCustomers";
import AdminBanners from "@/pages/admin/AdminBanners";
import AdminSite from "@/pages/admin/AdminSite";
import AdminBranding from "@/pages/admin/AdminBranding";
import AdminMelhorEnvio from "@/pages/admin/AdminMelhorEnvio";

const Shell = ({ children }) => <Layout>{children}</Layout>;

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <SiteConfigProvider>
          <CartProvider>
            <FavoritesProvider>
              <ScrollToTop />
              <Toaster theme="dark" position="top-right" richColors />
              <MaintenanceGate>
              <Routes>
                <Route path="/" element={<Shell><Home /></Shell>} />
                <Route path="/produtos" element={<Shell><Catalog /></Shell>} />
                <Route path="/grupo/:group" element={<Shell><Catalog /></Shell>} />
                <Route path="/produto/:slug" element={<Shell><ProductDetail /></Shell>} />
                <Route path="/marcas" element={<Shell><Brands /></Shell>} />
                <Route path="/contato" element={<Shell><Contact /></Shell>} />
                <Route path="/carrinho" element={<Shell><Cart /></Shell>} />
                <Route path="/checkout" element={<Shell><Checkout /></Shell>} />
                <Route path="/favoritos" element={<Shell><Favorites /></Shell>} />
                <Route path="/em-construcao" element={<UnderConstruction />} />
                <Route path="/login" element={<Shell><Login /></Shell>} />
                <Route path="/cadastro" element={<Shell><Register /></Shell>} />
                <Route path="/recuperar-senha" element={<Shell><ForgotPassword /></Shell>} />
                <Route path="/reset-password" element={<Shell><ResetPassword /></Shell>} />
                <Route
                  path="/conta"
                  element={<ProtectedRoute><Shell><Account /></Shell></ProtectedRoute>}
                />
                <Route
                  path="/admin"
                  element={<ProtectedRoute adminOnly><AdminLayout /></ProtectedRoute>}
                >
                  <Route index element={<Dashboard />} />
                  <Route path="produtos" element={<AdminProducts />} />
                  <Route path="categorias" element={<AdminCategories />} />
                  <Route path="marcas" element={<AdminBrands />} />
                  <Route path="pedidos" element={<AdminOrders />} />
                  <Route path="clientes" element={<AdminCustomers />} />
                  <Route path="banners" element={<AdminBanners />} />
                  <Route path="site" element={<AdminSite />} />
                  <Route path="identidade" element={<AdminBranding />} />
                  <Route path="melhor-envio" element={<AdminMelhorEnvio />} />
                </Route>
              </Routes>
              </MaintenanceGate>
            </FavoritesProvider>
          </CartProvider>
          </SiteConfigProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
