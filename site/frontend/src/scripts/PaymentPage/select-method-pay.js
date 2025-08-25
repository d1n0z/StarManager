export function CheckMethodPay(idMethod) {
    const methodPay = document.getElementById(idMethod);
    const activeMethodPay = document
        .querySelectorAll(".payment__menu-pay__method-checkbox-fill");

    activeMethodPay.forEach((element, index) => {
        element.style.fill = "transparent";
    })

    if (methodPay) methodPay.style.fill = "#5491D8";
}