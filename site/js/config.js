// ----------------------------------------
// Build absolute API URLs from current origin (ignores any bad API_BASE)
function API(path) {
  return location.origin.replace(/\/+$/, '') + path;
}

async function fetchClients() {
  const response = await fetch(API("/api/clients/"), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  return await response.json();
}

async function createClient(clientData) {
  console.log("POST URL:", API("/api/clients/"));
  const response = await fetch(API("/api/clients/"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(clientData),
  });
  return await response.json();
}

async function fetchClient(clientId) {
  const response = await fetch(API(`/api/clients/${clientId}/`), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  return await response.json();
}

async function updateClient(clientId, clientData) {
  const response = await fetch(API(`/api/clients/${clientId}/`), {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(clientData),
  });
  return await response.json();
}

async function fetchPlans() {
  const response = await fetch(API("/api/plans/"));
  return await response.json();
}

async function fetchClientPlanHistory(clientId) {
  const response = await fetch(API(`/api/client_plans/${clientId}/history`));
  return await response.json();
}

async function createClientPlan(planData) {
  const response = await fetch(API(`/api/client_plans/`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(planData),
  });
  return await response.json();
}
