const detailStatusElement = document.getElementById("detail-status");
const customerNameElement = document.getElementById("customer-name");
const customerSummaryElement = document.getElementById("customer-summary");
const customerDetailsElement = document.getElementById("customer-details");

const DETAIL_FIELDS = [
  ["ID", "id"],
  ["First name", "first_name"],
  ["Last name", "last_name"],
  ["Email", "email"],
  ["Gender", "gender"],
  ["IP address", "ip_address"],
  ["Company", "company"],
  ["City", "city"],
  ["Title", "title"],
  ["Website", "website"],
];

async function loadCustomer() {
  const customerId = getCustomerIdFromPath();
  if (customerId === null) {
    renderError("Invalid customer id.");
    return;
  }

  detailStatusElement.textContent = "Loading customer details...";

  try {
    const response = await fetch(`/api/customers/${customerId}`);
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Unable to load customer.");
    }

    renderCustomer(payload.data);
  } catch (error) {
    renderError(error.message);
  }
}

function getCustomerIdFromPath() {
  const segments = window.location.pathname.split("/").filter(Boolean);
  const rawCustomerId = segments.at(-1);
  if (!rawCustomerId) {
    return null;
  }

  const customerId = Number.parseInt(rawCustomerId, 10);
  return Number.isNaN(customerId) || customerId < 1 ? null : customerId;
}

function renderCustomer(customer) {
  const fullName = `${customer.first_name} ${customer.last_name}`;
  customerNameElement.textContent = fullName;
  customerSummaryElement.textContent = `${customer.email} · ${customer.company || "No company listed"}`;
  detailStatusElement.textContent = "";
  customerDetailsElement.innerHTML = DETAIL_FIELDS.map(([label, key]) => renderField(label, key, customer[key])).join("");
  bindCopyButtons();
}

function renderField(label, key, value) {
  const isWebsiteField = key === "website";
  const displayValue = isWebsiteField ? renderWebsite(value) : escapeHtml(value || "—");
  const fieldLabel = isWebsiteField
    ? `${escapeHtml(label)} <button type="button" class="btn btn-sm btn-link p-0 align-baseline ms-2 js-copy-website" data-copy-value="${escapeHtml(value || "")}" aria-label="Copy website">Copy</button>`
    : escapeHtml(label);
  return `
    <div class="col">
      <div class="detail-card h-100 p-3 p-md-4">
        <dt class="mb-1 small text-uppercase text-secondary fw-semibold">${fieldLabel}</dt>
        <dd class="mb-0">${displayValue}</dd>
      </div>
    </div>
  `;
}

function renderWebsite(value) {
  if (!value) {
    return "—";
  }

  // Keep the href and the visible label escaped because the source data comes
  // from the imported CSV rather than trusted literals.
  const safeValue = escapeHtml(value);
  const displayValue = escapeHtml(shortenUrl(value));
  return `
    <div class="d-flex flex-wrap align-items-center gap-2">
      <a class="fw-semibold text-decoration-none text-break website-link" href="${safeValue}" target="_blank" rel="noreferrer">${displayValue}</a>
    </div>
  `;
}

function renderError(message) {
  customerNameElement.textContent = "Customer Details";
  customerSummaryElement.textContent = "Customer data unavailable";
  customerDetailsElement.innerHTML = "";
  detailStatusElement.textContent = message;
}

function shortenUrl(value) {
  const trimmed = String(value).trim();
  const withoutProtocol = trimmed.replace(/^https?:\/\//i, "");
  if (withoutProtocol.length <= 34) {
    return withoutProtocol;
  }

  return `${withoutProtocol.slice(0, 18)}...${withoutProtocol.slice(-10)}`;
}

function bindCopyButtons() {
  customerDetailsElement.querySelectorAll(".js-copy-website").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.getAttribute("data-copy-value");
      if (!value) {
        return;
      }

      const copied = await copyText(value);
      if (copied) {
        const originalLabel = button.textContent;
        button.textContent = "Copied";
        button.classList.remove("btn-outline-secondary");
        button.classList.add("btn-outline-success");
        window.setTimeout(() => {
          button.textContent = originalLabel;
          button.classList.remove("btn-outline-success");
          button.classList.add("btn-outline-secondary");
        }, 1200);
      }
    });
  });
}

async function copyText(value) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (error) {
    // Fall back to the legacy clipboard path below for local/http environments.
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "readonly");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (error) {
    copied = false;
  } finally {
    document.body.removeChild(textarea);
  }

  return copied;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

loadCustomer();
