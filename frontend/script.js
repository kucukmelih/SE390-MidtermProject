const defaultApiBase =
  window.location.hostname === "localhost"
    ? "http://localhost:5005"
    : `${window.location.origin}/api`;
const apiBase = window.API_BASE_URL || defaultApiBase;
const endpoint = `${apiBase}/predict`;
const productsEndpoint = `${apiBase}/products`;

const riskClasses = {
  High: "bg-danger",
  Medium: "bg-warning text-dark",
  Low: "bg-success",
};

function setStatus(card, text, badgeClass = "bg-secondary") {
  const badge = card.querySelector(".risk-result .badge");
  if (!badge) return;
  badge.className = `badge ${badgeClass}`;
  badge.textContent = text;
}

function toggleDetails(card) {
  const btn = card.querySelector(".toggle-details");
  const list = card.querySelector(".risk-result ul");
  if (!btn || !list) return;
  const hidden = list.classList.contains("d-none");
  list.classList.toggle("d-none", !hidden);
  btn.textContent = hidden ? "Hide" : "Details";
}

function enableDetails(card, enabled) {
  const btn = card.querySelector(".toggle-details");
  const list = card.querySelector(".risk-result ul");
  if (!btn) return;
  btn.classList.toggle("d-none", !enabled);
  if (card.dataset.mode === "form" && list) {
    btn.textContent = "Details";
    list.classList.add("d-none");
  }
}

function renderExplanations(card, explanations = []) {
  const list = card.querySelector(".risk-result ul");
  if (!list) return;
  list.innerHTML = "";
  explanations.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
}

function renderError(card, message) {
  const error = card.querySelector(".risk-result .error");
  if (!error) return;
  error.textContent = message;
  error.classList.remove("d-none");
  renderExplanations(card, []);
}

function clearError(card) {
  const error = card.querySelector(".risk-result .error");
  if (!error) return;
  error.textContent = "";
  error.classList.add("d-none");
}

function collectPayload(card) {
  if (card.dataset.mode === "form") {
    const inputs = card.querySelectorAll("[data-input]");
    const payload = {};
    inputs.forEach((input) => {
      const key = input.dataset.input;
      const value = parseFloat(input.value);
      if (Number.isNaN(value)) {
        throw new Error("Please fill every field with a number.");
      }
      payload[key] = value;
    });
    return payload;
  }

  return {
    stock_amount: parseFloat(card.dataset.stock || "0"),
    weekly_sales: parseFloat(card.dataset.weeklySales || "0"),
    product_age_days: parseFloat(card.dataset.productAgeDays || "0"),
    rating: parseFloat(card.dataset.rating || "0"),
    return_rate: parseFloat(card.dataset.returnRate || "0"),
  };
}

async function requestPrediction(payload) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function getProductInfo(card) {
  if (card.dataset.mode === "form") {
    const inputs = card.querySelectorAll("[data-input]");
    const fields = {};
    inputs.forEach((input) => {
      fields[input.dataset.input] = input.value;
    });
    return {
      name: "Custom Scenario",
      category: "Ad-hoc",
      description: "User-entered product parameters.",
      image:
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
      stock_amount: fields.stock_amount || "?",
      weekly_sales: fields.weekly_sales || "?",
      product_age_days: fields.product_age_days || "?",
      rating: fields.rating || "?",
      return_rate: fields.return_rate || "?",
    };
  }

  return {
    name: card.dataset.name || "Product",
    category: card.dataset.category || "Inventory",
    description: card.dataset.description || "",
    image: card.dataset.image || "",
    stock_amount: card.dataset.stock || "?",
    weekly_sales: card.dataset.weeklySales || "?",
    product_age_days: card.dataset.productAgeDays || "?",
    rating: card.dataset.rating || "?",
    return_rate: card.dataset.returnRate || "?",
  };
}

function openModal(data) {
  const overlay = document.getElementById("modal-overlay");
  if (!overlay) return;

  const title = document.getElementById("modal-title");
  const category = document.getElementById("modal-category");
  const desc = document.getElementById("modal-description");
  const image = document.getElementById("modal-image");
  const badge = document.getElementById("modal-risk-badge");
  const stats = document.getElementById("modal-stats");
  const expl = document.getElementById("modal-explanations");

  title.textContent = data.product.name;
  category.textContent = data.product.category;
  desc.textContent = data.product.description || "";
  if (data.product.image) {
    image.src = data.product.image;
    image.classList.remove("d-none");
  } else {
    image.classList.add("d-none");
  }

  const badgeClass = riskClasses[data.risk] || "bg-secondary";
  badge.className = `badge ${badgeClass}`;
  badge.textContent = `${data.risk} Risk`;

  stats.textContent = `Stock ${data.product.stock_amount} • Weekly sales ${data.product.weekly_sales} • Age ${data.product.product_age_days} days • Rating ${data.product.rating} • Returns ${(
    Number(data.product.return_rate) * 100
  ).toFixed(0)}%`;

  expl.innerHTML = "";
  data.explanations.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    expl.appendChild(li);
  });

  overlay.classList.remove("d-none");
}

function setupModalClose() {
  const overlay = document.getElementById("modal-overlay");
  const closeBtn = document.getElementById("modal-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => overlay.classList.add("d-none"));
  }
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.add("d-none");
    });
  }
}

function openModalFromCard(card) {
  const data = card.__riskData;
  if (!data) return;
  openModal(data);
}

async function handleCard(card) {
  const button = card.querySelector(".check-risk");
  if (!button) return;

  const toggleBtn = card.querySelector(".toggle-details");
  if (toggleBtn && !toggleBtn.dataset.bound) {
    toggleBtn.dataset.bound = "true";
    if (card.dataset.mode === "form") {
      toggleBtn.addEventListener("click", () => toggleDetails(card));
    } else {
      toggleBtn.addEventListener("click", () => openModalFromCard(card));
    }
  }

  button.addEventListener("click", async () => {
    button.disabled = true;
    clearError(card);
    setStatus(card, "Checking...", "bg-info text-dark");
    renderExplanations(card, []);
    enableDetails(card, false);

    try {
      const payload = collectPayload(card);
      const { risk, explanations } = await requestPrediction(payload);
      const badgeClass = riskClasses[risk] || "bg-secondary";
      setStatus(card, `${risk} Risk`, badgeClass);
      renderExplanations(card, explanations);
      enableDetails(card, true);
      card.__riskData = {
        risk,
        explanations,
        product: getProductInfo(card),
      };
    } catch (err) {
      setStatus(card, "Error", "bg-danger");
      renderError(card, err.message);
      enableDetails(card, false);
    } finally {
      button.disabled = false;
    }
  });
}

function createProductCard(product) {
  const col = document.createElement("div");
  col.className = "col-12 col-md-6 col-lg-4";
  col.dataset.riskCard = "";
  col.dataset.stock = product.stock_amount;
  col.dataset.weeklySales = product.weekly_sales;
  col.dataset.productAgeDays = product.product_age_days;
  col.dataset.rating = product.rating;
  col.dataset.returnRate = product.return_rate;
  col.dataset.name = product.name;
  col.dataset.category = product.category;
  col.dataset.description = product.description;
  col.dataset.image = product.image;

  col.innerHTML = `
    <div class="card product-card h-100 shadow">
      <img src="${product.image}" class="card-img-top" alt="${product.name}" />
      <div class="card-body d-flex flex-column">
        <p class="product-category">${product.category}</p>
        <h5 class="card-title">${product.name}</h5>
        <p class="card-text text-muted">${product.description}</p>
        <ul class="small text-muted mb-3">
          <li>Stock: ${product.stock_amount} units</li>
          <li>Weekly sales: ${product.weekly_sales} units</li>
          <li>Age: ${product.product_age_days} days in inventory</li>
          <li>Rating: ${product.rating}, Returns: ${(product.return_rate * 100).toFixed(0)}%</li>
        </ul>
        <div class="mt-auto">
          <div class="risk-result mb-3">
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <span class="badge bg-secondary">Awaiting check</span>
              <button class="btn btn-sm btn-outline-light toggle-details d-none" type="button">
                Details
              </button>
            </div>
            <ul class="list-unstyled mt-2 mb-0 d-none"></ul>
            <div class="error small text-danger mt-1 d-none"></div>
          </div>
          <button class="btn btn-primary w-100 check-risk">Check Risk</button>
        </div>
      </div>
    </div>
  `;

  return col;
}

async function loadProducts() {
  const container = document.getElementById("products-row");
  if (!container) return;

  try {
    const res = await fetch(productsEndpoint);
    const data = await res.json();
    const products = data.products || [];

    products.forEach((product) => {
      const card = createProductCard(product);
      container.prepend(card);
      handleCard(card);
    });
  } catch (err) {
    // If fetching products fails, surface minimal message in console.
    console.error("Failed to load products", err);
  }
}

function initPage() {
  document.querySelectorAll("[data-risk-card]").forEach(handleCard);
  loadProducts();
  setupModalClose();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPage);
} else {
  initPage();
}
