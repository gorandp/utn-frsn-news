lang = "es";

const switchLanguage = () => {
    const flagArgentina = document.getElementById("switch-lang-flag-arg");
    const flagUS = document.getElementById("switch-lang-flag-us");
    const btnText = document.getElementById("switch-lang-btn-text");
    const esContent = document.getElementById("about-es");
    const enContent = document.getElementById("about-en");

    if (lang === "es") {
        // Switch to English
        // hide Spanish
        esContent.classList.add("hidden");
        flagArgentina.classList.add("hidden");
        // show English
        enContent.classList.remove("hidden");
        flagUS.classList.remove("hidden");
        // change button text
        btnText.textContent = "English (haz click para cambiar a Español)";
        // update lang variable
        lang = "en";
    } else {
        // Switch to Spanish
        // show Spanish
        esContent.classList.remove("hidden");
        flagArgentina.classList.remove("hidden");
        // hide English
        enContent.classList.add("hidden");
        flagUS.classList.add("hidden");
        btnText.textContent = "Español (click to switch to English)";
        lang = "es";
    }
}