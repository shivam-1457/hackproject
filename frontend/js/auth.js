let selectedRole = "farmer";
let pickerMap = null;
let pickerMarker = null;

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const roleParam = urlParams.get("role");
  const tabParam = urlParams.get("tab");

  // Tab switching
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const panelLogin = document.getElementById("login-panel");
  const panelRegister = document.getElementById("register-panel");

  tabLogin.addEventListener("click", () => {
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    panelLogin.style.display = "block";
    panelRegister.style.display = "none";
  });

  tabRegister.addEventListener("click", () => {
    tabRegister.classList.add("active");
    tabLogin.classList.remove("active");
    panelRegister.style.display = "block";
    panelLogin.style.display = "none";
    initPickerMap();
  });

  if (tabParam === "register" || roleParam) {
    tabRegister.click();
  }

  // Role switching in register
  const btnRoleFarmer = document.getElementById("btn-role-farmer");
  const btnRoleConsumer = document.getElementById("btn-role-consumer");
  const farmerFields = document.getElementById("farmer-fields");
  const consumerFields = document.getElementById("consumer-fields");

  btnRoleFarmer.addEventListener("click", () => {
    selectedRole = "farmer";
    btnRoleFarmer.classList.add("active");
    btnRoleConsumer.classList.remove("active");
    farmerFields.style.display = "block";
    consumerFields.style.display = "none";
    initPickerMap();
  });

  btnRoleConsumer.addEventListener("click", () => {
    selectedRole = "consumer";
    btnRoleConsumer.classList.add("active");
    btnRoleFarmer.classList.remove("active");
    farmerFields.style.display = "none";
    consumerFields.style.display = "block";
  });

  if (roleParam === "consumer") {
    btnRoleConsumer.click();
  }

  // Handle Login
  document.getElementById("login-form").addEventListener("submit", handleLogin);

  // Handle Register
  document.getElementById("register-form").addEventListener("submit", handleRegister);
});

function initPickerMap() {
  const mapElem = document.getElementById("farm-picker-map");
  if (!mapElem || pickerMap) {
    if (pickerMap) pickerMap.invalidateSize();
    return;
  }

  setTimeout(() => {
    // Default to central India
    const defaultLat = 20.5937;
    const defaultLng = 78.9629;

    pickerMap = L.map('farm-picker-map').setView([defaultLat, defaultLng], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap'
    }).addTo(pickerMap);

    pickerMap.on("click", (e) => {
      const { lat, lng } = e.latlng;
      document.getElementById("reg-lat").value = lat.toFixed(5);
      document.getElementById("reg-lng").value = lng.toFixed(5);
      document.getElementById("coord-display").textContent = `Pinned: ${lat.toFixed(3)}, ${lng.toFixed(3)}`;

      if (pickerMarker) {
        pickerMarker.setLatLng([lat, lng]);
      } else {
        pickerMarker = L.marker([lat, lng]).addTo(pickerMap);
      }
    });
  }, 100);
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const data = await apiRequest("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });

    if (!data.is_verified) {
      showToast("Please verify your email address to activate your account.", "warning");
      setTimeout(() => {
        window.location.href = `verify-email.html?email=${encodeURIComponent(email)}`;
      }, 1500);
      return;
    }

    setAuth(data.access_token, data);
    showToast(`Welcome back, ${data.full_name}!`, "success");

    setTimeout(() => {
      if (data.role === "farmer") {
        window.location.href = "farmer-dashboard.html";
      } else if (data.role === "admin") {
        window.location.href = "admin-portal.html";
      } else {
        window.location.href = "marketplace.html";
      }
    }, 800);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-submit-register");
  btn.disabled = true;
  btn.textContent = "Registering...";

  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const full_name = document.getElementById("reg-name").value.trim();
  const phone = document.getElementById("reg-phone").value.trim();

  const payload = {
    email,
    password,
    full_name,
    phone,
    role: selectedRole
  };

  if (selectedRole === "farmer") {
    payload.farm_name = document.getElementById("reg-farm-name").value.trim() || `${full_name} Farm`;
    payload.farm_address = document.getElementById("reg-farm-address").value.trim();
    payload.farm_city = document.getElementById("reg-farm-city").value.trim();
    payload.farm_state = document.getElementById("reg-farm-state").value.trim();
    const lat = parseFloat(document.getElementById("reg-lat").value);
    const lng = parseFloat(document.getElementById("reg-lng").value);
    if (!isNaN(lat) && !isNaN(lng)) {
      payload.farm_lat = lat;
      payload.farm_lng = lng;
    }
  } else {
    payload.delivery_address = document.getElementById("reg-delivery-address").value.trim();
    payload.delivery_city = document.getElementById("reg-delivery-city").value.trim();
    payload.delivery_state = document.getElementById("reg-delivery-state").value.trim();
  }

  try {
    const res = await apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    showToast("Registration successful! Verification token generated.", "success");
    // Redirect to verify-email with dev token automatically attached
    const token = res.dev_verification_token || "";
    setTimeout(() => {
      window.location.href = `verify-email.html?token=${encodeURIComponent(token)}&email=${encodeURIComponent(email)}`;
    }, 1200);
  } catch (err) {
    showToast(err.message, "error");
    btn.disabled = false;
    btn.textContent = "Register & Send Verification Token";
  }
}

function fillDemo(role) {
  const emailInput = document.getElementById("login-email");
  const pwdInput = document.getElementById("login-password");

  if (role === "farmer") {
    emailInput.value = "rameshwar.patil@kisan.in";
    pwdInput.value = "password123";
  } else if (role === "admin") {
    emailInput.value = "admin@kisan2consumer.in";
    pwdInput.value = "Admin@123";
  } else {
    emailInput.value = "priya.sharma@consumer.in";
    pwdInput.value = "password123";
  }
  showToast(`Loaded demo credentials for ${role}!`, "info");
}
