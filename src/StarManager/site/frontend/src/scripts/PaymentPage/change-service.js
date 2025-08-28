export function ChangeServiceChat(serviceButtonID) {
    const serviceSubscribe = document.querySelector(".payment__menu-option");
    const serviceChat = document.querySelector(".payment__menu-option--chat");

    const paymentMenu = document.querySelector(".payment__menu");
    const serviceButton = document.getElementById(serviceButtonID);
    document.querySelector(".payment__menu-title__button--select")
        .className = "payment__menu-title__button";


    serviceSubscribe.style.marginLeft = "-1500px";
    serviceChat.style.marginLeft = "-40px";

    paymentMenu.style.height = "690px";

    serviceButton.className = "payment__menu-title__button--select";
}

export function ChangeServiceSub(serviceButtonID) {
    const serviceSubscribe = document.querySelector(".payment__menu-option");
    const serviceChat = document.querySelector(".payment__menu-option--chat");

    const serviceButton = document.getElementById(serviceButtonID);
    document.querySelector(".payment__menu-title__button--select")
        .className = "payment__menu-title__button";


    serviceSubscribe.style.marginLeft = "-40px";
    serviceChat.style.marginLeft = "-1500px";

    serviceButton.className = "payment__menu-title__button--select";
}