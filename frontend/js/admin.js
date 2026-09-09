/**
 * Kisan2Consumer Admin Portal & Conflict Resolution Desk
 */

let allDisputes = [];

document.addEventListener("DOMContentLoaded", () => {
  if (!isLoggedIn()) {
    showToast("Please sign in with Admin credentials to access the Ombudsman Portal.", "warning");
    setTimeout(() => window.location.href = "auth.html?role=admin", 1200);
    return;
  }

  const user = getUser();
  if (user.role !== "admin") {
    showToast("Access Denied: This area requires Administrator credentials.", "error");
    setTimeout(() => {
      window.location.href = user.role === "farmer" ? "farmer-dashboard.html" : "consumer-dashboard.html";
    }, 1500);
    return;
  }

  setupTabs();
  loadAdminStats();
  loadDisputes();
  setupArbitrationModal();

  // Status Filter Change
  document.getElementById("filter-dispute-status").addEventListener("change", (e) => {
    loadDisputes(e.target.value);
  });

  // User Role Filter Change
  document.getElementById("filter-user-role").addEventListener("change", (e) => {
    loadUsers(e.target.value);
  });
});

function setupTabs() {
  const tabDisputes = document.getElementById("tab-disputes-btn");
  const tabUsers = document.getElementById("tab-users-btn");
  const secDisputes = document.getElementById("section-disputes");
  const secUsers = document.getElementById("section-users");

  tabDisputes.addEventListener("click", () => {
    tabDisputes.classList.add("active");
    tabUsers.classList.remove("active");
    secDisputes.style.display = "block";
    secUsers.style.display = "none";
  });

  tabUsers.addEventListener("click", () => {
    tabUsers.classList.add("active");
    tabDisputes.classList.remove("active");
    secUsers.style.display = "block";
    secDisputes.style.display = "none";
    loadUsers();
  });
}

async function loadAdminStats() {
  try {
    const stats = await apiRequest("/api/admin/stats");
    document.getElementById("stat-farmers").textContent = stats.total_farmers || 0;
    document.getElementById("stat-consumers").textContent = stats.total_consumers || 0;
    document.getElementById("stat-gmv").textContent = `₹${(stats.gross_merchandise_value || 0).toLocaleString('en-IN')}`;
    document.getElementById("stat-open-disputes").textContent = stats.open_complaints || 0;
  } catch (err) {
    console.error("Failed to load admin stats:", err);
  }
}

async function loadDisputes(statusFilter = "OPEN") {
  const container = document.getElementById("disputes-list-container");
  container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-muted);">Fetching conflict registry...</div>`;

  try {
    const filter = statusFilter || document.getElementById("filter-dispute-status").value;
    const disputes = await apiRequest(`/api/admin/complaints?status_filter=${filter}`);
    allDisputes = disputes;
    renderDisputes(disputes);
  } catch (err) {
    container.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--danger);">Error loading disputes: ${err.message}</div>`;
  }
}

function renderDisputes(disputes) {
  const container = document.getElementById("disputes-list-container");

  if (!disputes || disputes.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 50px 20px; background: white; border-radius: 12px; border: 1px dashed #cbd5e1;">
        <div style="font-size: 3rem; margin-bottom: 10px;">✅</div>
        <h3>No Disputes in this Category</h3>
        <p style="color: var(--text-muted);">Trade operations are flowing smoothly with no active unresolved grievances.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = disputes.map(d => {
    const isPending = d.status === "OPEN" || d.status === "UNDER_INVESTIGATION";

    let badgeClass = "badge-pending";
    if (d.status === "RESOLVED_REFUND") badgeClass = "badge-delivered";
    if (d.status === "RESOLVED_REPLACED") badgeClass = "badge-shipped";
    if (d.status === "REJECTED") badgeClass = "badge-cancelled";

    return `
      <div class="dispute-card">
        <div class="dispute-header">
          <div>
            <span style="font-size: 1.1rem; font-weight: 800; color: #1e3a8a;">Grievance Case #${d.id}</span>
            <span style="color: var(--text-muted); font-size: 0.85rem; margin-left: 12px;">
              Order #${d.order_id} • Value: ₹${d.order_grand_total} • ${d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Recent'}
            </span>
          </div>
          <div>
            <span class="badge ${badgeClass}">${d.status}</span>
          </div>
        </div>

        <div class="dispute-parties">
          <div>
            <div class="party-title">👤 Consumer (Complainant)</div>
            <strong>${d.consumer_name}</strong><br>
            <span style="color: var(--text-muted);">Email:</span> ${d.consumer_email}<br>
            <span style="color: var(--text-muted);">Phone:</span> ${d.consumer_phone || 'N/A'}
          </div>
          <div>
            <div class="party-title">🚜 Farmer (Seller)</div>
            <strong>${d.farmer_farm_name} (${d.farmer_name})</strong><br>
            <span style="color: var(--text-muted);">Email:</span> ${d.farmer_email}<br>
            <span style="color: var(--text-muted);">Phone:</span> ${d.farmer_phone || 'N/A'}
          </div>
        </div>

        <div style="margin-bottom: 14px;">
          <div style="font-weight: 700; color: #b91c1c; margin-bottom: 4px;">
            ⚠️ Reported Issue: ${d.issue_type}
          </div>
          <p style="margin: 0 0 8px; color: #334155; font-size: 0.92rem; line-height: 1.5;">
            "${d.description}"
          </p>
          <div style="font-size: 0.85rem; color: #64748b;">
            Consumer Requested: <strong>${d.requested_resolution}</strong>
          </div>
          ${d.proof_image_url ? `
            <div style="margin-top: 8px;">
              <span style="font-size: 0.82rem; color: #64748b;">Inspection Photo Evidence:</span><br>
              <a href="${d.proof_image_url}" target="_blank">
                <img src="${d.proof_image_url}" class="proof-thumb" alt="Damage evidence">
              </a>
            </div>
          ` : ''}
        </div>

        ${d.admin_verdict ? `
          <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px; border-radius: 6px; margin-bottom: 14px; font-size: 0.88rem;">
            <strong style="color: #166534;">⚖️ Official Arbitration Ruling:</strong>
            <div style="color: #15803d; margin-top: 2px;">${d.admin_verdict}</div>
            <div style="color: #65a30d; font-size: 0.8rem; margin-top: 4px;">
              Ruling by: ${d.arbitrated_by || 'Admin Desk'} • ${d.resolved_at ? new Date(d.resolved_at).toLocaleString() : ''}
            </div>
          </div>
        ` : ''}

        <div style="display: flex; justify-content: flex-end; gap: 10px; padding-top: 10px; border-top: 1px solid #f1f5f9;">
          ${isPending ? `
            <button onclick="openArbitrateModal(${d.id})" class="btn btn-primary btn-sm" style="background: #1e3a8a; border-color: #1e3a8a;">
              Arbitrate & Issue Verdict ⚖️
            </button>
          ` : `
            <button onclick="openArbitrateModal(${d.id})" class="btn btn-outline btn-sm">
              Re-arbitrate / Modify Ruling
            </button>
          `}
        </div>
      </div>
    `;
  }).join("");
}

// Arbitration Modal Management
function setupArbitrationModal() {
  const modal = document.getElementById("arbitrate-modal");
  document.getElementById("close-arbitrate-modal").addEventListener("click", () => modal.classList.remove("active"));
  document.getElementById("cancel-arbitrate-btn").addEventListener("click", () => modal.classList.remove("active"));

  document.getElementById("arbitrate-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("arb-complaint-id").value;
    const status = document.getElementById("arb-status").value;
    const admin_verdict = document.getElementById("arb-verdict").value.trim();
    const resolution_notes = document.getElementById("arb-notes").value.trim() || null;

    try {
      await apiRequest(`/api/admin/complaints/${id}/arbitrate`, {
        method: "PUT",
        body: JSON.stringify({ status, admin_verdict, resolution_notes })
      });

      showToast(`Ruling recorded and emailed to both parties!`, "success");
      modal.classList.remove("active");
      loadAdminStats();
      loadDisputes();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function openArbitrateModal(complaintId) {
  const dispute = allDisputes.find(d => d.id === complaintId);
  if (!dispute) return;

  document.getElementById("arb-complaint-id").value = dispute.id;
  document.getElementById("arb-case-title").textContent = `Case #${dispute.id} (Order #${dispute.order_id}) • ${dispute.consumer_name} vs. ${dispute.farmer_farm_name}`;
  document.getElementById("arb-case-desc").textContent = `Issue: "${dispute.description}"`;

  const preview = document.getElementById("arb-proof-preview");
  if (dispute.proof_image_url) {
    preview.innerHTML = `<img src="${dispute.proof_image_url}" style="max-height: 120px; border-radius: 6px; border: 1px solid #ccc; margin-top: 4px;">`;
  } else {
    preview.innerHTML = "";
  }

  document.getElementById("arb-verdict").value = dispute.admin_verdict || "";
  document.getElementById("arb-notes").value = dispute.resolution_notes || "";
  if (dispute.status !== "OPEN") {
    document.getElementById("arb-status").value = dispute.status;
  }

  document.getElementById("arbitrate-modal").classList.add("active");
}

// User Directory
async function loadUsers(roleFilter = "ALL") {
  const tbody = document.getElementById("users-table-body");
  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 25px;">Fetching user directory...</td></tr>`;

  try {
    const role = roleFilter || document.getElementById("filter-user-role").value;
    const users = await apiRequest(`/api/admin/users?role_filter=${role}`);

    if (!users || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 25px; color: var(--text-muted);">No users found.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td><strong>#${u.id}</strong></td>
        <td><strong>${u.full_name}</strong></td>
        <td>${u.email}</td>
        <td>${u.phone || '—'}</td>
        <td>
          <span class="badge ${u.role === 'admin' ? 'badge-confirmed' : (u.role === 'farmer' ? 'badge-delivered' : 'badge-shipped')}">
            ${u.role.toUpperCase()}
          </span>
        </td>
        <td>${u.location || '—'}</td>
        <td>
          <span style="color: ${u.is_verified ? 'var(--primary)' : 'var(--danger)'}; font-weight: 700;">
            ${u.is_verified ? '✓ Verified' : '⏳ Pending'}
          </span>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 25px; color: var(--danger);">Error: ${err.message}</td></tr>`;
  }
}
