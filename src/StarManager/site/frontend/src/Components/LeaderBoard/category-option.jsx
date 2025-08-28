export default function CategoryOption({ nameCategory, descriptorSetTextCategory, flags }) {
    let sizeBorderTopRightRadius = "0";
    let sizeBorderTopLeftRadius = "0";
    let sizeBorderBottomRightRadius = "0";
    let sizeBorderBottomLeftRadius = "0";

    switch (flags) {
        case "start":
            sizeBorderTopRightRadius = "8px";
            sizeBorderTopLeftRadius = "8px";
            break
        case "end":
            sizeBorderBottomRightRadius = "8px";
            sizeBorderBottomLeftRadius = "8px";
            break
    }

    return (
        <li className={"show-menu-category-lists-el"}
            onClick={() => {
                descriptorSetTextCategory(nameCategory);

                const menuOption
                    = document.querySelector(".show-menu-category");
                const inputOption
                    = document.getElementById("input-option");

                inputOption.style.borderBottomLeftRadius = "8px";
                inputOption.style.borderBottomRightRadius = "8px";
                menuOption.style.display = "none";
            }}>
            <button style={{
                borderTopRightRadius: sizeBorderTopRightRadius,
                borderTopLeftRadius: sizeBorderTopLeftRadius,
                borderBottomRightRadius: sizeBorderBottomRightRadius,
                borderBottomLeftRadius: sizeBorderBottomLeftRadius,
            }}>{nameCategory}</button>
        </li>
    )
}