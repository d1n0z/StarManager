export function ButtonMenuSubscribe({
                                 title="test title",

                                 top=0,

                                 borderRadiusDown=0,
                                 borderRadiusTop=0,
                             }) {
    function FillSubscribeInformation() {
        document.getElementById("days-premium").value = title;
        ShowMenuSubscribe();
    }

    return (
        <li
            className={"payment__menu-option__input-menu-button"}>
            <input style={{
                borderTop: `${top}px solid #5491D8`,

                borderBottomRightRadius: borderRadiusDown,
                borderBottomLeftRadius: borderRadiusDown,
                borderTopRightRadius: borderRadiusTop,
                borderTopLeftRadius: borderRadiusTop,
            }}
                   disabled placeholder={title}/>
            <button onClick={() => FillSubscribeInformation()}>Выбрать</button>
        </li>
    )
}

export function ShowMenuSubscribe() {
    const menuSubscribe = document.querySelector(".payment__menu-option__input-menu");
    const showType = menuSubscribe.style.opacity;

    const informationBlock = document.querySelector(".payment__menu-option__input")
        .querySelector("fieldset");

    const buttonGiftSubscribe = document.querySelector(".payment__menu-option__input-gift");

    if (menuSubscribe && informationBlock) {
        if (showType === "0" || !showType) {
            // показываем меню
            menuSubscribe.style.display = "block";
            setTimeout(() => {
                menuSubscribe.style.opacity = 1;

                // изменяем вид блока с информацией о подписке
                informationBlock.style.borderBottomRightRadius = "0";
                informationBlock.style.borderBottomLeftRadius = "0";
                informationBlock.style.borderBottom = "none";

                // перемещаем кнопку "подарить подписку"
                if (buttonGiftSubscribe.innerHTML !== "Купить подписку себе") {
                    buttonGiftSubscribe.style.marginTop = "-83px";
                }
            }, 5);
        }
        else {
            // скрываем меню
            menuSubscribe.style.opacity = 0;

            // изменяем вид блока с информацией о подписке
            informationBlock.style.borderBottomRightRadius = "16px";
            informationBlock.style.borderBottomLeftRadius = "16px";
            informationBlock.style.borderBottom = "1px solid #5491D8";

            // возвращаем кнопку "подарить подписку"
            if (buttonGiftSubscribe.innerHTML !== "Купить подписку себе") {
                buttonGiftSubscribe.style.marginTop = "-16px";
            }

            setTimeout(() => menuSubscribe.style.display = "none", 450);
        }
    }
}