/**
 * Kisan2Consumer Centralized API Client & Frontend State Manager
 * SIH 2026 - Problem Statement SIH26033
 */

// Dynamic API Base URL: adaptive for local dev and live cloud deployment (Render)
const API_BASE = (window.location.port === "5500" || window.location.protocol === "file:")
  ? "http://127.0.0.1:8000"
  : window.location.origin;

// HTTP Request Utility
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = localStorage.getItem("k2c_token");

  const headers = {
    ...(options.isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {})
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const fetchOptions = { ...options, headers };
    delete fetchOptions.isFormData;

    const response = await fetch(url, fetchOptions);

    // Handle unauthorized
    if (response.status === 401) {
      if (token && !endpoint.includes("/auth/login")) {
        showToast("Session expired. Please log in again.", "warning");
        localStorage.removeItem("k2c_token");
        localStorage.removeItem("k2c_user");
        setTimeout(() => {
          window.location.href = "auth.html";
        }, 1500);
      }
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    console.error(`[API Error] ${endpoint}:`, err);
    throw err;
  }
}

// Authentication Helpers
function setAuth(token, user) {
  localStorage.setItem("k2c_token", token);
  localStorage.setItem("k2c_user", JSON.stringify(user));
}

function getUser() {
  const user = localStorage.getItem("k2c_user");
  return user ? JSON.parse(user) : null;
}

function getToken() {
  return localStorage.getItem("k2c_token");
}

function isLoggedIn() {
  return !!getToken();
}

function isFarmer() {
  const user = getUser();
  return user && user.role === "farmer";
}

function isConsumer() {
  const user = getUser();
  return user && user.role === "consumer";
}

function isAdmin() {
  const user = getUser();
  return user && user.role === "admin";
}

function logout() {
  localStorage.removeItem("k2c_token");
  localStorage.removeItem("k2c_user");
  showToast("Logged out successfully.", "success");
  setTimeout(() => {
    window.location.href = "index.html";
  }, 500);
}

// Shopping Cart Helpers (stored in localStorage)
function getCart() {
  const cart = localStorage.getItem("k2c_cart");
  return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
  localStorage.setItem("k2c_cart", JSON.stringify(cart));
  updateCartBadge();
}

function addToCart(product, quantity = 1) {
  let cart = getCart();
  const existingIndex = cart.findIndex(item => item.id === product.id);

  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
    if (cart[existingIndex].quantity > product.stock_quantity) {
      cart[existingIndex].quantity = product.stock_quantity;
      showToast(`Adjusted to maximum available stock (${product.stock_quantity} ${product.unit}).`, "warning");
    } else {
      showToast(`Updated ${product.title} in cart!`, "success");
    }
  } else {
    cart.push({
      id: product.id,
      title: product.title,
      price_per_unit: product.price_per_unit,
      unit: product.unit,
      image_url: product.image_url,
      farmer_id: product.farmer_id,
      farm_name: product.farm_location_name || (product.farmer ? product.farmer.farm_name : "Farm"),
      stock_quantity: product.stock_quantity,
      quantity: Math.min(quantity, product.stock_quantity)
    });
    showToast(`Added ${product.title} to cart!`, "success");
  }

  saveCart(cart);
}

function updateCartQuantity(productId, quantity) {
  let cart = getCart();
  if (quantity <= 0) {
    cart = cart.filter(item => item.id !== productId);
  } else {
    const item = cart.find(item => item.id === productId);
    if (item) {
      item.quantity = Math.min(quantity, item.stock_quantity);
    }
  }
  saveCart(cart);
}

function removeFromCart(productId) {
  let cart = getCart().filter(item => item.id !== productId);
  saveCart(cart);
  showToast("Item removed from cart.", "info");
}

function clearCart() {
  localStorage.removeItem("k2c_cart");
  updateCartBadge();
}

function getCartCount() {
  const cart = getCart();
  return cart.reduce((total, item) => total + item.quantity, 0);
}

function updateCartBadge() {
  const badges = document.querySelectorAll(".cart-badge");
  const count = getCartCount();
  badges.forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? "inline-block" : "none";
  });
}

// Toast Notifications
function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icon = type === "error" ? "❌" : (type === "warning" ? "⚠️" : (type === "info" ? "ℹ️" : "✅"));
  toast.innerHTML = `<span>${icon}</span> <div>${message}</div>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Navbar UI Initialization
function initNavbar() {
  const user = getUser();
  const navActions = document.querySelector(".nav-actions");
  const navLinks = document.querySelector(".nav-links");

  if (!navActions) return;

  updateCartBadge();

  if (user && isLoggedIn()) {
    // Add Dashboard link
    if (navLinks) {
      const existingDash = document.getElementById("nav-dashboard-link");
      if (!existingDash) {
        const li = document.createElement("li");
        li.id = "nav-dashboard-link";
        let dashUrl = "consumer-dashboard.html";
        let dashTitle = "📦 My Orders";
        if (user.role === "farmer") {
          dashUrl = "farmer-dashboard.html";
          dashTitle = "🌾 Farmer Portal";
        } else if (user.role === "admin") {
          dashUrl = "admin-portal.html";
          dashTitle = "⚖️ Admin Portal";
        }
        li.innerHTML = `<a href="${dashUrl}" style="color: var(--primary); font-weight: 700;">${dashTitle}</a>`;
        navLinks.appendChild(li);
      }
    }

    // Determine badge prefix
    let roleBadge = "👤 Grahak";
    if (user.role === "farmer") roleBadge = "🚜 Kisan";
    if (user.role === "admin") roleBadge = "⚖️ Admin";

    // Update Action Buttons
    navActions.innerHTML = `
      <a href="cart.html" class="cart-icon-btn">
        🛒 Cart <span class="cart-badge" style="display:none;">0</span>
      </a>
      <div class="user-menu">
        <span class="user-badge">
          ${roleBadge}: <strong>${user.full_name || user.email}</strong>
        </span>
        <button class="btn btn-outline btn-sm" onclick="logout()">Logout</button>
      </div>
    `;
    updateCartBadge();
  } else {
    navActions.innerHTML = `
      <a href="cart.html" class="cart-icon-btn">
        🛒 Cart <span class="cart-badge" style="display:none;">0</span>
      </a>
      <a href="auth.html" class="btn btn-outline btn-sm">Login / Register</a>
    `;
    updateCartBadge();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initNavbar();
});
