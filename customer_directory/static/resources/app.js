const state = {
  page: 1,
  pageSize: 20,
  search: "",
  totalPages: 0,
  total: 0,
};

const rowsElement = document.getElementById("customer-rows");
const statusElement = document.getElementById("status");
const summaryElement = document.getElementById("summary");
const paginationSummaryElement = document.getElementById("pagination-summary");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchButton = document.getElementById("search-button");
const $paginationNav = window.jQuery("#pagination-nav");

function initializePagination(pageNumber = 1) {
  destroyPagination();
  setLoadingState(true);
  statusElement.textContent = "Loading customers...";

  $paginationNav.pagination({
    dataSource: "/api/customers",
    locator: "data",
    totalNumberLocator(response) {
      return response.pagination.total;
    },
    alias: {
      pageNumber: "page",
      pageSize: "page_size",
    },
    ajax: {
      dataType: "json",
      data: {
        search: state.search,
      },
    },
    pageNumber,
    pageSize: state.pageSize,
    pageRange: 2,
    showPrevious: true,
    showNext: true,
    showPageNumbers: true,
    showGoInput: true,
    showGoButton: true,
    hideOnlyOnePage: true,
    prevText: "Previous",
    nextText: "Next",
    className: "customer-pagination",
    ulClassName: "customer-pagination-list",
    activeClassName: "is-current",
    disableClassName: "is-disabled",
    formatGoInput() {
      return `
        <input
          type="text"
          class="J-paginationjs-go-pagenumber form-control form-control-sm text-center"
          inputmode="numeric"
          aria-label="Page number"
        >
      `;
    },
    formatGoButton(button) {
      return `
        <span class="J-paginationjs-go-button custom-go-btn">Go</span>
      `;
    },
    callback(data, pagination) {
      const payload = pagination.originalResponse;
      if (!payload) {
        return;
      }

      renderRows(data);
      syncState(payload.pagination);
      applyPaginationClasses();
      statusElement.textContent = "";
      setLoadingState(false);
    },
    formatAjaxError(jqXHR) {
      const message = jqXHR.responseJSON?.error || "Unable to load customers.";
      renderError(message);
      setLoadingState(false);
    },
  });
}

function destroyPagination() {
  if ($paginationNav.data("pagination")?.initialized) {
    $paginationNav.pagination("destroy");
  }
}

function syncState(pagination) {
  state.page = pagination.page;
  state.totalPages = pagination.total_pages;
  state.total = pagination.total;
  state.search = pagination.search;
  searchInput.value = state.search;
  summaryElement.textContent = buildSummary(pagination);
  paginationSummaryElement.textContent = buildPaginationSummary(pagination);
}

function renderRows(customers) {
  if (customers.length === 0) {
    rowsElement.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">No customers found for this page.</td>
      </tr>
    `;
    return;
  }

  // The table is rendered with innerHTML for simplicity, so every dynamic value
  // must be escaped before insertion.
  rowsElement.innerHTML = customers
    .map(
      (customer) => `
        <tr>
          <td>
            <a class="fw-semibold text-decoration-none" href="/customers/${customer.id}">
              ${escapeHtml(`${customer.first_name} ${customer.last_name}`)}
            </a>
          </td>
          <td>${escapeHtml(customer.email)}</td>
          <td>${escapeHtml(customer.gender || "—")}</td>
          <td>${escapeHtml(customer.company || "—")}</td>
          <td>${escapeHtml(customer.city || "—")}</td>
          <td>${escapeHtml(customer.title || "—")}</td>
        </tr>
      `,
    )
    .join("");
}

function applyPaginationClasses() {
  const root = document.querySelector("#pagination-nav .paginationjs");
  if (!root) {
    return;
  }

  root.classList.add(
    "customer-pagination",
    "d-flex",
    "flex-nowrap",
    "gap-3",
    "align-items-center",
    "justify-content-center",
    "w-100",
  );

  root.querySelector(".paginationjs-pages")?.classList.add("flex-shrink-0");
  root.querySelector(".paginationjs-pages ul")?.classList.add(
    "pagination",
    "mb-0",
    "justify-content-center",
  );

  root.querySelectorAll(".paginationjs-pages li").forEach((item) => {
    item.classList.add("page-item");
  });

  root.querySelectorAll(".paginationjs-pages li > a").forEach((link) => {
    link.className = "page-link";
  });

  root.querySelectorAll(".paginationjs-pages li.is-current").forEach((item) => {
    item.classList.add("active");
  });

  root.querySelectorAll(".paginationjs-pages li.is-disabled").forEach((item) => {
    item.classList.add("disabled");
  });

  root.querySelectorAll(".paginationjs-pages li.paginationjs-ellipsis > a").forEach((link) => {
    link.className = "page-link border-0 bg-transparent text-secondary";
  });

  root.querySelector(".paginationjs-go-input")?.classList.add(
    "d-flex",
    "align-items-center",
    "gap-2",
    "justify-content-center",
    "flex-shrink-0",
  );

  root.querySelector(".paginationjs-go-button")?.classList.add("flex-shrink-0");
}

function renderError(message) {
  state.totalPages = 0;
  rowsElement.innerHTML = "";
  summaryElement.textContent = "Customer data unavailable";
  paginationSummaryElement.textContent = "Page information unavailable";
  statusElement.textContent = message;
  destroyPagination();
}

function setLoadingState(isLoading) {
  searchInput.disabled = isLoading;
  searchButton.disabled = isLoading;
}

function buildSummary(pagination) {
  const baseSummary = `Page ${pagination.page} of ${pagination.total_pages || 1} · ${pagination.total} total customers`;
  return pagination.search ? `${baseSummary} · Search: ${pagination.search}` : baseSummary;
}

function buildPaginationSummary(pagination) {
  return `Page ${pagination.page} of ${pagination.total_pages || 1}`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const nextSearch = searchInput.value.trim();
  if (nextSearch === state.search && state.page === 1) {
    statusElement.textContent = "";
    return;
  }

  state.search = nextSearch;
  initializePagination(1);
});

initializePagination();
