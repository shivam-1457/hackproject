document.addEventListener("DOMContentLoaded", () => {
  if (!isLoggedIn()) {
    showToast("Please log in to access the Farmer Dashboard.", "warning");
    setTimeout(() => window.location.href = "auth.html?role=farmer", 1000);
    return;
  }

  const user = getUser();
  if (user.role !== "farmer") {
    showToast("Farmer portal is only accessible to verified farmers.", "error");
    setTimeout(() => window.location.href = "consumer-dashboard.html", 1200);
    return;
  }

  // Set Profile details
  document.getElementById("farmer-display-name").textContent = user.full_name || "Kisan";
  document.getElementById("farmer-farm-name").textContent = user.farm_name || "Agro Farm";
  document.getElementById("farmer-location-tag").textContent = `📍 ${user.farm_city || 'City'}, ${user.farm_state || 'India'}`;

  // Tab switching
  setupTabs();

  // Load Data
  loadFarmerData();

  // Modals setup
  setupCropModal();
  setupEditCropModal();
  setupResolveModal();
});

function setupTabs() {
  const tabCrops = document.getElementById("tab-crops-btn");
  const tabOrders = document.getElementById("tab-orders-btn");
  const tabComplaints = document.getElementById("tab-complaints-btn");

  const secCrops = document.getElementById("section-crops");
  const secOrders = document.getElementById("section-orders");
  const secComplaints = document.getElementById("section-complaints");

  tabCrops.addEventListener("click", () => {
    setActiveTab(tabCrops, secCrops);
  });
  tabOrders.addEventListener("click", () => {
    setActiveTab(tabOrders, secOrders);
  });
  tabComplaints.addEventListener("click", () => {
    setActiveTab(tabComplaints, secComplaints);
  });

  function setActiveTab(activeBtn, activeSec) {
    [tabCrops, tabOrders, tabComplaints].forEach(b => b.classList.remove("active"));
    [secCrops, secOrders, secComplaints].forEach(s => s.style.display = "none");
    activeBtn.classList.add("active");
    activeSec.style.display = "block";
  }
}

let farmerCropsList = [];

async function loadFarmerData() {
  try {
    // 1. Fetch crops
    const crops = await apiRequest("/api/products/farmer/my-products");
    farmerCropsList = crops;
    renderFarmerCrops(crops);
    document.getElementById("stat-crops").textContent = crops.length;

    // 2. Fetch orders
    const orders = await apiRequest("/api/orders/farmer-orders");
    renderFarmerOrders(orders);
    document.getElementById("stat-orders").textContent = orders.length;

    let totalRev = 0;
    orders.forEach(o => {
      if (o.order_status !== "CANCELLED") {
        totalRev += (o.farmer_revenue || 0);
      }
    });
    document.getElementById("stat-revenue").textContent = `₹${totalRev.toFixed(0)}`;

    // 3. Fetch complaints
    const complaints = await apiRequest("/api/complaints/farmer-complaints");
    renderFarmerComplaints(complaints);
    const openCount = complaints.filter(c => c.status === "OPEN" || c.status === "UNDER_INVESTIGATION").length;
    document.getElementById("stat-complaints").textContent = openCount;

  } catch (err) {
    showToast("Error loading dashboard data: " + err.message, "error");
  }
}

function renderFarmerCrops(crops) {
  const tbody = document.getElementById("farmer-products-table");
  if (!crops || crops.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--text-muted);">No crops listed yet. Click "+ Add New Crop" to list your harvest!</td></tr>`;
    return;
  }

  tbody.innerHTML = crops.map(p => `
    <tr>
      <td>
        <div style="display: flex; align-items: center; gap: 10px;">
          <img src="${p.image_url || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=80&q=80'}" style="width: 44px; height: 44px; border-radius: 6px; object-fit: cover;">
          <div>
            <strong>${p.title}</strong>
            ${p.is_organic ? '<br><span style="font-size: 0.75rem; color: var(--primary); font-weight: 700;">🌱 Organic</span>' : ''}
          </div>
        </div>
      </td>
      <td>${p.category}</td>
      <td><strong>₹${p.price_per_unit}</strong> / ${p.unit}</td>
      <td>${p.stock_quantity} ${p.unit}</td>
      <td>★ ${p.average_rating > 0 ? p.average_rating : 'New'} (${p.total_reviews})</td>
      <td>
        <span class="badge ${p.is_active ? 'badge-delivered' : 'badge-cancelled'}">
          ${p.is_active ? 'Active' : 'Unlisted'}
        </span>
      </td>
      <td>
        <div style="display: flex; gap: 6px;">
          <button onclick="openEditCropModal(${p.id})" class="btn btn-outline btn-sm">
            ✏️ Edit
          </button>
          <button onclick="deleteCrop(${p.id})" class="btn btn-outline btn-sm" style="color: var(--danger); border-color: #ffcdd2;">
            Delete
          </button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderFarmerOrders(orders) {
  const tbody = document.getElementById("farmer-orders-table");
  if (!orders || orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">No orders received yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = orders.map(ord => {
    const itemsText = ord.farmer_items.map(it => `• ${it.product_title}: ${it.quantity} ${it.unit}`).join("<br>");
    return `
      <tr>
        <td><strong>#${ord.order_id}</strong></td>
        <td>
          <strong>${ord.consumer_name}</strong><br>
          <span style="font-size: 0.8rem; color: var(--text-muted);">${ord.shipping_address}</span>
        </td>
        <td style="font-size: 0.88rem;">${itemsText}</td>
        <td><strong style="color: var(--primary-dark);">₹${ord.farmer_revenue}</strong></td>
        <td>
          <span class="badge ${getStatusBadgeClass(ord.order_status)}">${ord.order_status}</span>
        </td>
        <td>
          <select onchange="updateStatus(${ord.order_id}, this.value)" class="form-control" style="font-size: 0.82rem; padding: 4px 8px; width: 130px;">
            <option value="CONFIRMED" ${ord.order_status === 'CONFIRMED' ? 'selected' : ''}>Confirmed</option>
            <option value="SHIPPED" ${ord.order_status === 'SHIPPED' ? 'selected' : ''}>Shipped</option>
            <option value="DELIVERED" ${ord.order_status === 'DELIVERED' ? 'selected' : ''}>Delivered</option>
            <option value="CANCELLED" ${ord.order_status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
          </select>
        </td>
      </tr>
    `;
  }).join("");
}

function renderFarmerComplaints(complaints) {
  const tbody = document.getElementById("farmer-complaints-table");
  if (!complaints || complaints.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--text-muted);">No damaged goods complaints filed against your produce.</td></tr>`;
    return;
  }

  tbody.innerHTML = complaints.map(c => `
    <tr>
      <td>#${c.id}</td>
      <td><strong>#${c.order_id}</strong></td>
      <td><span style="color: var(--danger); font-weight: 600;">${c.issue_type}</span></td>
      <td style="max-width: 250px;">
        <div>${c.description}</div>
        ${c.proof_image_url ? `<a href="${c.proof_image_url}" target="_blank" style="font-size: 0.78rem; color: var(--primary);">View Photo Proof ↗</a>` : ''}
      </td>
      <td><strong>${c.requested_resolution}</strong></td>
      <td>
        <span class="badge ${c.status === 'OPEN' ? 'badge-pending' : (c.status.includes('RESOLVED') ? 'badge-delivered' : 'badge-shipped')}">
          ${c.status}
        </span>
      </td>
      <td>
        <button onclick="openResolveModal(${c.id})" class="btn btn-outline btn-sm">Resolve</button>
      </td>
    </tr>
  `).join("");
}

function getStatusBadgeClass(status) {
  switch (status) {
    case "CONFIRMED": return "badge-confirmed";
    case "SHIPPED": return "badge-shipped";
    case "DELIVERED": return "badge-delivered";
    case "CANCELLED": return "badge-cancelled";
    default: return "badge-pending";
  }
}

async function updateStatus(orderId, newStatus) {
  try {
    await apiRequest(`/api/orders/${orderId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: newStatus })
    });
    showToast(`Order #${orderId} status updated to ${newStatus}!`, "success");
    loadFarmerData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteCrop(cropId) {
  if (!confirm("Are you sure you want to remove this crop listing from the marketplace?")) return;
  try {
    await apiRequest(`/api/products/${cropId}`, { method: "DELETE" });
    showToast("Crop listing removed.", "info");
    loadFarmerData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Upload helper function for image files
async function uploadCropImageFile(fileInput, previewImg, previewContainer, urlInput, statusText) {
  if (!fileInput.files || !fileInput.files[0]) return;
  const file = fileInput.files[0];

  // Client preview
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewContainer.style.display = "flex";
  };
  reader.readAsDataURL(file);

  if (statusText) statusText.textContent = "Uploading image...";

  // Upload to API
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await apiRequest("/api/products/upload-image", {
      method: "POST",
      body: formData,
      isFormData: true
    });
    urlInput.value = res.image_url;
    if (statusText) statusText.textContent = "✓ Uploaded!";
    showToast("Photo uploaded successfully!", "success");
  } catch (err) {
    if (statusText) statusText.textContent = "Upload failed";
    showToast(`Image upload failed: ${err.message}`, "error");
  }
}

// Add Crop Modal
function setupCropModal() {
  const modal = document.getElementById("add-crop-modal");
  document.getElementById("btn-add-crop").addEventListener("click", () => modal.classList.add("active"));
  document.getElementById("close-crop-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("cancel-crop-btn").addEventListener("click", () => modal.classList.remove("active"));

  // File upload change listener
  const fileInput = document.getElementById("crop-image-file");
  const previewImg = document.getElementById("crop-image-preview");
  const previewContainer = document.getElementById("crop-image-preview-container");
  const urlInput = document.getElementById("crop-image");
  const statusText = document.getElementById("upload-status-text");

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      uploadCropImageFile(fileInput, previewImg, previewContainer, urlInput, statusText);
    });
  }

  document.getElementById("add-crop-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById("crop-title").value.trim(),
      category: document.getElementById("crop-category").value,
      unit: document.getElementById("crop-unit").value,
      price_per_unit: parseFloat(document.getElementById("crop-price").value),
      stock_quantity: parseFloat(document.getElementById("crop-stock").value),
      harvest_date: document.getElementById("crop-harvest").value || null,
      image_url: document.getElementById("crop-image").value.trim() || null,
      description: document.getElementById("crop-desc").value.trim() || null,
      is_organic: document.getElementById("crop-organic").checked
    };

    try {
      await apiRequest("/api/products", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      showToast("Crop listed successfully!", "success");
      modal.classList.remove("active");
      document.getElementById("add-crop-form").reset();
      if (previewContainer) previewContainer.style.display = "none";
      loadFarmerData();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

// Edit Crop Modal
function setupEditCropModal() {
  const modal = document.getElementById("edit-crop-modal");
  if (!modal) return;

  document.getElementById("close-edit-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("cancel-edit-btn").addEventListener("click", () => modal.classList.remove("active"));

  const fileInput = document.getElementById("edit-crop-image-file");
  const previewImg = document.getElementById("edit-image-preview");
  const previewContainer = document.getElementById("edit-image-preview-container");
  const urlInput = document.getElementById("edit-crop-image");

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      uploadCropImageFile(fileInput, previewImg, previewContainer, urlInput, null);
    });
  }

  document.getElementById("edit-crop-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const cropId = document.getElementById("edit-crop-id").value;
    const payload = {
      title: document.getElementById("edit-crop-title").value.trim(),
      category: document.getElementById("edit-crop-category").value,
      unit: document.getElementById("edit-crop-unit").value,
      price_per_unit: parseFloat(document.getElementById("edit-crop-price").value),
      stock_quantity: parseFloat(document.getElementById("edit-crop-stock").value),
      image_url: document.getElementById("edit-crop-image").value.trim() || null,
      description: document.getElementById("edit-crop-desc").value.trim() || null,
      is_organic: document.getElementById("edit-crop-organic").checked
    };

    try {
      await apiRequest(`/api/products/${cropId}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      showToast("Produce listing updated successfully!", "success");
      modal.classList.remove("active");
      loadFarmerData();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function openEditCropModal(cropId) {
  const crop = farmerCropsList.find(c => c.id === cropId);
  if (!crop) return;

  document.getElementById("edit-crop-id").value = crop.id;
  document.getElementById("edit-crop-title").value = crop.title || "";
  document.getElementById("edit-crop-category").value = crop.category || "Fresh Vegetables";
  document.getElementById("edit-crop-unit").value = crop.unit || "kg";
  document.getElementById("edit-crop-price").value = crop.price_per_unit || "";
  document.getElementById("edit-crop-stock").value = crop.stock_quantity || 0;
  document.getElementById("edit-crop-image").value = crop.image_url || "";
  document.getElementById("edit-crop-desc").value = crop.description || "";
  document.getElementById("edit-crop-organic").checked = !!crop.is_organic;

  const previewContainer = document.getElementById("edit-image-preview-container");
  const previewImg = document.getElementById("edit-image-preview");
  if (crop.image_url) {
    previewImg.src = crop.image_url;
    previewContainer.style.display = "block";
  } else {
    previewContainer.style.display = "none";
  }

  document.getElementById("edit-crop-modal").classList.add("active");
}

// Resolve Dispute Modal
function setupResolveModal() {
  const modal = document.getElementById("resolve-modal");
  document.getElementById("close-resolve-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("cancel-resolve-btn").addEventListener("click", () => modal.classList.remove("active"));

  document.getElementById("resolve-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("resolve-complaint-id").value;
    const status = document.getElementById("resolve-status").value;
    const resolution_notes = document.getElementById("resolve-notes").value.trim();

    try {
      await apiRequest(`/api/complaints/${id}/resolve`, {
        method: "PUT",
        body: JSON.stringify({ status, resolution_notes })
      });
      showToast("Dispute resolution submitted!", "success");
      modal.classList.remove("active");
      loadFarmerData();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function openResolveModal(complaintId) {
  document.getElementById("resolve-complaint-id").value = complaintId;
  document.getElementById("resolve-notes").value = "";
  document.getElementById("resolve-modal").classList.add("active");
}
