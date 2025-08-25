export function hoverBuyPremium() {
    const blueBuyPremiumButton = document.querySelector(".premium__buy-premium--blue");
    const buyPremiumButton = document.querySelector(".premium__buy-premium");

    blueBuyPremiumButton.style.opacity = "1";
    buyPremiumButton.style.opacity = "0";
}

export function leaveBuyPremium() {
    const blueBuyPremiumButton = document.querySelector(".premium__buy-premium--blue");
    const buyPremiumButton = document.querySelector(".premium__buy-premium");

    blueBuyPremiumButton.style.opacity = "0";
    buyPremiumButton.style.opacity = "1";
}