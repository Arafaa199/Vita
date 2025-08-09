document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("http://localhost:8000/api/plans/");
    if (!res.ok) throw new Error("Failed to fetch plans");

    const plans = await res.json();
    const planList = document.getElementById("plan-list");

    planList.innerHTML = ""; // Clear default/sample items

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
  }
});
