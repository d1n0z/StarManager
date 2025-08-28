export function EnterSettingButt() {
    const svg = document.querySelector(".profile__menu-members__setting-butt-svg");
    const message = document.querySelector(".profile__menu-members__setting-butt-message-first");

    if (svg) {
        svg.setAttribute("class", "profile__menu-members__setting-butt-svg--hover");
    }

    if (message) {
        message.className = "profile__menu-members__setting-butt-message-first--hover";
    }
}

export function LeaveSettingButt() {
    const svg = document.querySelector(".profile__menu-members__setting-butt-svg--hover");
    const message = document.querySelector(".profile__menu-members__setting-butt-message-first--hover");

    if (svg) {
        svg.setAttribute("class", "profile__menu-members__setting-butt-svg");
    }

    if (message) {
        message.className = "profile__menu-members__setting-butt-message-first";
    }
}


export function EnterCloseButt() {
    const svg = document.querySelector(".profile__menu-members__close-butt-svg");
    const message = document.querySelector(".profile__menu-members__close-butt-message-first");

    if (svg) {
        svg.setAttribute("class", "profile__menu-members__close-butt-svg--hover");
    }

    if (message) {
        message.className = "profile__menu-members__close-butt-message-first--hover";
    }
}

export function LeaveCloseButt() {
    const svg = document.querySelector(".profile__menu-members__close-butt-svg--hover");
    const message = document.querySelector(".profile__menu-members__close-butt-message-first--hover");

    if (svg) {
        svg.setAttribute("class", "profile__menu-members__close-butt-svg");
    }

    if (message) {
        message.className = "profile__menu-members__close-butt-message-first";
    }
}