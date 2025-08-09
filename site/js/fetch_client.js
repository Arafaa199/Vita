// --- API base fallback & normalization ---
(function () {
  var base = (typeof window.API_BASE === 'string' && window.API_BASE) || location.origin;
  try {
    var u = new URL(base, location.href);
    // Force to pure origin (strip any path like /html)
    base = u.origin;
  } catch (e) {
    base = location.origin;
  }
  // strip trailing slashes just in case
  window.API_BASE = String(base).replace(/\/+$/, '');
})();
// ----------------------------------------
// Build absolute API URLs from current origin (unique name to avoid globals)
function buildApiUrl(path) {
  return location.origin.replace(/\/+$/, '') + path;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const phone = document.getElementById("phone").value.trim();
      const heightVal = document.getElementById("height").value.trim();
      const height = parseFloat(heightVal);

      if (!phone) {
        alert("❌ Please enter a valid phone number.");
        return;
      }
      if (!heightVal || isNaN(height) || height <= 0) {
        alert("❌ Please enter a valid height in cm.");
        return;
      }

      const data = {
        full_name: document.getElementById("fullName").value,
        email: document.getElementById("email").value,
        phone: phone,
        height: height,
        age: parseInt(document.getElementById("age").value),
        weight: parseFloat(document.getElementById("weight").value),
        goal: document.getElementById("goal").value,
        membership_active: document.getElementById("membership_active").value === "true",
        start_date: document.getElementById("start_date").value,
        end_date: document.getElementById("end_date").value,
        membership_length: document.getElementById("membership_length").value,
      };

      try {
        console.log("POST URL:", buildApiUrl("/api/clients/"));
        const response = await fetch(buildApiUrl("/api/clients/"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        if (response.ok) {
          alert("✅ Client added successfully");
          form.reset();
        } else {
          const error = await response.json();
          alert("❌ Error: " + (error.detail || response.statusText));
        }
      } catch (err) {
        alert("❌ Request failed: " + err.message);
      }
    });
  }

  // Additional code from client_detail.html's removed <script> block:

  const urlPath = window.location.pathname;
  const clientIdMatch = urlPath.match(/\/clients\/(\d+)/);
  const clientId = clientIdMatch ? clientIdMatch[1] : null;

  const loadClient = async () => {
    try {
      const response = await fetch(buildApiUrl(`/api/clients/${clientId}/`));
      if (!response.ok) throw new Error("Failed to load client");
      const client = await response.json();

      document.getElementById("fullName").value = client.full_name || "";
      document.getElementById("email").value = client.email || "";
      document.getElementById("phone").value = client.phone || "";
      document.getElementById("height").value = client.height || "";
      document.getElementById("age").value = client.age || "";
      document.getElementById("weight").value = client.weight || "";
      document.getElementById("goal").value = client.goal || "";
      document.getElementById("membership_active").checked = client.membership_active || false;
      document.getElementById("start_date").value = client.start_date || "";
      document.getElementById("end_date").value = client.end_date || "";
      document.getElementById("membership_length").value = client.membership_length || "";
    } catch (error) {
      alert("❌ " + error.message);
    }
  };

  const saveChanges = async () => {
    const phone = document.getElementById("phone").value.trim();
    const heightVal = document.getElementById("height").value.trim();
    const height = parseFloat(heightVal);

    if (!phone) {
      alert("❌ Please enter a valid phone number.");
      return;
    }
    if (!heightVal || isNaN(height) || height <= 0) {
      alert("❌ Please enter a valid height in cm.");
      return;
    }

    const data = {
      full_name: document.getElementById("fullName").value,
      email: document.getElementById("email").value,
      phone: phone,
      height: height,
      age: parseInt(document.getElementById("age").value),
      weight: parseFloat(document.getElementById("weight").value),
      goal: document.getElementById("goal").value,
      membership_active: document.getElementById("membership_active").checked,
      start_date: document.getElementById("start_date").value,
      end_date: document.getElementById("end_date").value,
      membership_length: document.getElementById("membership_length").value,
    };

    try {
      const response = await fetch(buildApiUrl(`/api/clients/${clientId}/`), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        alert("✅ Client updated successfully");
      } else {
        const error = await response.json();
        alert("❌ Error: " + (error.detail || response.statusText));
      }
    } catch (err) {
      alert("❌ Request failed: " + err.message);
    }
  };

  const deleteClient = async () => {
    if (!confirm("Are you sure you want to delete this client?")) return;
    try {
      const response = await fetch(buildApiUrl(`/api/clients/${clientId}/`), {
        method: "DELETE",
      });
      if (response.ok) {
        alert("✅ Client deleted successfully");
        window.location.href = "/html/clients.html";
      } else {
        const error = await response.json();
        alert("❌ Error: " + (error.detail || response.statusText));
      }
    } catch (err) {
      alert("❌ Request failed: " + err.message);
    }
  };

  const loadPlans = async () => {
    try {
      const response = await fetch(buildApiUrl("/api/plans/"));
      if (!response.ok) throw new Error("Failed to load plans");
      const plans = await response.json();
      const planSelect = document.getElementById("planSelect");
      planSelect.innerHTML = "";
      plans.forEach(plan => {
        const option = document.createElement("option");
        option.value = plan.id;
        option.textContent = plan.name;
        planSelect.appendChild(option);
      });
    } catch (error) {
      alert("❌ " + error.message);
    }
  };

  const loadAssignedPlans = async () => {
    try {
      const response = await fetch(buildApiUrl(`/api/client_plans/${clientId}/history`));
      if (!response.ok) throw new Error("Failed to load assigned plans");
      const assignedPlans = await response.json();
      const assignedPlansList = document.getElementById("assignedPlansList");
      assignedPlansList.innerHTML = "";
      assignedPlans.forEach(plan => {
        const li = document.createElement("li");
        li.textContent = plan.name;
        assignedPlansList.appendChild(li);
      });
    } catch (error) {
      alert("❌ " + error.message);
    }
  };

  const assignPlan = async () => {
    const planId = document.getElementById("planSelect").value;
    if (!planId) {
      alert("❌ Please select a plan to assign.");
      return;
    }
    try {
      const response = await fetch(buildApiUrl(`/api/client_plans/`), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ client_id: Number(clientId), plan_id: Number(planId) }),
      });
      if (response.ok) {
        alert("✅ Plan assigned successfully");
        loadAssignedPlans();
      } else {
        const error = await response.json();
        alert("❌ Error: " + (error.detail || response.statusText));
      }
    } catch (err) {
      alert("❌ Request failed: " + err.message);
    }
  };

  const saveButton = document.getElementById("saveButton");
  if (saveButton) {
    saveButton.addEventListener("click", (e) => {
      e.preventDefault();
      saveChanges();
    });
  }

  const deleteButton = document.getElementById("deleteButton");
  if (deleteButton) {
    deleteButton.addEventListener("click", (e) => {
      e.preventDefault();
      deleteClient();
    });
  }

  const assignPlanButton = document.getElementById("assignPlanButton");
  if (assignPlanButton) {
    assignPlanButton.addEventListener("click", (e) => {
      e.preventDefault();
      assignPlan();
    });
  }

  if (clientId) {
    loadClient();
    loadPlans();
    loadAssignedPlans();
  }
});
