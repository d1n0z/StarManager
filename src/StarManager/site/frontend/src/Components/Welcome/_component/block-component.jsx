// react
import React from "react";

// js
import { hoverButtonVK, leaveButtonVK } from "../../../scripts/WelcomePage/hover-vkbutton";

export function BlockVKStyle({
                          title,
                          description,
                          textButton,
                          svg,
                          svgMini,
                          onClickEvent,
                          idVKButton,
                          color=""
                      }) {
    if (color === "red" || color === "") color = ""; else color = `--${color}`;

    return (
        <>
            <aside className={"advantages__block-fill"}>
                { svgMini }

                <p className={"advantages__block-title"}>
                    { title }
                </p>
                <p className={"advantages__block-description"}>
                    { description }
                </p>
                <button
                    onMouseEnter={ () => hoverButtonVK(idVKButton, color) }
                    onMouseLeave={ () => leaveButtonVK(idVKButton) }
                    onClick={onClickEvent} className={`advantages__block-button${color}`}>
                    { textButton }
                </button>
            </aside>

            <aside>
                { svg }
            </aside>
        </>
    )
}