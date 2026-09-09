let currentCategory = "All";
let userLocation = null;
let allProducts = [];
let mapInstance = null;
let mapMarkers = [];

document.addEventListener("DOMContentLoaded", () => {
  // Check URL params for category
  const urlParams = new URLSearchParams(window.location.search);
  const catParam = urlParams.get("category");
  if (catParam) {
    currentCategory = catParam;
    document.querySelectorAll(".pill-btn").forEach(btn => {
      if (btn.getAttribute("data-category") === catParam) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  loadProducts();

  // Search input
  let searchTimeout = null;
  document.getElementById("search-input").addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadProducts, 350);
  });

  // Category pills
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      currentCategory = e.target.getAttribute("data-category");
      loadProducts();
    });
  });

  // Sort and organic toggle
  document.getElementById("sort-select").addEventListener("change", loadProducts);
  document.getElementById("organic-toggle").addEventListener("change", loadProducts);

  // Near me button
  document.getElementById("btn-near-me").addEventListener("click", handleNearMe);
  document.getElementById("clear-location-btn").addEventListener("click", clearLocation);

  // Map Modal
  document.getElementById("btn-open-map").addEventListener("click", openMapModal);
  document.getElementById("close-map-modal").addEventListener("click", closeMapModal);
  document.getElementById("close-map-btn").addEventListener("click", closeMapModal);
});

async function loadProducts() {
  const grid = document.getElementById("marketplace-grid");
  const search = document.getElementById("search-input").value.trim();
  const sortBy = document.getElementById("sort-select").value;
  const isOrganic = document.getElementById("organic-toggle").checked;

  let query = `/api/products?sort_by=${sortBy}`;
  if (search) query += `&search=${encodeURIComponent(search)}`;
  if (currentCategory && currentCategory !== "All") query += `&category=${encodeURIComponent(currentCategory)}`;
  if (isOrganic) query += `&is_organic=true`;

  if (userLocation) {
    query += `&user_lat=${userLocation.lat}&user_lng=${userLocation.lng}`;
  }

  try {
    const products = await apiRequest(query);
    allProducts = products;
    renderProducts(products);
  } catch (err) {
    grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: red; padding: 40px;">Failed to load products: ${err.message}</div>`;
  }
}

function renderProducts(products) {
  const grid = document.getElementById("marketplace-grid");
  if (!products || products.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: white; border-radius: 12px; border: 1px solid var(--border-color);">
        <div style="font-size: 3rem; margin-bottom: 12px;">🌾</div>
        <h3 style="margin-bottom: 8px;">No produce matches your filters</h3>
        <p style="color: var(--text-muted); margin-bottom: 20px;">Try adjusting your search query, category, or distance settings.</p>
        <button class="btn btn-outline btn-sm" onclick="resetFilters()">Reset All Filters</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = products.map(prod => `
    <div class="product-card">
      <div class="product-img-wrap">
        <img src="${prod.image_url || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80'}" alt="${prod.title}">
        ${prod.is_organic ? '<div class="organic-badge">🌱 Organic Certified</div>' : ''}
        ${prod.distance_km !== null && prod.distance_km !== undefined ? `<div class="distance-badge">📍 ${prod.distance_km} km away</div>` : ''}
      </div>
      <div class="product-body">
        <div class="product-cat">${prod.category}</div>
        <h3 class="product-title">${prod.title}</h3>
        <div class="product-farm">
          🚜 ${prod.farmer ? (prod.farmer.farm_name || prod.farmer.full_name) : 'Farmer'}
          • ${prod.farm_location_name || (prod.farmer ? prod.farmer.farm_city : 'India')}
        </div>
        <div class="rating-row">
          <span class="rating-stars">★ ${prod.average_rating > 0 ? prod.average_rating : 'New'}</span>
          <span>(${prod.total_reviews} reviews)</span>
          <span style="margin-left: auto; color: ${prod.stock_quantity > 10 ? 'var(--primary)' : 'var(--danger)'}; font-size: 0.8rem; font-weight: 600;">
            ${prod.stock_quantity > 0 ? `${prod.stock_quantity} ${prod.unit} in stock` : 'Out of stock'}
          </span>
        </div>
        <div class="product-footer">
          <div class="product-price">₹${prod.price_per_unit} <span>/ ${prod.unit}</span></div>
          <div style="display: flex; gap: 8px;">
            <a href="product-detail.html?id=${prod.id}" class="btn btn-outline btn-sm">Details</a>
            <button class="btn btn-primary btn-sm" onclick='handleAddToCart(${JSON.stringify(prod).replace(/'/g, "&apos;")})'>
              + Add
            </button>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

function handleAddToCart(product) {
  addToCart(product, 1);
}

function handleNearMe() {
  const banner = document.getElementById("location-banner");
  const bannerText = document.getElementById("location-text");

  if (!navigator.geolocation) {
    showToast("Geolocation is not supported by your browser. Using Mumbai reference.", "info");
    setLocation({ lat: 19.0760, lng: 72.8777, label: "Mumbai (Default)" });
    return;
  }

  showToast("Requesting device location...", "info");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      setLocation({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        label: `Current GPS (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)})`
      });
    },
    (err) => {
      console.warn("Geolocation denied or timed out:", err);
      // Fallback to Mumbai
      setLocation({ lat: 19.0760, lng: 72.8777, label: "Mumbai Region" });
      showToast("Location access denied or unavailable. Set reference to Mumbai region.", "info");
    },
    { timeout: 8000 }
  );
}

function setLocation(loc) {
  userLocation = loc;
  const banner = document.getElementById("location-banner");
  const bannerText = document.getElementById("location-text");
  banner.style.display = "flex";
  bannerText.textContent = `📍 Geolocation active: ${loc.label} — Products sorted by proximity to your area!`;
  document.getElementById("sort-select").value = "distance";
  loadProducts();
}

function clearLocation() {
  userLocation = null;
  document.getElementById("location-banner").style.display = "none";
  document.getElementById("sort-select").value = "newest";
  loadProducts();
}

function resetFilters() {
  document.getElementById("search-input").value = "";
  document.getElementById("organic-toggle").checked = false;
  document.getElementById("sort-select").value = "newest";
  currentCategory = "All";
  document.querySelectorAll(".pill-btn").forEach((b, i) => {
    if (i === 0) b.classList.add("active");
    else b.classList.remove("active");
  });
  clearLocation();
}

// Leaflet Map Logic
function openMapModal() {
  const modal = document.getElementById("map-modal");
  modal.classList.add("active");

  setTimeout(() => {
    if (!mapInstance) {
      // Initialize Leaflet map centered in central India
      mapInstance = L.map('map').setView([20.5937, 78.9629], 5);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapInstance);
    } else {
      mapInstance.invalidateSize();
    }

    // Clear old markers
    mapMarkers.forEach(m => mapInstance.removeLayer(m));
    mapMarkers = [];

    // Add markers for all products with coordinates
    allProducts.forEach(prod => {
      if (prod.farm_lat && prod.farm_lng) {
        const marker = L.marker([prod.farm_lat, prod.farm_lng]).addTo(mapInstance);
        const popupContent = `
          <div style="font-family: Inter, sans-serif; font-size: 13px;">
            <strong style="color: #1b5e20; font-size: 14px;">${prod.title}</strong><br>
            <span>🚜 ${prod.farm_location_name || 'Farm'}</span><br>
            <span style="font-weight: 700; color: #2e7d32;">₹${prod.price_per_unit} / ${prod.unit}</span><br>
            <div style="margin-top: 6px;">
              <a href="product-detail.html?id=${prod.id}" style="color: #f57c00; font-weight: 600; text-decoration: none;">View Produce →</a>
            </div>
          </div>
        `;
        marker.bindPopup(popupContent);
        mapMarkers.push(marker);
      }
    });

    if (mapMarkers.length > 0) {
      const group = new L.featureGroup(mapMarkers);
      mapInstance.fitBounds(group.getBounds().pad(0.2));
    }
  }, 200);
}

function closeMapModal() {
  document.getElementById("map-modal").classList.remove("active");
}
