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

    const trainingList = document.getElementById("training-plan-list");
    const dietList = document.getElementById("diet-plan-list");
    const legacyList = document.getElementById("plan-list");

    // Legacy page: single list
    if (!trainingList && !dietList && legacyList) {
      legacyList.innerHTML = "";
      if (!Array.isArray(plans) || plans.length===0) {
        legacyList.innerHTML = '<li class="empty">No plans yet</li>';
        return;
      }
      plans.forEach(plan => {
        const li = document.createElement("li");
        li.textContent = plan.name || `Plan #${plan.id}`;
        li.classList.add("plan-item");
        li.onclick = () => { window.location.href = `plan_detail.html?id=${plan.id}`; };
        legacyList.appendChild(li);
      });
      return;
    }

    // New split layout: training & diet
    if (trainingList) trainingList.innerHTML = "";
    if (dietList) dietList.innerHTML = "";

    const listOrEmpty = (ul, items) => {
      if (!ul) return;
      if (!items || items.length===0) {
        ul.innerHTML = '<li class="empty">No plans yet</li>';
        return;
      }
      items.forEach(plan => {
        const li = document.createElement("li");
        li.className = "plan-item";
        li.textContent = plan.name || `Plan #${plan.id}`;
        li.onclick = () => { window.location.href = `plan_detail.html?id=${plan.id}`; };
        ul.appendChild(li);
      });
    };

    const tPlans = plans.filter(p => (p.type||"").toLowerCase()==='training');
    const dPlans = plans.filter(p => (p.type||"").toLowerCase()==='diet');

    // Any uncategorized plans go to training by default to keep them visible
    const other = plans.filter(p => ['training','diet'].indexOf((p.type||"").toLowerCase())===-1);

    listOrEmpty(trainingList, tPlans.concat(other));
    listOrEmpty(dietList, dPlans);

  } catch (err) {
    console.error("Error loading plans:", err);
    alert("❌ Failed to load plans");
  }
});
