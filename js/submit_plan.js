document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("add-plan-form");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const planData = {
      name: document.getElementById("plan-name").value,
      type: document.getElementById("plan-type").value,
      description: document.getElementById("plan-description").value,
    };

    try {
      const res = await fetch("http://localhost:8000/api/plans/", {
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