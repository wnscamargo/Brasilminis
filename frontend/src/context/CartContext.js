import { createContext, useContext, useEffect, useState } from "react";
import { toast } from "sonner";

const CartContext = createContext(null);
const KEY = "bm_cart";

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY)) || [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(items));
  }, [items]);

  const addItem = (product, quantity = 1) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === product.id);
      if (existing) {
        return prev.map((i) =>
          i.product_id === product.id ? { ...i, quantity: i.quantity + quantity } : i
        );
      }
      return [
        ...prev,
        {
          product_id: product.id,
          name: product.name,
          slug: product.slug,
          price: product.price,
          image: (product.images || [])[0] || "",
          stock: product.stock,
          quantity,
        },
      ];
    });
    toast.success(`${product.name} adicionado ao carrinho`);
  };

  const updateQty = (product_id, quantity) => {
    if (quantity < 1) return;
    setItems((prev) => prev.map((i) => (i.product_id === product_id ? { ...i, quantity } : i)));
  };

  const removeItem = (product_id) => {
    setItems((prev) => prev.filter((i) => i.product_id !== product_id));
  };

  const clearCart = () => setItems([]);

  const subtotal = items.reduce((sum, i) => sum + i.price * i.quantity, 0);
  const count = items.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <CartContext.Provider
      value={{ items, addItem, updateQty, removeItem, clearCart, subtotal, count }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
