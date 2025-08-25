import profileImg from "../../image/profileImgTestHighQ.jpg";

export function MemberCase({ nick, root, premium }) {
    let rootText = "";
    let prefixClass = ""

    switch (root) {
        case 0:
            rootText = "Пользователь";
            break
        case 1:
            rootText = "Смотрящий";
            prefixClass = "--beholder"
            break
        case 2:
            rootText = "Модератор";
            prefixClass = "--moderator"
            break
        case 3:
            rootText = "Старший модератор";
            prefixClass = "--senior-moderator"
            break
        case 4:
            rootText = "Администратор";
            prefixClass = "--administrator"
            break
        case 5:
            rootText = "Спец. администратор";
            prefixClass = "--special-administrator"
            break
        case 6:
            rootText = "Руководитель";
            prefixClass = "--director"
            break
        case 7:
            rootText = "Владелец";
            prefixClass = "--owner"
            break
        case 8:
            rootText = "Dev";
            prefixClass = "--dev"
            break
    }

    if (premium) prefixClass = "--premium";

    return (
        <li className={`profile__menu-members__lists-member${prefixClass}`}>
            <img className={"profile__menu-members__lists-member-avatar"} src={profileImg}/>

            <aside className={"profile__menu-members__lists-member-text"}>
                <p className={"profile__menu-members__lists-member-text-name"}>{nick}</p>
                <p className={"profile__menu-members__lists-member-text-root"}>{rootText}</p>
            </aside>

            <svg className={"profile__menu-members__lists-member-more"}
                 viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                    d="M16.0002 21.333C16.5276 21.333 17.0432 21.4894 17.4817 21.7824C17.9202 22.0754 18.262 22.4919 18.4638 22.9792C18.6657 23.4665 18.7185 24.0026 18.6156 24.5199C18.5127 25.0372 18.2587 25.5124 17.8858 25.8853C17.5128 26.2582 17.0377 26.5122 16.5204 26.6151C16.0031 26.718 15.4669 26.6652 14.9797 26.4634C14.4924 26.2615 14.0759 25.9197 13.7829 25.4812C13.4899 25.0427 13.3335 24.5271 13.3335 23.9997C13.3335 23.2924 13.6144 22.6142 14.1145 22.1141C14.6146 21.614 15.2929 21.333 16.0002 21.333ZM13.3335 7.99967C13.3335 8.52709 13.4899 9.04266 13.7829 9.48119C14.0759 9.91973 14.4924 10.2615 14.9797 10.4634C15.4669 10.6652 16.0031 10.718 16.5204 10.6151C17.0377 10.5122 17.5128 10.2582 17.8858 9.88529C18.2587 9.51235 18.5127 9.0372 18.6156 8.51992C18.7185 8.00263 18.6657 7.46645 18.4638 6.97919C18.262 6.49192 17.9202 6.07544 17.4817 5.78242C17.0432 5.48941 16.5276 5.33301 16.0002 5.33301C15.2929 5.33301 14.6146 5.61396 14.1145 6.11406C13.6144 6.61415 13.3335 7.29243 13.3335 7.99967ZM13.3335 15.9997C13.3335 16.5271 13.4899 17.0427 13.7829 17.4812C14.0759 17.9197 14.4924 18.2615 14.9797 18.4634C15.4669 18.6652 16.0031 18.718 16.5204 18.6151C17.0377 18.5122 17.5128 18.2582 17.8858 17.8853C18.2587 17.5124 18.5127 17.0372 18.6156 16.5199C18.7185 16.0026 18.6657 15.4665 18.4638 14.9792C18.262 14.4919 17.9202 14.0754 17.4817 13.7824C17.0432 13.4894 16.5276 13.333 16.0002 13.333C15.2929 13.333 14.6146 13.614 14.1145 14.1141C13.6144 14.6142 13.3335 15.2924 13.3335 15.9997Z"/>
            </svg>
        </li>
    )
}