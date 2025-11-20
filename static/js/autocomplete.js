
document.addEventListener("DOMContentLoaded", () => {
    const jobTitleInput = document.getElementById("jobTitle");
    const dropdown = document.getElementById("jobTitleDropdown");

    const search = debounce(async (query) => {
        if (query.length < 2) { dropdown.classList.add("hidden"); return; }

        const response = await fetch(`/api/autocomplete/job-title?q=${encodeURIComponent(query)}`);
        const results = await response.json();

        if (!results.length) { dropdown.classList.add("hidden"); return; }

        dropdown.innerHTML = results.map(title => `
            <div class="px-4 py-2 hover:bg-gray-100 cursor-pointer">${title}</div>
        `).join("");

        dropdown.classList.remove("hidden");

        dropdown.querySelectorAll("div").forEach(item => {
            item.addEventListener("click", () => {
                jobTitleInput.value = item.textContent.trim();
                dropdown.classList.add("hidden");
            });
        });
    }, 300);

    jobTitleInput?.addEventListener("input", e => search(e.target.value));

    document.addEventListener("click", e => {
        if (!dropdown.contains(e.target) && !jobTitleInput.contains(e.target)) {
            dropdown.classList.add("hidden");
        }
    });
});
