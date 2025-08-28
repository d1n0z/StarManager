import {useEffect, useState} from "react";

export default function useNavigateButton(dataListUsers) {
    const [offsetsPageStart, setOffsetsPageStart] = useState(0);
    const [offsetsPageEnd, setOffsetsPageEnd] = useState(25);

    useEffect(() => {
        if (dataListUsers.length < offsetsPageEnd) {
            const buttonFooter = document
                .querySelector(".leaderboard__list-footerButton")
                .querySelectorAll("button");
            const buttonNext = buttonFooter[1];
            const buttonPred = buttonFooter[0];

            buttonNext.className = "footerButton--disable"
            buttonPred.className = "footerButton"
        } else if (dataListUsers.length > offsetsPageStart) {
            const buttonFooter = document
                .querySelector(".leaderboard__list-footerButton")
                .querySelectorAll("button");
            const buttonNext = buttonFooter[1];
            const buttonPred = buttonFooter[0];

            buttonPred.className = "footerButton--disable"
            buttonNext.className = "footerButton"
        }
    }, [offsetsPageStart])

    return [offsetsPageStart, offsetsPageEnd, setOffsetsPageStart, setOffsetsPageEnd];
}