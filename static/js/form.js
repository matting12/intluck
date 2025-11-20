
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("searchForm");

    form?.addEventListener("submit", (e) => {
        e.preventDefault();
        const data = {
            jobTitle: document.getElementById("jobTitle").value,
            companyName: document.getElementById("companyName").value,
            zipCode: document.getElementById("zipCode").value
        };
        console.log("Form submitted:", data);
    });
});
