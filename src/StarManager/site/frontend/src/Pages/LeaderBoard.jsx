// React
import { useEffect, useState } from "react";

// component
import { MiniProfileLegacy } from "../Components/mini-profile-legacy";
import UserSection from "../Components/LeaderBoard/user-section";
import CategoryOption from "../Components/LeaderBoard/category-option";

// css
import "../styles/leaderboard.css";

const PAGE_SIZE = 10;

const DICT_CATEGORY_NAME = {
    "Топ по монетам":       "topcoins",
    "Топ по сообщениям":    "topmessages",
    "Топ по дуэлям":        "topduels",
    "Топ по лиге":          "topleagues",
    "Топ по репутации":     "toprep",
    "Топ по примерам":      "topmath",
    "Топ по бонусам":       "topbonus",
}

const TEST_RESPONSE = [
    {
        "place": 1,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "Бронза | 71 уровень"
    },
    {
        "place": 2,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "Платина | 71 уровень"
    },
    {
        "place": 3,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 4,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 5,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 6,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 7,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 8,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 9,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 10,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 11,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 12,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 13,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 14,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 15,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 16,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 17,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 18,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 19,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 20,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 21,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 22,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 23,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 24,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 25,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 26,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 27,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 28,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    },
    {
        "place": 29,
        "avatar": "https://sun9-26.userapi.com/s/v1/ig2/DF3XLjl9SXZdgPdkdXF0xPa51OqDM5SaEDo9LDZNSB-0JVkzHhebu_f7iUXDisANqpe8B9-XM54JGgQpTnmCIM-d.jpg?quality=95&as=32x33,48x50,72x75,108x113,160x167,240x251,360x377,480x502,540x565,640x670,720x753,735x769&from=bu&cs=735x0",
        "username": "user name",
        "value": "12345"
    }
]

function LeaderBoard() {
    const [textCategory, setTextCategory] = useState("Топ по монетам");
    const [page, setPage] = useState(0);
    const [data, setData] = useState({ total: 0, items: [] });
    const [displayCategoryOption, setDisplayCategoryOption] = useState("none");

    useEffect(() => {
        const categoryKey = DICT_CATEGORY_NAME[textCategory];
        const offset = page * PAGE_SIZE;

        fetch(`/api/leaderboard/${categoryKey}?offset=${offset}&limit=${PAGE_SIZE}`)
            .then(res => res.json())
            .then(json => setData(json))
            .catch(console.error);
    }, [textCategory, page]);

    useEffect(() => {
        const categoryInput = document.querySelector(".leaderboard__list-buttons__option");
        if (categoryInput) {
            categoryInput.style.borderBottomLeftRadius = displayCategoryOption === "block" ? "0" : "8px";
            categoryInput.style.borderBottomRightRadius = displayCategoryOption === "block" ? "0" : "8px";
        }
    }, [displayCategoryOption]);

    const maxPage = Math.ceil(data.total / PAGE_SIZE) - 1;

    return (
        <div className="leaderboard">
            <header>
                <MiniProfileLegacy />
            </header>
            <main>
                <aside className="leaderboard__title">
                    <h1 className="leaderboard__title__first">
                        ПОЛЬЗОВАТЕЛЬСКИЙ
                        <span className="leaderboard__title__second"> ТОП</span>
                    </h1>
                    <p className="leaderboard__title__description">
                        <span className="leaderboard__title__description--main">Пользовательский ТОП </span>
                        — это особый рейтинг, отражающий активность и вклад участников. Попадая в ТОП, вы получаете
                        признание в сообществе, а ваш профиль выделяется среди других. Это не только показатель вашей
                        вовлечённости, но и способ подчеркнуть свой статус.
                    </p>
                </aside>

                <aside className="leaderboard__list">
                    <nav className="leaderboard__list-buttons">
                        <ul className="leaderboard__list-buttons-lists">
                            <li className="leaderboard__list-buttons__button">
                                <input
                                    placeholder="Введите имя пользователя..."
                                    className="leaderboard__list-buttons__input"
                                />
                            </li>

                            <li
                                className="leaderboard__list-buttons__button"
                                onMouseEnter={() => setDisplayCategoryOption("block")}
                                onMouseLeave={() => setDisplayCategoryOption("none")}
                            >
                                <div className="leaderboard__list-buttons__option-div">
                                    <input
                                        className="leaderboard__list-buttons__option"
                                        disabled
                                        value={textCategory}
                                    />

                                    <svg
                                        className="leaderboard__list-buttons__option-svg"
                                        viewBox="0 0 14 8"
                                        fill="none"
                                        xmlns="http://www.w3.org/2000/svg"
                                    >
                                        <path
                                            d="M6.48699 7.03713C6.81109 7.36123 7.33656 7.36123 7.66066 7.03713L12.9422 1.75563C13.2663 1.43153 13.2663 0.906059 12.9422 0.58196C12.6181 0.25786 12.0926 0.25786 11.7685 0.58196L7.07382 5.27663L2.37915 0.58196C2.05506 0.25786 1.52959 0.25786 1.20549 0.58196C0.881389 0.906059 0.881389 1.43153 1.20549 1.75563L6.48699 7.03713ZM7.07382 5.34375H6.24391V6.45029H7.07382H7.90373V5.34375H7.07382Z"
                                            fill="white"
                                        />
                                    </svg>
                                </div>

                                <nav className="show-menu-category" style={{ display: displayCategoryOption }}>
                                    <ul className="show-menu-category-lists">
                                        {Object.keys(DICT_CATEGORY_NAME).map((name, i, arr) => (
                                            <CategoryOption
                                                key={name}
                                                nameCategory={name}
                                                descriptorsetTextCategory={() => {
                                                    setTextCategory(name);
                                                    setPage(0);
                                                }}
                                                descriptorSetDisplayCategoryOption={setDisplayCategoryOption}
                                                flags={i === arr.length - 1 ? "end" : undefined}
                                            />
                                        ))}
                                    </ul>
                                </nav>
                            </li>
                        </ul>
                    </nav>

                    <nav className="leaderboard__list-users">
                        <ul className="leaderboard__list-users-lists">
                            <li className="leaderboard__list-users__user-header">
                                <nav className="leaderboard__list-users__user-header-names">
                                    <ul className="leaderboard__list-users__user-header-names-lists">
                                        <li className="lists-tag" id="Place">
                                            <p>Место</p>
                                        </li>
                                        <li className="lists-tag" id="Name">
                                            <p>Имя<span id="HiddenName">/Username</span></p>
                                        </li>
                                        <li className="lists-tag" id="Username">
                                            <p>VK</p>
                                        </li>
                                        <li className="lists-tag" id="Count">
                                            <p>Количество</p>
                                        </li>
                                    </ul>
                                </nav>
                            </li>

                            {data.items.map(user => (
                                <UserSection
                                    key={user.place}
                                    number={user.place}
                                    avatar={user.avatar}
                                    name={user.username}
                                    username={user.username}
                                    count={user.value}
                                />
                            ))}
                        </ul>
                    </nav>

                    <article className="leaderboard__list-footerButton">
                        <button
                            className={`footerButton ${page === 0 ? "footerButton--disable" : ""}`}
                            onClick={() => setPage(p => Math.max(p - 1, 0))}
                            disabled={page === 0}
                        >
                            Смотреть предыдущие
                        </button>
                        <button
                            className={`footerButton ${page >= maxPage ? "footerButton--disable" : ""}`}
                            onClick={() => setPage(p => Math.min(p + 1, maxPage))}
                            disabled={page >= maxPage}
                        >
                            Смотреть далее
                        </button>
                    </article>
                </aside>
            </main>
        </div>
    );
}

export default LeaderBoard;