lang = "en";

const switchLanguage = () => {
    const btn = document.getElementById("switch-lang-btn");
    const esContent = document.getElementById("about-es");
    const enContent = document.getElementById("about-en");

    if (lang === "en") {
        esContent.classList.remove("hidden");
        enContent.classList.add("hidden");
        btn.textContent = "Switch to English";
        lang = "es";
    } else {
        enContent.classList.remove("hidden");
        esContent.classList.add("hidden");
        btn.textContent = "Cambiar a Español";
        lang = "en";
    }
}