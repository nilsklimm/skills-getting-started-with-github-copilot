// Global variables for DOM elements
let activitiesList, activitySelect, signupForm, messageDiv;

// helper invoked by inline onclick handlers
async function removeParticipant(activity, email) {
  try {
    const resp = await fetch(
      `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
      { method: 'DELETE' }
    );
    if (resp.ok) {
      fetchActivities();
    } else {
      const err = await resp.json();
      console.error('Failed to remove participant:', err.detail || err);
    }
  } catch (err) {
    console.error('Error unregistering participant', err);
  }
}

// Function to fetch activities from API
async function fetchActivities() {
  try {
    const response = await fetch("/activities");
    const activities = await response.json();

    // Clear loading message
    activitiesList.innerHTML = "";

    // Populate activities list
    Object.entries(activities).forEach(([name, details]) => {
      const activityCard = document.createElement("div");
      activityCard.className = "activity-card";

      const spotsLeft = details.max_participants - details.participants.length;

      activityCard.innerHTML = `
        <h4>${name}</h4>
        <p>${details.description}</p>
        <p><strong>Schedule:</strong> ${details.schedule}</p>
        <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
        <div class="participants">
          <p><strong>Participants:</strong></p>
          <ul>
            ${details.participants.length > 0
              ? details.participants
                  .map(
                    (p) =>
                      `<li>
                          ${p}
                          <button type="button" class="remove-participant" onclick="removeParticipant('${name}', '${p}')" title="Unregister">✖</button>
                       </li>`
                  )
                  .join("")
              : '<li><em>No one signed up yet.</em></li>'}
          </ul>
        </div>
      `;

      activitiesList.appendChild(activityCard);

      // Add option to select dropdown
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      activitySelect.appendChild(option);
    });
  } catch (error) {
    activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
    console.error("Error fetching activities:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  activitiesList = document.getElementById("activities-list");
  activitySelect = document.getElementById("activity");
  signupForm = document.getElementById("signup-form");
  messageDiv = document.getElementById("message");

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();  // Refresh the activities list to show the new participant
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
