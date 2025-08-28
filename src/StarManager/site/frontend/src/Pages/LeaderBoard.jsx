// React
import {useEffect, useRef, useState} from "react";

// component
import { MiniProfileLegacy } from "../Components/mini-profile-legacy";
import UserSection from "../Components/LeaderBoard/user-section";
import CategoryOption from "../Components/LeaderBoard/category-option";

// css
import "../styles/leaderboard.css";

const PAGE_SIZE = 25;

const DICT_CATEGORY_NAME = {
    "Топ по монетам":       "topcoins",
    "Топ по сообщениям":    "topmessages",
    "Топ по дуэлям":        "topduels",
    "Топ по лиге":          "topleagues",
    "Топ по репутации":     "toprep",
    "Топ по примерам":      "topmath",
    "Топ по бонусам":       "topbonus",
}

const TEST_RESPONSE = {
    "total": 145939,
    "items": [
        {
            "place": 1,
            "avatar": "https://sun1-89.userapi.com/s/v1/ig2/N_9GZV99ir_-ajNHB4mfZU0-7tmpPTGcLq3IDY8HZ-WWZNMjKTCDVpYqgmBITYP0PuR0xUIzXdiucvss6NX_dtO-.jpg?quality=95&crop=0,266,1049,1049&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "tsobaev_l",
            "username": "Loma Federal",
            "value": "Платина | 80 уровень"
        },
        {
            "place": 2,
            "avatar": "https://sun1-28.userapi.com/s/v1/ig2/SEMFG9E7f-cKakFIgSAyztdZFnFmcFhVVEDVSLH7kiR1fwyb7lXGVjN9YhzQ_7PywxwWuFsv2vud5L1B7HTvDRIp.jpg?quality=95&crop=0,172,736,736&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "maga_travmatolog",
            "username": "Мага Актимиров",
            "value": "25665"
        },
        {
            "place": 3,
            "avatar": "https://sun1-17.userapi.com/s/v1/ig2/jOYO5UTNT6tusJOITQHdtiGlQD5BW59UW8wkW38UAgYf6HmhhP1CoqUyjk0yMg6EfhwOuTbgEhVInB6Vl01PmRz7.jpg?quality=96&crop=98,98,787,787&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "nekki_legend",
            "username": "Артур Пирожков",
            "value": "22089"
        },
        {
            "place": 4,
            "avatar": "https://sun1-93.userapi.com/s/v1/ig2/i_O7QjCID0231tFwHRi8_TcNTz1qz0-PWQYiM9cXm_X1nJmtlnDI5Mjo293J_v9HG2T4Jsltrn7fxa7WZpkxfBab.jpg?quality=95&crop=1,1,706,706&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640&ava=1&cs=400x400",
            "domain": "br_hamhoev",
            "username": "Ali Hamhoev",
            "value": "15132"
        },
        {
            "place": 5,
            "avatar": "https://sun1-98.userapi.com/s/v1/ig2/is-l3LyhD_2s_3L5lerRYtQuiDCVMdloLYw-v2xl_PaE2LFMYIYMLjuOsT4hoZtOfTmTIQDp5QmcpsGwO3R_tOe2.jpg?quality=95&crop=5,0,1074,1074&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "legendarybr",
            "username": "Глеб Легенда",
            "value": "13330"
        },
        {
            "place": 6,
            "avatar": "https://sun1-95.userapi.com/impg/DW4IDqvukChyc-WPXmzIot46En40R00idiUAXw/l5w5aIHioYc.jpg?quality=96&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360&sign=10ad7d7953daabb7b0e707fdfb7ebefd&u=I6EtahnrCRLlyd0MhT2raQt6ydhuyxX4s72EHGuUSoM&cs=400x400",
            "domain": "id749561341",
            "username": "Egor Robion",
            "value": "8321"
        },
        {
            "place": 7,
            "avatar": "https://sun1-20.userapi.com/s/v1/ig2/JeMuqw3OPV495gH_cO-lEd4YqTX8LMwPiY-tk2_i59Y09fCcnK6kKre8QH2LYwbu3JkPgwhWK8sSb4ALdk9pEH9R.jpg?quality=95&crop=1,1,732,732&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "dine228",
            "username": "Ярослав Волков",
            "value": "8117"
        },
        {
            "place": 8,
            "avatar": "https://sun1-83.userapi.com/s/v1/ig2/hfpoCTpo6HAFG_YYqBOrcKOZFHDOKucmB1Wybthelk6tCfkUo6r3cguErTY4w8uXsUQ0IS5IConJK_lDA6xRAYZS.jpg?quality=95&crop=67,44,622,622&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540&ava=1&cs=400x400",
            "domain": "mryakudz",
            "username": "Роман С",
            "value": "7868"
        },
        {
            "place": 9,
            "avatar": "https://sun1-92.userapi.com/s/v1/ig2/aFoPK-TVzzNXF5kDMgnPztkZpf9s64stQhD7brtU8CFerE7kKJmjYPpQ281Uo5Ncx-9Fqotro3U2dsh3KurXq8sl.jpg?quality=95&crop=0,0,600,600&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540&ava=1&cs=400x400",
            "domain": "avroracanabis",
            "username": "Avrora Canabis",
            "value": "7725"
        },
        {
            "place": 10,
            "avatar": "https://sun1-47.userapi.com/s/v1/ig2/Qz4drPtvmdmbiOUahwrUszKG_JmDjmbns9ck3cTmrGqPKvCusK8WQk01IzYll_1EXwptqGlcnHvJeunSdAwQAjVN.jpg?quality=96&crop=66,66,531,531&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480&ava=1&cs=400x400",
            "domain": "andreya_netegai",
            "username": "Андрюха Измайлов",
            "value": "7695"
        },
        {
            "place": 11,
            "avatar": "https://sun1-95.userapi.com/impg/DW4IDqvukChyc-WPXmzIot46En40R00idiUAXw/l5w5aIHioYc.jpg?quality=96&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360&sign=10ad7d7953daabb7b0e707fdfb7ebefd&u=I6EtahnrCRLlyd0MhT2raQt6ydhuyxX4s72EHGuUSoM&cs=400x400",
            "domain": "siletsa",
            "username": "Vania S",
            "value": "6773"
        },
        {
            "place": 12,
            "avatar": "https://sun1-24.userapi.com/s/v1/ig2/-xBILk_QIFLpxL2TMDZoRNr8I55LdubXJZMTZHsXyC4s3LomaUVfvqDEuvVTlkZ67BLIW3Zn5mtHLX3sY_qzY291.jpg?quality=95&crop=40,0,1020,1020&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "meo_w15",
            "username": "Matvey Morris",
            "value": "6717"
        },
        {
            "place": 13,
            "avatar": "https://sun1-90.userapi.com/s/v1/ig2/FWfCfhOglnQ1bFpBvnCXfxsnK1tVxpiEi3cHGQre6knIVPTSKU7jgBZskOAd24AXNBM_eOHevH8g3E9LEmHcGysS.jpg?quality=95&crop=6,1,1067,1067&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "id850679336",
            "username": "Таганрок Бухает",
            "value": "6320"
        },
        {
            "place": 14,
            "avatar": "https://sun1-30.userapi.com/s/v1/ig2/Fz0eJ4rLMgsHxNsTXsR1qBpA6M4hFPatdM7tQdfPmb5WpQMkfJZWZZI090eN0SI2Jbcaja2hBjl5KBPX1Lv4QZgl.jpg?quality=95&crop=1,359,1289,1289&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1280x1280&ava=1&cs=400x400",
            "domain": "ekaterina_waleson",
            "username": "Екатерина Леонова",
            "value": "6133"
        },
        {
            "place": 15,
            "avatar": "https://sun1-91.userapi.com/s/v1/ig2/6ozqhzes9JwTeuaw7DmlTmH4cNsm4bDBXp4R0NWbBbC6H6Ib-vM8p5_qNo1SOupvbS8mM0BklOloWqJIi0ln5tAj.jpg?quality=95&crop=1,514,719,719&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640&ava=1&cs=400x400",
            "domain": "mrezersize",
            "username": "Maksim Rezersize",
            "value": "5991"
        },
        {
            "place": 16,
            "avatar": "https://sun1-54.userapi.com/s/v1/ig2/vdtlWFr8Cwd_IOh4Y19gQf-APy6IDO31iqWpy8iTj50vSStynx8Zd47Ggx4VdxAEX6EQNMBPwEbZ9qVGAyvuFcbE.jpg?quality=95&crop=1,0,734,734&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "vz1215",
            "username": "Владислав Зотов",
            "value": "5936"
        },
        {
            "place": 17,
            "avatar": "https://sun1-88.userapi.com/s/v1/ig2/6dJ6hEaXddHUphlcQIK2lJvZ_pByzCRdsvbj04ekCSUwO8RTrztH5OgxxC5KBDp0D12wuWdcpEhyYJHdKEYG6eZa.jpg?quality=95&crop=196,53,364,364&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360&ava=1&cs=400x400",
            "domain": "animiru69",
            "username": "Роман Анимиру",
            "value": "5793"
        },
        {
            "place": 18,
            "avatar": "https://sun1-98.userapi.com/s/v1/ig2/rMX7ZoOBqHDi6CTxiQpIEXtLCAh6s6BuljzwtMkWobV4o5bL_l8aQvF2UtM1bN8tci8gnRnKm-Ij81VUS-eZGQJI.jpg?quality=95&crop=234,0,575,575&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540&ava=1&cs=400x400",
            "domain": "mark17babanin",
            "username": "Марк Бабанин",
            "value": "5636"
        },
        {
            "place": 19,
            "avatar": "https://sun1-23.userapi.com/s/v1/ig2/BwrPcJwA5sISIesiJ0jIc6gy29-IqpwUk9bSIF2t_2cm9KyeVusvK4iuluLOcJWpa3Nvw7IEq3SJ19MHm0SBmvKL.jpg?quality=95&crop=0,269,715,715&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640&ava=1&cs=400x400",
            "domain": "neprogressim5",
            "username": "Dmitry Morozov",
            "value": "5503"
        },
        {
            "place": 20,
            "avatar": "https://sun1-84.userapi.com/s/v1/ig2/m2yKHjLhrkZN3AhRHypfsgJejAkWvJ5iYKF2clekv2BQwPr45OufeaGdsfWmugImkT-rsZ74BmMKSqR2kVG3yGLV.jpg?quality=95&crop=111,291,539,539&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480&ava=1&cs=400x400",
            "domain": "id741993423",
            "username": "Андрей Тихненко",
            "value": "5468"
        },
        {
            "place": 21,
            "avatar": "https://sun1-93.userapi.com/s/v1/ig2/qtyu3LVUOdbVWBBMq9B-XFYMeCzlm-HUD0heLlT9kwsBY9MN9gsCtVLBEJB1o-4Z2CkP7F6OMn9NkRakEalAdPeF.jpg?quality=95&crop=1,0,748,748&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "vrodenekit",
            "username": "Nikita Kapustin",
            "value": "5381"
        },
        {
            "place": 22,
            "avatar": "https://sun1-88.userapi.com/s/v1/ig2/TQtE1zuszUlPM5kZDM0J-CSPvNaOG7J4fJaHaG4b8z9D0f-03i2oM6SAmGNAzOWCIqB1sxn9Kq-b7cgZ5cA95pxV.jpg?quality=95&crop=281,999,561,561&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540&ava=1&cs=400x400",
            "domain": "kewsik2t",
            "username": "Ernest Klimt",
            "value": "5282"
        },
        {
            "place": 23,
            "avatar": "https://sun1-97.userapi.com/s/v1/ig2/HBQuAukPpDgKFxZ0Ig9C8DQRq70dYkZLVuM9lovI4qRYOpWEKokcbz_rbJnLQkOSR4-145cwkxBpeeUZy5yAcSMM.jpg?quality=95&crop=2,22,733,733&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "tipodashkka",
            "username": "Daria Alexandrovna",
            "value": "5227"
        },
        {
            "place": 24,
            "avatar": "https://sun1-96.userapi.com/s/v1/ig2/pyXK9Qi8FPFN762TsPcZ_pjpy1wQv-tOnM3FIgnytAqcVvCCcXweREWlIxerr_e6Ls-tqBhTfJ_RCm2Unikv2ANx.jpg?quality=95&crop=350,1,898,898&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "id833467080",
            "username": "Саня Фуфлик",
            "value": "5193"
        },
        {
            "place": 25,
            "avatar": "https://sun1-95.userapi.com/s/v1/ig2/4i4EDymkNdl3DUE4nHQSUZOOUfFjjD0j0t8IFPS7ZEbcC9S3Uga0lxYR1r9r0wcm8IssOEAvjxBnwVX-M2HMKkxq.jpg?quality=95&crop=1,123,718,718&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640&ava=1&cs=400x400",
            "domain": "rasuliich",
            "username": "Расул Джаббаров",
            "value": "5172"
        },
        {
            "place": 26,
            "avatar": "https://sun1-55.userapi.com/s/v1/ig2/S8cwuMaGzytaOmXstDV8HW3b1yCIOq1AwFmp6HmSB4SyTeSkCHbK35l2cjk1A7B-Rlt6aAFNoTbLfIWbHjznGMyT.jpg?quality=96&crop=90,90,720,720&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "id704152085",
            "username": "Dior Forbes",
            "value": "5161"
        },
        {
            "place": 27,
            "avatar": "https://sun1-94.userapi.com/s/v1/ig2/sK80JVN21kfDts1DeHsWzvaPBU-RYAwM7GYXK98xCDPzdrUxKKWteBI4d_uK_JEKe8eNRxF8px1o4ttqJ_PYQ_QW.jpg?quality=95&crop=106,304,436,436&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360&ava=1&cs=400x400",
            "domain": "kingmaninban",
            "username": "Олег Мирный",
            "value": "5013"
        },
        {
            "place": 28,
            "avatar": "https://sun1-28.userapi.com/s/v1/ig2/j7U-gl9Ao32kNoXVhLwP5Z_bigBkag_1haqKV8J79mFZ2Pacz32iNwEK3rqjgXJOWoe1BbPwZMWUe09xXc50RQpP.jpg?quality=95&crop=1,1,1279,1279&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080&ava=1&cs=400x400",
            "domain": "semmws",
            "username": "Luna Corleone",
            "value": "4900"
        },
        {
            "place": 29,
            "avatar": "https://sun1-86.userapi.com/s/v1/ig2/McjZdu3OsaoznFI6pau4rApI2dmSQxoR9cdaHMoT0PfyK2UZ-N4qSkTmOuQj26mU7_pcYGUBHeYWkjMIUGN-RRWD.jpg?quality=95&crop=2,2,733,733&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=400x400",
            "domain": "rp.monster",
            "username": "Merry Tatar",
            "value": "4816"
        },
        {
            "place": 30,
            "avatar": "https://sun1-17.userapi.com/s/v1/ig2/ld9mMXcs_Elk73tF7ZzAM41RMfpVz8y4-EW6rnlNxCWIE3y8u89nl5DrR3_EGnmJx6SH-H5YWYs8zRpKh-A4gp4v.jpg?quality=95&crop=184,184,367,367&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360&ava=1&cs=400x400",
            "domain": "absolut_hehehe",
            "username": "Джотаро Токийский",
            "value": "4748"
        }
    ]
}

function LeaderBoard() {
    const [textCategory, setTextCategory] = useState("Топ по монетам");
    const [page, setPage] = useState(0);
    const [data, setData] = useState({ total: 0, items: [] });
    const [nameInput, setNameInput] = useState("");

    useEffect(() => {
        // сбрасываем страницу, если изменился фильтр или категория
        setPage(0);
    }, [nameInput, textCategory]);

    useEffect(() => {
        const categoryKey = DICT_CATEGORY_NAME[textCategory];
        const offset = page * PAGE_SIZE;

        const searchParam = nameInput ? `&search=${encodeURIComponent(nameInput)}` : "";

        fetch(`/api/leaderboard/${categoryKey}?offset=${offset}&limit=${PAGE_SIZE}${searchParam}`)
            .then(res => res.json())
            .then(json => setData(json))
            .catch(console.error);
    }, [page, nameInput, textCategory]);

    const maxPage = Math.ceil(data.total / PAGE_SIZE) - 1;

    return (
        <div className="leaderboard">
            <header>
                <MiniProfileLegacy/>
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
                            <li className="leaderboard__list-buttons__button" id="input-name">
                                <input
                                    value={nameInput}
                                    placeholder="Введите имя пользователя..."
                                    className="leaderboard__list-buttons__input"

                                    onInput={(e) => setNameInput(e.target.value)}
                                />
                            </li>

                            <li
                                className="leaderboard__list-buttons__button"
                                onMouseLeave={() => {
                                    const menuOption
                                        = document.querySelector(".show-menu-category");
                                    const inputOption
                                        = document.getElementById("input-option");

                                    inputOption.style.borderBottomLeftRadius = "8px";
                                    inputOption.style.borderBottomRightRadius = "8px";
                                    menuOption.style.display = "none";
                                }}
                            >
                                <div className="leaderboard__list-buttons__option-div">
                                    <button
                                        onClick={() => {
                                            const menuOption
                                                = document.querySelector(".show-menu-category");
                                            const inputOption
                                                = document.getElementById("input-option");

                                            inputOption.style.borderBottomLeftRadius = "0";
                                            inputOption.style.borderBottomRightRadius = "0";
                                            menuOption.style.display = "block";
                                        }}
                                        id="input-option"
                                        className="leaderboard__list-buttons__option"
                                    >{textCategory}</button>

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

                                <nav className="show-menu-category" style={{display: "none"}}>
                                    <ul className="show-menu-category-lists">
                                        {Object.keys(DICT_CATEGORY_NAME).map((name, i, arr) => (
                                            <CategoryOption
                                                key={name}
                                                nameCategory={name}
                                                descriptorSetTextCategory={() => {
                                                    setTextCategory(name);
                                                    setPage(0);
                                                }}
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
                                    username={user.domain}
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