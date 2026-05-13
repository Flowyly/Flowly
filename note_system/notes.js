const checkboxes =
document.querySelectorAll(".topic-check");

checkboxes.forEach(box => {

    box.addEventListener("change", updateProgress);

});

function updateProgress() {

    const total = checkboxes.length;

    const checked =
    document.querySelectorAll(".topic-check:checked").length;

    const percentage =
    Math.round((checked / total) * 100);

    document.getElementById("currentProgress")
    .textContent = percentage + "%";

    document.getElementById("software-percent")
    .textContent = percentage + "%";

    document.getElementById("software-bar")
    .style.width = percentage + "%";
}

updateProgress();