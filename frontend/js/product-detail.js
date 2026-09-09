let currentProduct = null;
let miniMap = null;

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const productId = urlParams.get("id");

  if (!productId) {
    document.getElementById("product-loading").innerHTML = "Error: No product ID specified in URL.";
    return;
  }

  loadProductDetail(productId);

  // Qty controls
  const qtyInput = document.getElementById("order-qty");
  document.getElementById("qty-minus").addEventListener("click", () => {
    let val = parseInt(qtyInput.value) || 1;
    if (val > 1) qtyInput.value = val - 1;
  });

  document.getElementById("qty-plus").addEventListener("click", () => {
    let val = parseInt(qtyInput.value) || 1;
    if (currentProduct && val < currentProduct.stock_quantity) {
      qtyInput.value = val + 1;
    } else {
      showToast("Cannot exceed maximum available stock.", "warning");
    }
  });

  document.getElementById("btn-add-cart").addEventListener("click", () => {
    if (!currentProduct) return;
    const qty = parseFloat(qtyInput.value) || 1;
    addToCart(currentProduct, qty);
  });

  document.getElementById("btn-buy-now").addEventListener("click", () => {
    if (!currentProduct) return;
    const qty = parseFloat(qtyInput.value) || 1;
    addToCart(currentProduct, qty);
    window.location.href = "checkout.html";
  });
});

async function loadProductDetail(id) {
  const loading = document.getElementById("product-loading");
  const content = document.getElementById("product-content");

  try {
    const prod = await apiRequest(`/api/products/${id}`);
    currentProduct = prod;

    // Fill details
    document.title = `${prod.title} - Kisan2Consumer`;
    document.getElementById("p-image").src = prod.image_url || "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80";
    document.getElementById("p-image").alt = prod.title;
    document.getElementById("p-category").textContent = prod.category;
    document.getElementById("p-title").textContent = prod.title;
    document.getElementById("p-description").textContent = prod.description || "Farm-fresh produce with direct traceability.";
    document.getElementById("p-price").textContent = `₹${prod.price_per_unit}`;
    document.getElementById("p-unit").textContent = prod.unit;
    document.getElementById("p-harvest").textContent = prod.harvest_date || "Fresh Harvest";
    document.getElementById("p-stock").textContent = `${prod.stock_quantity} ${prod.unit} available`;

    if (prod.is_organic) {
      document.getElementById("p-organic-badge").style.display = "block";
    }

    // Farmer details
    const farmerName = prod.farmer ? (prod.farmer.farm_name || prod.farmer.full_name) : "Registered Kisan";
    document.getElementById("p-farmer-name").textContent = farmerName;
    document.getElementById("p-farm-address").textContent = `Cultivated at: ${prod.farm_location_name || (prod.farmer ? `${prod.farmer.farm_city}, ${prod.farmer.farm_state}` : 'Local Farm, India')}`;

    // Rating stats
    document.getElementById("p-stars").textContent = `★ ${prod.average_rating > 0 ? prod.average_rating : 'New'}`;
    document.getElementById("p-review-count").textContent = `(${prod.total_reviews} reviews)`;

    // Mini Map initialization
    initMiniMap(prod.farm_lat, prod.farm_lng, prod.farm_location_name || farmerName);

    // Show content
    loading.style.display = "none";
    content.style.display = "block";

    // Load reviews
    loadReviews(id);
  } catch (err) {
    loading.innerHTML = `<div style="color: red;">Failed to load product: ${err.message}</div>`;
  }
}

function initMiniMap(lat, lng, farmLabel) {
  const mapElement = document.getElementById("farm-view-map");
  if (!lat || !lng) {
    // Default central India coordinates if not geotagged
    lat = 20.5937;
    lng = 78.9629;
  }

  if (miniMap) {
    miniMap.remove();
  }

  miniMap = L.map(mapElement).setView([lat, lng], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(miniMap);

  const marker = L.marker([lat, lng]).addTo(miniMap);
  marker.bindPopup(`<strong>🌾 ${farmLabel}</strong><br>GPS Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}`).openPopup();
}

async function loadReviews(productId) {
  const list = document.getElementById("reviews-list");
  try {
    const reviews = await apiRequest(`/api/ratings/product/${productId}`);
    if (!reviews || reviews.length === 0) {
      list.innerHTML = `
        <div style="background: white; border: 1px dashed var(--border-color); border-radius: 10px; padding: 25px; text-align: center; color: var(--text-muted);">
          No consumer reviews yet. Be the first to order and review this crop!
        </div>
      `;
      return;
    }

    list.innerHTML = reviews.map(r => `
      <div class="review-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div>
            <strong>👤 ${r.consumer_name || 'Consumer'}</strong>
            <span style="color: #ffb300; font-weight: 700; margin-left: 8px;">★ ${r.rating_score} / 5.0</span>
          </div>
          <span style="font-size: 0.8rem; color: var(--text-muted);">
            ${r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'}
          </span>
        </div>
        <p style="color: #475569; font-size: 0.95rem; margin: 0;">${r.review_text || 'Excellent farm-fresh quality.'}</p>
      </div>
    `).join("");
  } catch (err) {
    list.innerHTML = `<div style="color: red;">Could not fetch reviews: ${err.message}</div>`;
  }
}
