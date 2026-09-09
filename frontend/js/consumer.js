document.addEventListener("DOMContentLoaded", () => {
  if (!isLoggedIn()) {
    showToast("Please log in to view your orders.", "warning");
    setTimeout(() => window.location.href = "auth.html?role=consumer", 1000);
    return;
  }

  const user = getUser();
  if (user.role !== "consumer") {
    showToast("Redirecting to Farmer Portal...", "info");
    setTimeout(() => window.location.href = "farmer-dashboard.html", 800);
    return;
  }

  // Set Profile details
  document.getElementById("consumer-name").textContent = user.full_name || "Consumer";
  document.getElementById("consumer-email").textContent = user.email || "";
  document.getElementById("consumer-city").textContent = user.delivery_city ? `📍 ${user.delivery_city}` : "India";

  // Tab setup
  setupTabs();

  // Load Data
  loadConsumerData();

  // Modals setup
  setupRatingModal();
  setupComplaintModal();
  setupTrackingModal();
});

function setupTabs() {
  const tabOrders = document.getElementById("tab-orders-btn");
  const tabComplaints = document.getElementById("tab-complaints-btn");
  const secOrders = document.getElementById("section-orders");
  const secComplaints = document.getElementById("section-complaints");

  tabOrders.addEventListener("click", () => {
    tabOrders.classList.add("active");
    tabComplaints.classList.remove("active");
    secOrders.style.display = "block";
    secComplaints.style.display = "none";
  });

  tabComplaints.addEventListener("click", () => {
    tabComplaints.classList.add("active");
    tabOrders.classList.remove("active");
    secComplaints.style.display = "block";
    secOrders.style.display = "none";
  });
}

let consumerOrdersList = [];

async function loadConsumerData() {
  try {
    // 1. Load orders
    const orders = await apiRequest("/api/orders/my-orders");
    consumerOrdersList = orders;
    renderConsumerOrders(orders);

    // 2. Load complaints
    const complaints = await apiRequest("/api/complaints/my-complaints");
    renderConsumerComplaints(complaints);
  } catch (err) {
    showToast("Error loading orders: " + err.message, "error");
  }
}

function renderConsumerOrders(orders) {
  const container = document.getElementById("orders-container");
  if (!orders || orders.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 50px 20px; background: #f8faf9; border-radius: 12px;">
        <div style="font-size: 3rem; margin-bottom: 10px;">📦</div>
        <h3>No orders placed yet</h3>
        <p style="color: var(--text-muted); margin: 8px 0 20px;">Explore direct produce from verified kisans.</p>
        <a href="marketplace.html" class="btn btn-primary btn-sm">Shop Farm Produce</a>
      </div>
    `;
    return;
  }

  container.innerHTML = orders.map(ord => {
    const itemsHtml = ord.items.map(it => `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f1f5f9; flex-wrap: wrap; gap: 10px;">
        <div>
          <strong style="color: var(--primary-dark); font-size: 1rem;">${it.product_title}</strong>
          <div style="font-size: 0.85rem; color: var(--text-muted);">
            Quantity: ${it.quantity} ${it.unit} @ ₹${it.unit_price} = ₹${it.subtotal.toFixed(2)}
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button onclick="openRatingModal(${it.product_id}, ${ord.id}, '${it.product_title.replace(/'/g, "\\'")}')" class="btn btn-outline btn-sm">
            ★ Rate Product
          </button>
          <button onclick="openComplaintModal(${ord.id}, ${it.product_id}, '${it.product_title.replace(/'/g, "\\'")}')" class="btn btn-outline btn-sm" style="color: var(--danger); border-color: #ffcdd2;">
            ⚠️ Report Damage
          </button>
        </div>
      </div>
    `).join("");

    return `
      <div style="background: white; border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; margin-bottom: 22px; box-shadow: var(--shadow-sm);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
          <div>
            <span style="font-weight: 800; font-size: 1.1rem; color: var(--primary-dark);">Order #${ord.id}</span>
            <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 10px;">
              ${ord.created_at ? new Date(ord.created_at).toLocaleDateString() : 'Recent'}
            </span>
          </div>
          <div>
            <span class="badge ${getStatusBadge(ord.status)}">${ord.status}</span>
            <span class="badge badge-delivered" style="margin-left: 6px;">PAID: ${ord.payment_transaction_id || 'COMPLETED'}</span>
          </div>
        </div>

        <div style="margin-bottom: 14px;">
          ${itemsHtml}
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 14px; border-top: 1px solid var(--border-color); font-size: 0.9rem; flex-wrap: wrap; gap: 12px;">
          <div style="color: var(--text-muted); max-width: 450px;">
            📍 Delivering to: <strong>${ord.shipping_address}, ${ord.shipping_city} (${ord.shipping_pincode})</strong>
          </div>
          <div style="display: flex; align-items: center; gap: 14px;">
            <div style="font-size: 1.15rem; font-weight: 800; color: var(--primary-dark);">
              Grand Total: ₹${ord.grand_total.toFixed(2)}
            </div>
            <button onclick="openOrderTracker(${ord.id})" class="btn btn-primary btn-sm" style="display: flex; align-items: center; gap: 6px;">
              🗺️ Track Farm Origin & Route
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function renderConsumerComplaints(complaints) {
  const tbody = document.getElementById("consumer-complaints-table");
  if (!complaints || complaints.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--text-muted);">No damage claims filed. All produce delivered successfully!</td></tr>`;
    return;
  }

  tbody.innerHTML = complaints.map(c => `
    <tr>
      <td><strong>#${c.id}</strong></td>
      <td>#${c.order_id}</td>
      <td><strong style="color: var(--danger);">${c.issue_type}</strong></td>
      <td style="max-width: 250px;">
        <div>${c.description}</div>
        ${c.proof_image_url ? `<a href="${c.proof_image_url}" target="_blank" style="font-size: 0.78rem; color: var(--primary);">View Photo ↗</a>` : ''}
      </td>
      <td><strong>${c.requested_resolution}</strong></td>
      <td>
        <span class="badge ${c.status === 'OPEN' ? 'badge-pending' : (c.status.includes('RESOLVED') ? 'badge-delivered' : 'badge-shipped')}">
          ${c.status}
        </span>
      </td>
      <td>
        <span style="font-size: 0.85rem; color: #475569;">
          ${c.resolution_notes || 'Pending farmer review'}
        </span>
      </td>
    </tr>
  `).join("");
}

function getStatusBadge(status) {
  switch (status) {
    case "CONFIRMED": return "badge-confirmed";
    case "SHIPPED": return "badge-shipped";
    case "DELIVERED": return "badge-delivered";
    case "CANCELLED": return "badge-cancelled";
    default: return "badge-pending";
  }
}

// Rating Modal Logic
function setupRatingModal() {
  const modal = document.getElementById("rating-modal");
  document.getElementById("close-rating-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("cancel-rating-btn").addEventListener("click", () => modal.classList.remove("active"));

  // Star selector
  const stars = document.querySelectorAll("#star-selector .star");
  stars.forEach(s => {
    s.addEventListener("click", () => {
      const val = parseInt(s.getAttribute("data-value"));
      document.getElementById("rate-score").value = val;
      stars.forEach(star => {
        const starVal = parseInt(star.getAttribute("data-value"));
        if (starVal <= val) {
          star.classList.add("active");
        } else {
          star.classList.remove("active");
        }
      });
    });
  });

  document.getElementById("rating-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const product_id = parseInt(document.getElementById("rate-product-id").value);
    const order_id = parseInt(document.getElementById("rate-order-id").value);
    const rating_score = parseFloat(document.getElementById("rate-score").value);
    const review_text = document.getElementById("rate-text").value.trim();

    try {
      await apiRequest("/api/ratings", {
        method: "POST",
        body: JSON.stringify({ product_id, order_id, rating_score, review_text })
      });
      showToast("Thank you! Your rating and review were published.", "success");
      modal.classList.remove("active");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function openRatingModal(productId, orderId, title) {
  document.getElementById("rate-product-id").value = productId;
  document.getElementById("rate-order-id").value = orderId;
  document.getElementById("rate-product-title").textContent = `Produce: ${title}`;
  document.getElementById("rate-text").value = "";
  document.getElementById("rating-modal").classList.add("active");
}

// Complaint Modal Logic
function setupComplaintModal() {
  const modal = document.getElementById("complaint-modal");
  document.getElementById("close-complaint-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("cancel-complaint-btn").addEventListener("click", () => modal.classList.remove("active"));

  document.getElementById("complaint-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const order_id = parseInt(document.getElementById("comp-order-id").value);
    const product_id = parseInt(document.getElementById("comp-product-id").value);
    const issue_type = document.getElementById("comp-issue-type").value;
    const description = document.getElementById("comp-desc").value.trim();
    const proof_image_url = document.getElementById("comp-proof-url").value.trim() || null;
    const requested_resolution = document.getElementById("comp-resolution").value;

    try {
      await apiRequest("/api/complaints", {
        method: "POST",
        body: JSON.stringify({
          order_id,
          product_id,
          issue_type,
          description,
          proof_image_url,
          requested_resolution
        })
      });
      showToast("Dispute submitted. The farmer will be notified to review.", "success");
      modal.classList.remove("active");
      loadConsumerData();
      // Switch to complaints tab
      document.getElementById("tab-complaints-btn").click();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function openComplaintModal(orderId, productId, title) {
  document.getElementById("comp-order-id").value = orderId;
  document.getElementById("comp-product-id").value = productId;
  document.getElementById("comp-product-info").textContent = `Order #${orderId} • Produce: ${title}`;
  document.getElementById("comp-desc").value = "";
  document.getElementById("comp-proof-url").value = "";
  document.getElementById("complaint-modal").classList.add("active");
}

// ================= Live Leaflet Tracking System =================
let trackingMapInstance = null;

const indianCityCoordinates = {
  "mumbai": [19.0760, 72.8777],
  "delhi": [28.6139, 77.2090],
  "new delhi": [28.6139, 77.2090],
  "noida": [28.5355, 77.3910],
  "gurgaon": [28.4595, 77.0266],
  "gurugram": [28.4595, 77.0266],
  "pune": [18.5204, 73.8567],
  "bengaluru": [12.9716, 77.5946],
  "bangalore": [12.9716, 77.5946],
  "hyderabad": [17.3850, 78.4867],
  "chennai": [13.0827, 80.2707],
  "kolkata": [22.5726, 88.3639],
  "ahmedabad": [23.0225, 72.5714],
  "nashik": [19.9975, 73.7898],
  "ludhiana": [30.9010, 75.8573],
  "guntur": [16.3067, 80.4365],
  "chandigarh": [30.7333, 76.7794],
  "jaipur": [26.9124, 75.7873],
  "lucknow": [26.8467, 80.9462]
};

function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371.0;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

function setupTrackingModal() {
  const modal = document.getElementById("tracking-modal");
  if (!modal) return;
  document.getElementById("close-tracking-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("close-tracking-btn").addEventListener("click", () => modal.classList.remove("active"));
}

function openOrderTracker(orderId) {
  const ord = consumerOrdersList.find(o => o.id === orderId);
  if (!ord) return;

  const modal = document.getElementById("tracking-modal");
  document.getElementById("tracking-title").textContent = `🗺️ Live Transit Tracker: Order #${ord.id}`;

  // 1. Identify Farm Origin
  let farmLat = 19.9975;
  let farmLng = 73.7898;
  let farmName = "Kisan Agro Farm";
  let farmLoc = "Nashik, Maharashtra";

  if (ord.items && ord.items.length > 0) {
    const firstItem = ord.items[0];
    if (firstItem.farm_lat && firstItem.farm_lng) {
      farmLat = firstItem.farm_lat;
      farmLng = firstItem.farm_lng;
    }
    if (firstItem.farm_name) farmName = firstItem.farm_name;
    if (firstItem.farm_location) farmLoc = firstItem.farm_location;
  }

  document.getElementById("track-farm-name").textContent = farmName;
  document.getElementById("track-farm-location").textContent = `📍 ${farmLoc}`;
  document.getElementById("track-farm-coords").textContent = `GPS: ${farmLat.toFixed(4)}° N, ${farmLng.toFixed(4)}° E`;

  // 2. Identify Destination Coordinates
  const cityKey = (ord.shipping_city || "").trim().toLowerCase();
  let destLat = 19.0760;
  let destLng = 72.8777;
  if (indianCityCoordinates[cityKey]) {
    [destLat, destLng] = indianCityCoordinates[cityKey];
  }

  const user = getUser();
  document.getElementById("track-consumer-name").textContent = user ? user.full_name : "Customer";
  document.getElementById("track-delivery-address").textContent = `${ord.shipping_address}, ${ord.shipping_city} (${ord.shipping_pincode})`;

  const distance = calculateDistanceKm(farmLat, farmLng, destLat, destLng);
  document.getElementById("track-distance-badge").textContent = `🚚 Transit Distance: ~${distance} km`;

  // 3. Highlight Milestones
  const steps = ["step-placed", "step-confirmed", "step-shipped", "step-delivered"];
  steps.forEach(s => {
    const el = document.getElementById(s);
    if (el) {
      el.style.opacity = "0.4";
      el.style.color = "#64748b";
    }
  });

  const activeSteps = {
    "PENDING_PAYMENT": ["step-placed"],
    "CONFIRMED": ["step-placed", "step-confirmed"],
    "SHIPPED": ["step-placed", "step-confirmed", "step-shipped"],
    "DELIVERED": ["step-placed", "step-confirmed", "step-shipped", "step-delivered"]
  };

  (activeSteps[ord.status] || ["step-placed"]).forEach(s => {
    const el = document.getElementById(s);
    if (el) {
      el.style.opacity = "1";
      el.style.color = "var(--primary-dark)";
    }
  });

  modal.classList.add("active");

  // 4. Initialize or reset Leaflet map
  setTimeout(() => {
    if (trackingMapInstance) {
      trackingMapInstance.remove();
      trackingMapInstance = null;
    }

    trackingMapInstance = L.map("tracking-map").setView([(farmLat + destLat) / 2, (farmLng + destLng) / 2], 6);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(trackingMapInstance);

    // Custom Farm Marker Icon
    const farmIcon = L.divIcon({
      html: '<div style="background: #2e7d32; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); border: 2px solid white;">🚜</div>',
      className: '',
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });

    // Custom Destination Marker Icon
    const destIcon = L.divIcon({
      html: '<div style="background: #1e3a8a; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); border: 2px solid white;">🏡</div>',
      className: '',
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });

    L.marker([farmLat, farmLng], { icon: farmIcon })
      .addTo(trackingMapInstance)
      .bindPopup(`<b>🌾 Farm Origin:</b><br>${farmName}<br>${farmLoc}`)
      .openPopup();

    L.marker([destLat, destLng], { icon: destIcon })
      .addTo(trackingMapInstance)
      .bindPopup(`<b>🏡 Consumer Delivery:</b><br>${ord.shipping_address}, ${ord.shipping_city}`);

    // Draw Route Polyline
    const routeCoords = [[farmLat, farmLng], [destLat, destLng]];
    const polyline = L.polyline(routeCoords, {
      color: '#16a34a',
      weight: 4,
      opacity: 0.8,
      dashArray: '8, 8'
    }).addTo(trackingMapInstance);

    // Position delivery vehicle according to status
    let truckProgress = 0.15; // default near farm
    if (ord.status === "SHIPPED") truckProgress = 0.65; // on highway
    if (ord.status === "DELIVERED") truckProgress = 0.98; // arrived

    const truckLat = farmLat + (destLat - farmLat) * truckProgress;
    const truckLng = farmLng + (destLng - farmLng) * truckProgress;

    const truckIcon = L.divIcon({
      html: '<div style="background: #eab308; color: black; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); border: 2px solid white;">🚚</div>',
      className: '',
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    L.marker([truckLat, truckLng], { icon: truckIcon })
      .addTo(trackingMapInstance)
      .bindPopup(`<b>🚚 Real-Time Transit:</b><br>Status: <strong>${ord.status}</strong><br>Direct Kisan2Consumer Logistics`);

    trackingMapInstance.fitBounds(polyline.getBounds(), { padding: [40, 40] });
    trackingMapInstance.invalidateSize();
  }, 200);
}
