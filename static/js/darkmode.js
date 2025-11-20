
document.addEventListener("DOMContentLoaded", () => {
    const html = document.documentElement;
    const toggle = document.getElementById("darkModeToggle");

    if (localStorage.getItem("theme") === "dark") {
        html.classList.add("dark");
    }

    toggle?.addEventListener("click", () => {
        html.classList.toggle("dark");
        localStorage.setItem("theme", html.classList.contains("dark") ? "dark" : "light");
    });
});
