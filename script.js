// ==============================
// BASE URL (Flask backend)
// ==============================
const BASE_URL = "http://127.0.0.1:5000";


// ==============================
// ADD MEMBER
// ==============================
function addMember() {

    // Get values from input fields
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const role = document.getElementById("role").value;
    const coursework_id = document.getElementById("coursework_id").value;

    // Send data to Flask backend
    fetch(`${BASE_URL}/add_member`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            email: email,
            role: role,
            coursework_id: parseInt(coursework_id)
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("✅ Member Added!");

        // Clear inputs after submit (important UX fix)
        document.getElementById("name").value = "";
        document.getElementById("email").value = "";
        document.getElementById("role").value = "";
        document.getElementById("coursework_id").value = "";

        console.log(data);
    })
    .catch(err => console.error(err));
}


// ==============================
// LOAD UPCOMING TASKS
// ==============================
function loadUpcoming() {

    fetch(`${BASE_URL}/upcoming`)
    .then(res => res.json())
    .then(data => {

        const list = document.getElementById("taskList");
        list.innerHTML = "";

        data.forEach(task => {

            const li = document.createElement("li");

            // Show task info
            li.textContent = `${task.title} (${task.days_left} days left)`;

            // FIXED BUG: use "status" not "deadline_status"
            if (task.status === "URGENT ⚠️") {
                li.classList.add("urgent");
            } else {
                li.classList.add("normal");
            }

            list.appendChild(li);
        });
    })
    .catch(err => console.error(err));
}


// ==============================
// LOAD ALERTS (URGENT TASKS)
// ==============================
function loadAlerts() {

    fetch(`${BASE_URL}/alerts`)
    .then(res => res.json())
    .then(data => {

        const list = document.getElementById("alertList");
        list.innerHTML = "";

        data.forEach(task => {

            const li = document.createElement("li");

            li.textContent = `${task.title} ⚠️ Due in ${task.days_left} days`;
            li.classList.add("urgent");

            list.appendChild(li);
        });
    })
    .catch(err => console.error(err));
}