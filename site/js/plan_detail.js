(function () {
  var b = (typeof window.API_BASE === 'string' && window.API_BASE) || location.origin;
  try { b = new URL(b, location.href).origin; } catch { b = location.origin; }
  window.API_BASE = String(b).replace(/\/+$/, '');
})();
function api(path){ return window.API_BASE + path; }

function pickEndpoint(type){
  type = (type||'').toLowerCase();
  if(type === 'training') return '/api/training_plans/';
  if(type === 'diet') return '/api/diet_plans/';
  return '/api/plans/';
}
function updateTypeVisibility(){
  var t = document.getElementById('plan-type');
  var type = t ? t.value : '';
  var train = document.getElementById('training-editor') || document.getElementById('training-section');
  var diet  = document.getElementById('diet-editor') || document.getElementById('diet-section');
  if(train){ train.style.display = (type === 'training') ? '' : 'none'; }
  if(diet){  diet.style.display  = (type === 'diet') ? '' : 'none'; }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("add-plan-form");
  updateTypeVisibility();
  var typeSel = document.getElementById('plan-type');
  if(typeSel){ typeSel.addEventListener('change', updateTypeVisibility); }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Basic validation for plan name
    const planName = document.getElementById("plan-name").value.trim();
    const planType = document.getElementById("plan-type").value;
    const planDescription = document.getElementById("plan-description").value;
    if (!planName) {
      alert("Please enter a plan name.");
      return;
    }

    // Collect exercises if present
    let exercises = [];
    if (planType === "training") {
      // Look for exercise rows/fields
      const exerciseRows = document.querySelectorAll(".exercise-row");
      exerciseRows.forEach(row => {
        const exercise_name = row.querySelector(".exercise-name") ? row.querySelector(".exercise-name").value.trim() : "";
        const sets = row.querySelector(".exercise-sets") ? row.querySelector(".exercise-sets").value.trim() : "";
        const reps = row.querySelector(".exercise-reps") ? row.querySelector(".exercise-reps").value.trim() : "";
        if (exercise_name) {
          exercises.push({
            exercise_name,
            sets,
            reps
          });
        }
      });
      if (exercises.length === 0) {
        alert("Please add at least one exercise for a training plan.");
        return;
      }
    }

    // Collect diet items if present
    let diet_items = [];
    if (planType === "diet") {
      const dietRows = document.querySelectorAll(".diet-row");
      dietRows.forEach(row => {
        const item_name = row.querySelector(".diet-item-name") ? row.querySelector(".diet-item-name").value.trim() : "";
        const quantity = row.querySelector(".diet-item-quantity") ? row.querySelector(".diet-item-quantity").value.trim() : "";
        const calories = row.querySelector(".diet-item-calories") ? row.querySelector(".diet-item-calories").value.trim() : "";
        if (item_name) {
          diet_items.push({
            item_name,
            quantity,
            calories
          });
        }
      });
      if (diet_items.length === 0) {
        alert("Please add at least one diet item for a diet plan.");
        return;
      }
    }

    const planData = {
      name: planName,
      type: planType,
      description: planDescription,
    };
    if (exercises.length > 0) {
      planData.exercises = exercises;
    }
    if (diet_items.length > 0) {
      planData.diet_items = diet_items;
    }

    try {
      const url = api(pickEndpoint(planType));
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(planData),
      });

      if (!res.ok) throw new Error("Failed to create plan");

      alert("Plan created successfully!");
      window.location.href = "plans.html";  // redirect to plans page
    } catch (err) {
      alert("Error creating plan");
      console.error(err);
    }
  });
});