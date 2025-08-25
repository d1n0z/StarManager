import errorProfileAvatar from "../../image/errorProfileImg.png";

export default function UserSection({ number, avatar, name, username, count }) {
    let modificator = "";

    if (avatar === "non-local url") {
        avatar = errorProfileAvatar;
    }

    switch (number) {
        case 1:
            modificator = "--first";
            break
        case 2:
            modificator = "--second";
            break
        case 3:
            modificator = "--third";
            break
    }

    return (
        <li className={`leaderboard__list-users__user${modificator}`}>
            <article className={"leaderboard__list-users__user-top"}>
                <p className={"top-number"}>{number}</p>
            </article>

            <article className={"leaderboard__list-users__user-info"}>
                <img
                    className={"info-avatar"}
                    src={avatar}
                />
                <p className={"info-name"}>{name}</p>
            </article>

            <article className={"leaderboard__list-users__user-username"}>
                <p className={"info-username"}>
                    <a href={`https://vk.com/${username}`}>@{username}</a>
                </p>
            </article>

            <article className={"leaderboard__list-users__user-count"}>
                <p className={"info-count"}>{count}</p>
            </article>
        </li>
    )
}