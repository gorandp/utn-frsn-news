let page = 0;

const apiSearchCall = async () => {
    const response = await fetch(
        `/api/news/latest?page=${page}`
    );
    if (!response.ok) {
        alert("Error fetching latest news. Please try again.");
        return null;
    }
    return await response.json();
}

const loadMoreResults = async () => {
    console.log("Loading more results...");
    page++;
    const res = await apiSearchCall();
    render(res);
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

const render = (data) => {
    if (!data || data.length === 0) {
        document.getElementById("load-more-btn").classList.add("hidden");
        return;
    }
    news_list = document.getElementById("news-list");
    data.forEach((item) => {
        const anchor = document.createElement("a");
        anchor.classList.add(
            "flex" ,"flex-row" ,"gap-2",
            "max-w-3xl" ,"mx-auto" ,"py-4" ,"px-4",
            "border-2" ,"border-t-transparent" ,"border-x-transparent" ,"border-b-slate-600",
            "last:border-0",
            "hover:bg-slate-800" ,"hover:border-sky-200");
        anchor.href = `/news/${item.id}`;
        anchor.style = "cursor: pointer;"

        const img = document.createElement("img");
        img.src = item.photo_url || "/static/img/news_placeholder.jpg";
        img.alt = "News Image";
        img.classList.add("w-full", "h-auto", "mb-4", "rounded-lg", "shadow-md");
        const imgDiv = document.createElement("div");
        imgDiv.classList.add("w-50", "my-auto", "flex-shrink-0");
        imgDiv.appendChild(img);
        anchor.appendChild(imgDiv);

        const infoDiv = document.createElement("div");
        const title = document.createElement("h1");
        title.classList.add("space-y-2", "text-xl", "font-semibold");
        title.textContent = item.title;
        const origDate = document.createElement("h2");
        origDate.classList.add("text-sm", "text-slate-400", "mb-2");
        origDate.textContent = formatDatetime(item.origin_created_at);
        const content = document.createElement("p");
        content.textContent = item.content;
        content.classList.add("space-y-2");
        infoDiv.appendChild(title);
        infoDiv.appendChild(origDate);
        infoDiv.appendChild(content);
        anchor.appendChild(infoDiv);

        news_list.appendChild(anchor);
    });
    if (data.length < 10) {
        document.getElementById("load-more-btn").classList.add("hidden");
        return;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadMoreResults(); // Load initial results
});
