let searchQueryString = "";
let searchPage = 1;


const apiSearchCall = async () => {
    const endpoint = "/api/search?" + searchQueryString + `&page=${searchPage}`;
    try {
        const response = await fetch(endpoint);
        if (response.status === 404) {
            // alert("No se encontraron nuevos resultados para la búsqueda.");
            return [];
        }
        if (!response.ok) {
            searchPage--; // Revert page increment if the call fails
            alert("Error fetching search results. Please try again.");
            return null
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching data:", error);
        return null;
    }
}

const query = (text, o_date_from, o_date_to, i_date_from, i_date_to) => {
    const params = new URLSearchParams();
    if (text) params.append("text", text);
    if (o_date_from) params.append("origin_date_from", o_date_from);
    if (o_date_to) params.append("origin_date_to", o_date_to);
    if (i_date_from) params.append("inserted_date_from", i_date_from);
    if (i_date_to) params.append("inserted_date_to", i_date_to);
    searchQueryString = params.toString();
    searchPage = 1;
    return params.toString();
}

const resetForm = () => {
    document.getElementById("search-form").reset();
    searchQueryString = "";
    searchPage = 1;
    document.getElementById("search-results").classList.add("hidden");
}

const formatDatetime = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.getFullYear()
        + "-" + String(date.getMonth() + 1).padStart(2, '0')
        + "-" + String(date.getDate()).padStart(2, '0')
        + " " + String(date.getHours()).padStart(2, '0')
        + ":" + String(date.getMinutes()).padStart(2, '0')
        + ":" + String(date.getSeconds()).padStart(2, '0');
}

const search = async (e) => {
    e.preventDefault();
    console.log("Searching...");
    console.log(e.target)
    const form = e.target;
    const formData = new FormData(form);
    if (!formData.get("text") &&
        !formData.get("origin_date_from") && !formData.get("origin_date_to") &&
        !formData.get("inserted_date_from") && !formData.get("inserted_date_to")
    ) {
        alert("Por favor ingrese al menos un filtro para buscar.");
        return;
    }
    query(
        formData.get("text"),
        formData.get("origin_date_from"),
        formData.get("origin_date_to"),
        formData.get("inserted_date_from"),
        formData.get("inserted_date_to")
    );
    // console.log("Query String:", searchQueryString);
    const res = await apiSearchCall();
    // console.log(res);
    renderSearchResults(res);
}

const loadMoreResults = async (e) => {
    console.log("Loading more results...");
    // Implement pagination logic here if needed
    searchPage++;
    const res = await apiSearchCall();
    renderRows(res);
}

const renderSearchResults = (results) => {
    const resultsContainer = document.getElementById("search-results");
    resultsContainer.classList.remove("hidden");
    const resultsTableBody = document
        .getElementById("search-results-table")
        .getElementsByTagName("tbody")[0];
    resultsTableBody.innerHTML = "";

    if (!results || results.length === 0) {
        document.getElementById("search-results-table")
            .classList.add("hidden");
        document.getElementById("search-results-empty")
            .classList.remove("hidden");
        return;
    } else {
        document.getElementById("search-results-table")
            .classList.remove("hidden");
        document.getElementById("search-results-empty")
            .classList.add("hidden");
    }

    renderRows(results);
}

const renderRows = (results) => {
    const resultsTableBody = document
        .getElementById("search-results-table")
        .getElementsByTagName("tbody")[0];

    results.forEach(result => {
        const row = resultsTableBody.insertRow();
        const titleCell = row.insertCell(0);
        const origDateCell = row.insertCell(1);
        const insDateCell = row.insertCell(2);

        const titleLink = document.createElement("a");
        titleLink.href = "/news/" + result.id;
        titleLink.target = "_blank";
        titleLink.textContent = result.title;
        titleLink.classList.add("text-blue-500", "hover:underline");

        titleCell.appendChild(titleLink);
        origDateCell.textContent = formatDatetime(result.origin_created_at);
        insDateCell.textContent = formatDatetime(result.inserted_at);
        // insDateCell.textContent = result.inserted_at ? new Date(result.inserted_at).toString() : "N/A";

        titleCell.classList.add("p-2", "border-b", "border-slate-600", "hover:underline");
        origDateCell.classList.add("p-2", "border-b", "border-slate-600");
        insDateCell.classList.add("p-2", "border-b", "border-slate-600");
    });

    if (!results || results.length < 50) {
        document.getElementById("search-load-more-btn").classList.add("hidden");
    } else {
        document.getElementById("search-load-more-btn").classList.remove("hidden");
    }
}
