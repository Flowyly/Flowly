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


// ===== SUBJECT + CHECKLIST DATA =====

let subjects = JSON.parse(localStorage.getItem("subjects")) || [];
let selectedSubjectIndex = null;

function saveSubjects() {
    localStorage.setItem("subjects", JSON.stringify(subjects));
}


// ===== SUBJECT FUNCTIONS =====

function renderSubjects() {
    const subjectList = document.getElementById("subjectList");
    const subjectSelect = document.getElementById("subjectSelect");

    subjectList.innerHTML = "";
    subjectSelect.innerHTML = "";

    if (subjects.length === 0) {
        subjectList.innerHTML = "<p class='empty-message'>No subject added yet.</p>";
        subjectSelect.innerHTML = "<option value=''>No subject added yet</option>";
        selectedSubjectIndex = null;
        renderTopics();
        return;
    }

    subjects.forEach((subject, index) => {
        const completed = subject.topics.filter(topic => topic.done).length;
        const total = subject.topics.length;
        const progress = total === 0 ? 0 : Math.round((completed / total) * 100);

        subject.progress = progress;

        const card = document.createElement("div");
        card.className = "subject-card";

        if (index === selectedSubjectIndex) {
            card.classList.add("active-subject");
        }

        card.innerHTML = `
            <div class="subject-top">
                <h3>${subject.name}</h3>
                <span>${progress}%</span>
            </div>

            <div class="mini-progress">
                <div class="mini-bar" style="width: ${progress}%"></div>
            </div>

            <p>${subject.description || "No description added"}</p>

            <div class="subject-actions">
                <button type="button" onclick="editSubject(event, ${index})">Edit</button>
                <button type="button" onclick="deleteSubject(event, ${index})">Delete</button>
            </div>
        `;

        card.addEventListener("click", () => {
            selectedSubjectIndex = index;
            subjectSelect.value = index;
            renderSubjects();
            renderTopics();
        });

        subjectList.appendChild(card);

        const option = document.createElement("option");
        option.value = index;
        option.textContent = subject.name;
        subjectSelect.appendChild(option);
    });

    if (selectedSubjectIndex === null && subjects.length > 0) {
        selectedSubjectIndex = 0;
    }

    subjectSelect.value = selectedSubjectIndex;
    saveSubjects();
}

function addSubject() {
    const input = document.getElementById("newSubjectInput");
    const subjectName = input.value.trim();

    if (subjectName === "") {
        alert("Please enter a subject name.");
        return;
    }

    subjects.push({
        name: subjectName,
        description: "",
        topics: [],
        notes: "",
        progress: 0
    });

    selectedSubjectIndex = subjects.length - 1;
    input.value = "";

    saveSubjects();
    renderSubjects();
    renderTopics();
}

function editSubject(event, index) {
    event.stopPropagation();

    const newName = prompt("Edit subject name:", subjects[index].name);

    if (newName && newName.trim() !== "") {
        subjects[index].name = newName.trim();
        saveSubjects();
        renderSubjects();
    }
}

function deleteSubject(event, index) {
    event.stopPropagation();

    if (confirm("Delete this subject?")) {
        subjects.splice(index, 1);

        if (subjects.length === 0) {
            selectedSubjectIndex = null;
        } else {
            selectedSubjectIndex = 0;
        }

        saveSubjects();
        renderSubjects();
        renderTopics();
    }
}

document.getElementById("subjectSelect").addEventListener("change", function () {
    if (this.value === "") {
        selectedSubjectIndex = null;
    } else {
        selectedSubjectIndex = Number(this.value);
    }

    renderSubjects();
    renderTopics();
});


// ===== TOPIC / REVISION CHECKLIST FUNCTIONS =====

function renderTopics() {
    const topicList = document.getElementById("topicList");
    const currentProgress = document.getElementById("currentProgress");

    topicList.innerHTML = "";

    if (selectedSubjectIndex === null || !subjects[selectedSubjectIndex]) {
        topicList.innerHTML = "<p class='empty-message'>Select or add a subject first.</p>";
        currentProgress.textContent = "0%";
        return;
    }

    const selectedSubject = subjects[selectedSubjectIndex];

    if (selectedSubject.topics.length === 0) {
        topicList.innerHTML = "<p class='empty-message'>No revision topic added yet.</p>";
        currentProgress.textContent = "0%";
        return;
    }

    selectedSubject.topics.forEach((topic, index) => {
        const label = document.createElement("label");
        label.className = "topic-item";

        label.innerHTML = `
            <input type="checkbox" ${topic.done ? "checked" : ""} onchange="toggleTopic(${index})">
            <span>${topic.text}</span>
            <button type="button" onclick="editTopic(event, ${index})">Edit</button>
            <button type="button" onclick="deleteTopic(event, ${index})">Delete</button>
        `;

        topicList.appendChild(label);
    });

    updateProgress();
}

function addTopic() {
    if (selectedSubjectIndex === null || !subjects[selectedSubjectIndex]) {
        alert("Please add or select a subject first.");
        return;
    }

    const input = document.getElementById("newTopicInput");
    const topicText = input.value.trim();

    if (topicText === "") {
        alert("Please enter a revision topic.");
        return;
    }

    subjects[selectedSubjectIndex].topics.push({
        text: topicText,
        done: false
    });

    input.value = "";

    saveSubjects();
    renderTopics();
    renderSubjects();
}

function toggleTopic(index) {
    subjects[selectedSubjectIndex].topics[index].done =
        !subjects[selectedSubjectIndex].topics[index].done;

    saveSubjects();
    renderTopics();
    renderSubjects();
}

function editTopic(event, index) {
    event.preventDefault();

    const currentText = subjects[selectedSubjectIndex].topics[index].text;
    const newText = prompt("Edit revision topic:", currentText);

    if (newText && newText.trim() !== "") {
        subjects[selectedSubjectIndex].topics[index].text = newText.trim();
        saveSubjects();
        renderTopics();
    }
}

function deleteTopic(event, index) {
    event.preventDefault();

    subjects[selectedSubjectIndex].topics.splice(index, 1);

    saveSubjects();
    renderTopics();
    renderSubjects();
}

function updateProgress() {
    if (selectedSubjectIndex === null || !subjects[selectedSubjectIndex]) {
        document.getElementById("currentProgress").textContent = "0%";
        return;
    }

    const topics = subjects[selectedSubjectIndex].topics;
    const completed = topics.filter(topic => topic.done).length;
    const total = topics.length;

    const percentage = total === 0 ? 0 : Math.round((completed / total) * 100);

    subjects[selectedSubjectIndex].progress = percentage;
    document.getElementById("currentProgress").textContent = percentage + "%";

    saveSubjects();
}


// ===== GENERATE NOTES =====

async function generateDummyNotes() {
    const notesArea = document.getElementById("notesArea");
    const topicInput = document.getElementById("topicInput");
    const fileInput = document.getElementById("fileUpload");

    if (selectedSubjectIndex === null || !subjects[selectedSubjectIndex]) {
        alert("Please add or select a subject first.");
        return;
    }

    if (fileInput.files.length === 0) {
        alert("Please choose a study material file first.");
        return;
    }

    const subjectName = subjects[selectedSubjectIndex].name;
    const topic = topicInput.value.trim();
    const file = fileInput.files[0];

    notesArea.value = "Reading uploaded file...";

    const reader = new FileReader();

    reader.onload = async function (event) {
        const fileContent = event.target.result;

        const promptText = `
Subject: ${subjectName}
Topic: ${topic}

Study Material:
${fileContent}

Please generate clear, structured study notes based ONLY on the uploaded study material.

Format:
1. Overview
2. Key Concepts
3. Important Details
4. Revision Checklist
5. Summary
`;

        notesArea.value = "Generating notes with AI...";

        try {
            const response = await fetch("http://127.0.0.1:5000/summarize_notes", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    notes: promptText
                })
            });

            const data = await response.json();

            if (data.success && data.summary) {
                notesArea.value = data.summary;
            } else {
                notesArea.value = data.message || "AI generation failed.";
            }

        } catch (error) {
            console.error(error);
            notesArea.value = "Error connecting to backend. Make sure Flask backend is running.";
        }
    };

    reader.onerror = function () {
        notesArea.value = "Failed to read uploaded file.";
    };

    reader.readAsText(file);
}


// ===== INITIAL LOAD =====

renderSubjects();
renderTopics();