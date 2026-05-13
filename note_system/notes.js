// ===== FRIEND NAVIGATION CODE =====

function toggleMenu() {
    let menu = document.getElementById("menu");

    if (menu) {
        menu.style.display =
            menu.style.display === "block" ? "none" : "block";
    }
}

function goHome() {
    window.location.href = "dashboard.html";
}

function goWork() {
    window.location.href = "work.html";
}

function goGenerateQuiz() {
    window.location.href = "generatequiz.html";
}

function goGenerateNotes() {
    window.location.href = "notes.html";
}

function goProfile() {
    window.location.href = "profile.html";
}

function goSettings() {
    window.location.href = "settings.html";
}

function logout() {
    window.location.href = "login1.html";
}


// ===== GENERATE NOTES =====

function generateDummyNotes() {
    const notesArea = document.getElementById("notesArea");

    notesArea.value = `Generated Study Notes

1. Overview
These notes are generated as a frontend demo.

2. Key Points
- Main ideas are summarized clearly.
- Notes can be edited manually.
- Backend will connect the real AI later.

3. Revision
After reading the notes, tick the related checklist items to update progress.

4. Summary
This page allows students to upload material, generate notes, edit them, and track revision progress.`;
}


// ===== SAVE / COPY / CLEAR =====

function saveNotes() {
    alert("Notes saved successfully.");
}

function copyNotes() {
    const notesArea = document.getElementById("notesArea");

    notesArea.select();
    document.execCommand("copy");

    alert("Notes copied.");
}

function clearNotes() {
    document.getElementById("notesArea").value = "";
}


// ===== SUBJECT SWITCHING + PROGRESS TRACKING =====

const subjectCards = document.querySelectorAll(".subject-card");

const topicLists = {
    software: document.getElementById("softwareTopics"),
    ethical: document.getElementById("ethicalTopics"),
    system: document.getElementById("systemTopics")
};

subjectCards.forEach(card => {
    card.addEventListener("click", () => {

        subjectCards.forEach(c => {
            c.classList.remove("active-subject");
        });

        card.classList.add("active-subject");

        Object.values(topicLists).forEach(list => {
            list.classList.add("hidden");
        });

        const selectedSubject = card.dataset.subject;

        topicLists[selectedSubject].classList.remove("hidden");

        updateProgress();
    });
});

document.querySelectorAll(".topic-check").forEach(box => {
    box.addEventListener("change", updateProgress);
});

function updateProgress() {
    const activeSubject = document.querySelector(".active-subject").dataset.subject;

    const checkboxes = document.querySelectorAll(
        `.topic-check[data-subject="${activeSubject}"]`
    );

    const checked = document.querySelectorAll(
        `.topic-check[data-subject="${activeSubject}"]:checked`
    );

    const total = checkboxes.length;

    const percentage =
        total === 0 ? 0 : Math.round((checked.length / total) * 100);

    document.getElementById("currentProgress").textContent = percentage + "%";
    document.getElementById(`${activeSubject}-percent`).textContent = percentage + "%";
    document.getElementById(`${activeSubject}-bar`).style.width = percentage + "%";
}

updateProgress();