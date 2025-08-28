export default function CategoryOption({ nameCategory, descriptorsetTextCategory, flags, descriptorSetDisplayCategoryOption }) {
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
                descriptorsetTextCategory(nameCategory)
                descriptorSetDisplayCategoryOption("none")
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