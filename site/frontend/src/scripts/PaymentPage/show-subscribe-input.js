export function ShowButtonGiftSubscribe() {
    const menu = document.querySelector(".payment__menu");

    const inputGift = document.getElementById("input-gift");
    const inputGiftDisplay = inputGift.style.display;

    const buttonGiftSubscribe = document.querySelector(".payment__menu-option__input-gift");

    if (inputGift) {
        if (!inputGiftDisplay || inputGiftDisplay === "none") {
            inputGift.style.display = "block";
            setTimeout(() => {
                inputGift.style.opacity = "1";

                buttonGiftSubscribe.style.marginTop = "100px";
                buttonGiftSubscribe.innerHTML = "Купить подписку себе";

                const currentHeight = parseFloat(getComputedStyle(menu).height);
                menu.style.height = `${currentHeight + 130}px`;
            }, 5);
        } else {
            inputGift.style.opacity = "0";
            setTimeout(() => {
                inputGift.style.display = "none";

                buttonGiftSubscribe.style.marginTop = "-16px";
                buttonGiftSubscribe.innerHTML = "Подарить подписку";

                const currentHeight = parseFloat(getComputedStyle(menu).height);
                menu.style.height = `${currentHeight - 130}px`;
            }, 5);
        }
    }
}

export function ShowButtonGiftSubscribeMobile() {
    const menu = document.querySelector(".payment__menu");

    const inputGift = document.getElementById("input-gift");
    const inputGiftDisplay = inputGift.style.display;

    const buttonGiftSubscribe = document.querySelector(".payment__menu-option__input-gift--mobile");

    if (inputGift) {
        if (!inputGiftDisplay || inputGiftDisplay === "none") {
            inputGift.style.display = "block";
            setTimeout(() => {
                inputGift.style.opacity = "1";

                buttonGiftSubscribe.innerHTML = "Купить подписку себе";
            }, 5);

            const currentHeight = parseFloat(getComputedStyle(menu).height);
            menu.style.height = `${currentHeight + 190}px`;
        } else {
            inputGift.style.opacity = "0";
            setTimeout(() => {
                inputGift.style.display = "none";

                buttonGiftSubscribe.innerHTML = "Подарить подписку";
            }, 5);

            const currentHeight = parseFloat(getComputedStyle(menu).height);
            menu.style.height = `${currentHeight - 190}px`;
        }
    }
}