(function(){
  var b=(typeof window.API_BASE==='string'&&window.API_BASE)||location.origin;
  try{ b=new URL(b,location.href).origin; }catch(e){ b=location.origin; }
  window.API_BASE=String(b).replace(/\/+$/,'');
})();
function api(path){ return window.API_BASE + path; }
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch(api("/api/plans/"));
    if (!res.ok) throw new Error("Failed to fetch plans");

    const plans = await res.json();
    const planList = document.getElementById("plan-list");
    if(!planList) return;
    planList.innerHTML = ""; // Clear default/sample items
    if(!Array.isArray(plans) || plans.length===0){ planList.innerHTML = '<li class="empty">No plans yet</li>'; return; }
    plans.forEach(plan => {
      const li = document.createElement("li");
      li.textContent = `${plan.name}`;
      li.classList.add("plan-item");
      li.onclick = () => {
        window.location.href = `plan_detail.html?id=${plan.id}`;
      };
      planList.appendChild(li);
    });
  } catch (err) {
    console.error("Error loading plans:", err);
    alert("❌ Failed to load plans");
  }
});
