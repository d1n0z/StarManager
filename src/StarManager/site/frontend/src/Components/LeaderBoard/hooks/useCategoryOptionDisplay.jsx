import {useEffect, useState} from "react";

export default function useCategoryOptionDisplay() {
    const [displayCategoryOption, setDisplayCategoryOption] = useState("none");

    useEffect(() => {
        const categoryInput =
            document.querySelector(".leaderboard__list-buttons__option");

        if (!categoryInput) return; // защита от ошибок, если элемент не найден

        if (displayCategoryOption === "block") {
            categoryInput.style.borderBottomLeftRadius = "0";
            categoryInput.style.borderBottomRightRadius = "0";
        } else {
            categoryInput.style.borderBottomLeftRadius = "8px";
            categoryInput.style.borderBottomRightRadius = "8px";
        }
    }, [displayCategoryOption]);

    return [displayCategoryOption, setDisplayCategoryOption];
}