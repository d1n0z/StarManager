import React from "react";

export function PremiumBlockOption({ svg, title, description }) {
    return (
        <li className={"premium__option"}>
            {svg}

            <aside className={"premium__option-text"}>
                <p className={"premium__option-text-first"}>{title}</p>
                <p className={"premium__option-text-second"}>{description}</p>
            </aside>
        </li>
    )
}

export function PremiumBlockOptionRight({ svg, title, description }) {
    return (
        <li className={"premium__option--right"}>
            {svg}

            <aside className={"premium__option-text--right"}>
                <p className={"premium__option-text-first--right"}>{title}</p>
                <p className={"premium__option-text-second--right"}>{description}</p>
            </aside>
        </li>
    )
}