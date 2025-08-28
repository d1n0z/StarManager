export function hoverButtonVK(id, color) {
    const buttonVK = document.getElementById(id);

    let borderCSS;
    let filterCSS;

    switch (color) {
        case "--red":
            borderCSS = "2px solid #FF5C5D";
            filterCSS = "drop-shadow(0px 0px 103.4px rgba(255, 92, 93, 0.23))";
            break
        case "":
            borderCSS = "2px solid #FF5C5D";
            filterCSS = "drop-shadow(0px 0px 103.4px rgba(255, 92, 93, 0.23))";
            break
        case "--white":
            borderCSS = "2px solid #FFF";
            filterCSS = "drop-shadow(0px 0px 103.4px rgba(255, 255, 255, 0.15))";
            break
        case "--green":
            borderCSS = "2px solid #4AB34E";
            filterCSS = "drop-shadow(0px 0px 103.4px rgba(74, 179, 78, 0.23))";
            break
    }

    buttonVK.style.border = borderCSS;
    buttonVK.style.filter = filterCSS;
}

export function leaveButtonVK(id) {
    const buttonVK = document.getElementById(id);

    buttonVK.style.border = "2px solid #10151B";
    buttonVK.style.filter = "none";
}