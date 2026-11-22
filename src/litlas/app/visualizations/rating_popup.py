"""Anchored book-list popups for the Litlas statistics charts."""

import streamlit as st


RATING_POPUP_JS = """
export default function(component) {
    const books = component.data.books;
    const isYear = component.data.mode === "year";
    const isCountry = component.data.mode === "country";
    const chartKey = component.data.chart_key;
    const canEdit = Boolean(component.data.can_edit) && !isYear && !isCountry;
    let chart = null;
    let popup = null;

    function closePopup() {
        if (popup) {
            popup.remove();
            popup = null;
        }
    }

    // Match the existing Litlas half-star selection behavior.
    function ratingFromPointer(event, element) {
        const rect = element.getBoundingClientRect();
        const fraction = Math.max(0, Math.min(1,
            (event.clientX - rect.left) / rect.width));
        return Math.max(0.5, Math.min(5, Math.ceil(fraction * 10) / 2));
    }

    function showPopup(event) {
        const point = event.points?.[0];
        if (!point) return;

        const rating = Number(point.x);
        const key = (isYear || isCountry)
            ? String(point.customdata)
            : String(rating);
        const entries = books[key] || [];

        closePopup();
        popup = document.createElement("div");
        popup.className = "litlas-anchored-rating-popup";

        Object.assign(popup.style, {
            position: "fixed", zIndex: "99999", width: "420px",
            maxWidth: "calc(100vw - 24px)", boxSizing: "border-box",
            padding: "20px 22px", border: "1px solid #E8DED0",
            borderRadius: "15px", background: "#FAF7F1",
            boxShadow: "0 8px 22px rgba(60,40,28,0.18)",
            fontFamily: "Georgia, serif", color: "#58412F"
        });

        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex", justifyContent: "space-between",
            alignItems: "center", gap: "12px"
        });

        const title = document.createElement("strong");
        title.textContent = isCountry
            ? "Books From This Country"
            : isYear ? "Books From My Reading Year" : "Books From My Rating";
        title.style.fontSize = "20px";

        const close = document.createElement("button");
        close.textContent = "×";
        close.setAttribute("aria-label", "Close rating books");
        Object.assign(close.style, {
            border: "none", background: "transparent", color: "#58412F",
            cursor: "pointer", fontSize: "23px", padding: "0 4px"
        });
        close.onclick = closePopup;
        header.append(title, close);

        const caption = document.createElement("div");
        caption.textContent = isCountry
            ? `${component.data.country_names[key] || key} · ${entries.length} books`
            : isYear ? `${key} · ${entries.length} books completed`
            : `${rating} ★ · ${entries.length} books`;
        Object.assign(caption.style, {
            margin: "14px 0 10px", color: "#96785D", fontSize: "13px"
        });

        const list = document.createElement("div");
        Object.assign(list.style, {
            background: "#F5EFE4", border: "1px solid #D4C1A7",
            borderRadius: "7px", padding: "5px 12px",
            maxHeight: "250px", overflowY: "auto"
        });

        for (const book of entries) {
            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "flex", alignItems: "baseline",
                justifyContent: "space-between", gap: "10px",
                padding: "5px 2px", borderBottom: "1px solid #E2D5C3",
                fontSize: "13px", lineHeight: "1.3"
            });

            const description = document.createElement("span");
            description.style.flex = "1";
            description.style.minWidth = "0";
            const bookTitle = document.createElement("i");
            bookTitle.textContent = book.title;
            const author = document.createElement("span");
            author.textContent = ` · ${book.author}`;
            author.style.color = "#81776E";
            description.append(bookTitle, author);

            const ratingArea = document.createElement("span");
            Object.assign(ratingArea.style, {
                whiteSpace: "nowrap", flexShrink: "0", display: "inline-flex",
                alignItems: "center", gap: "5px"
            });

            // This markup comes from Litlas's shared Python rating formatter.
            const ratingStars = document.createElement("span");
            ratingStars.innerHTML = book.stars_html;
            ratingArea.appendChild(ratingStars);

            if (canEdit && book.book_id != null) {
                const starElement = ratingStars.querySelector(".star-rating");
                if (starElement) {
                    starElement.style.cursor = "pointer";
                    starElement.style.touchAction = "none";
                    starElement.style.userSelect = "none";
                    const originalFill = starElement.style.getPropertyValue("--rating-fill");
                    let pending = null;

                    const done = document.createElement("button");
                    done.type = "button";
                    done.textContent = "Done";
                    done.hidden = true;
                    Object.assign(done.style, {
                        border: "1px solid #B29A7C", borderRadius: "5px",
                        padding: "3px 6px", background: "#FAF7F1",
                        color: "#58412F", font: "12px Georgia, serif",
                        cursor: "pointer", touchAction: "manipulation"
                    });

                    function setPreview(value) {
                        starElement.style.setProperty("--rating-fill", `${value / 5 * 100}%`);
                    }
                    starElement.addEventListener("pointermove", (e) => {
                        if (e.pointerType === "mouse" && pending === null) {
                            setPreview(ratingFromPointer(e, starElement));
                        }
                    });
                    starElement.addEventListener("pointerleave", () => {
                        if (pending === null) {
                            starElement.style.setProperty("--rating-fill", originalFill);
                        }
                    });
                    starElement.addEventListener("pointerup", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        pending = ratingFromPointer(e, starElement);
                        setPreview(pending);
                        done.hidden = false;
                    });
                    starElement.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                    });
                    done.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        if (pending === null) return;
                        done.disabled = true;
                        done.textContent = "Saving…";
                        component.setTriggerValue("rating", {
                            book_id: String(book.book_id), rating: pending
                        });
                    });
                    ratingArea.appendChild(done);
                }
            }
            row.append(description, ratingArea);
            list.appendChild(row);
        }

        popup.append(header, caption, list);
        document.body.appendChild(popup);

        const width = popup.getBoundingClientRect().width;
        const height = popup.getBoundingClientRect().height;
        const rect = chart.getBoundingClientRect();
        const clickX = event.event?.clientX ?? rect.left + rect.width / 2;
        const clickY = event.event?.clientY ?? rect.top + rect.height / 2;
        const preferredLeft = (isYear || isCountry)
            ? clickX + 16 : clickX - width - 16;
        const left = Math.max(12, Math.min(preferredLeft, window.innerWidth - width - 12));
        const top = Math.max(12, Math.min(clickY - height / 2, window.innerHeight - height - 12));
        popup.style.left = `${left}px`;
        popup.style.top = `${top}px`;
    }

    function onOutsideClick(event) {
        if (popup && !popup.contains(event.target) &&
            !event.target.closest(`.st-key-${chartKey}`)) {
            closePopup();
        }
    }
    function onEscape(event) {
        if (event.key === "Escape") closePopup();
    }
    function attach() {
        const found = document.querySelector(`.st-key-${chartKey} .js-plotly-plot`);
        if (!found || found === chart || typeof found.on !== "function") return;
        if (chart && typeof chart.removeListener === "function") {
            chart.removeListener("plotly_click", showPopup);
        }
        chart = found;
        chart.on("plotly_click", showPopup);
    }

    attach();
    const observer = new MutationObserver(attach);
    observer.observe(document.body, {childList: true, subtree: true});
    document.addEventListener("pointerdown", onOutsideClick);
    document.addEventListener("keydown", onEscape);
    return () => {
        observer.disconnect();
        document.removeEventListener("pointerdown", onOutsideClick);
        document.removeEventListener("keydown", onEscape);
        if (chart && typeof chart.removeListener === "function") {
            chart.removeListener("plotly_click", showPopup);
        }
        closePopup();
    };
}
"""

rating_popup_component = st.components.v2.component(
    "litlas_rating_popup",
    js=RATING_POPUP_JS,
)


def render_rating_popup(books, mode="rating", country_names=None, *, can_edit=False):
    chart_key = {
        "rating": "litlas_ratings",
        "year": "litlas_reading_history",
        "country": "litlas_country_density",
    }[mode]

    return rating_popup_component(
        key=f"litlas_anchored_{mode}_popup",
        data={
            "books": books,
            "mode": mode,
            "chart_key": chart_key,
            "country_names": country_names or {},
            "can_edit": bool(can_edit),
        },
        on_rating_change=lambda: None,
        height=0,
    )
