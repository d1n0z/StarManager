// img
import profileImg from '../image/profileImgTestHighQ.jpg';
import catImg from '../image/carImg.png';

// css
import "../styles/personal-account.css";

// js
import { MiniProfile } from "../Components/mini-profile";
import {
    EnterSettingButt,
    EnterCloseButt,
    LeaveSettingButt,
    LeaveCloseButt
} from "../Components/PersonalAccount/butt-event";
import { MemberCase } from "../Components/PersonalAccount/member-case";


function PersonalAccount() {
    return (
        <div className={"profile"}>
            <MiniProfile></MiniProfile>

            <div className={"profile__background"}></div>

            <article className={"profile__menu-members"}>
                <aside className={"profile__menu-members__setting-butt"}
                       onMouseEnter={() => EnterSettingButt()}
                       onMouseLeave={() => LeaveSettingButt()}>
                    <svg className={"profile__menu-members__setting-butt-svg"}
                         viewBox="0 0 46 46" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="1" y="1" width="44" height="44" rx="12" stroke="#56A0F6"
                              stroke-width="2"/>
                        <g>
                            <path
                                d="M31.1 20.2214C29.29 20.2214 28.55 18.9414 29.45 17.3714C29.97 16.4614 29.66 15.3014 28.75 14.7814L27.02 13.7914C26.23 13.3214 25.21 13.6014 24.74 14.3914L24.63 14.5814C23.73 16.1514 22.25 16.1514 21.34 14.5814L21.23 14.3914C20.78 13.6014 19.76 13.3214 18.97 13.7914L17.24 14.7814C16.33 15.3014 16.02 16.4714 16.54 17.3814C17.45 18.9414 16.71 20.2214 14.9 20.2214C13.86 20.2214 13 21.0714 13 22.1214V23.8814C13 24.9214 13.85 25.7814 14.9 25.7814C16.71 25.7814 17.45 27.0614 16.54 28.6314C16.02 29.5414 16.33 30.7014 17.24 31.2214L18.97 32.2114C19.76 32.6814 20.78 32.4014 21.25 31.6114L21.36 31.4214C22.26 29.8514 23.74 29.8514 24.65 31.4214L24.76 31.6114C25.23 32.4014 26.25 32.6814 27.04 32.2114L28.77 31.2214C29.68 30.7014 29.99 29.5314 29.47 28.6314C28.56 27.0614 29.3 25.7814 31.11 25.7814C32.15 25.7814 33.01 24.9314 33.01 23.8814V22.1214C33 21.0814 32.15 20.2214 31.1 20.2214ZM23 26.2514C21.21 26.2514 19.75 24.7914 19.75 23.0014C19.75 21.2114 21.21 19.7514 23 19.7514C24.79 19.7514 26.25 21.2114 26.25 23.0014C26.25 24.7914 24.79 26.2514 23 26.2514Z"
                                fill="#56A0F6"/>
                        </g>
                    </svg>

                    <p className={"profile__menu-members__setting-butt-message-first"}>
                        Настройки
                        <p className={"profile__menu-members__setting-butt-message-second"}>чата</p>
                    </p>
                </aside>

                <button className={"profile__menu-members__close-butt--mobile"}>Закрыть</button>
                <aside className={"profile__menu-members__close-butt"}
                       onMouseEnter={() => EnterCloseButt()}
                       onMouseLeave={() => LeaveCloseButt()}>
                    <svg className={"profile__menu-members__close-butt-svg"}
                         viewBox="0 0 46 46" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="1" y="1" width="44" height="44" rx="12" stroke="#56A0F6"
                              stroke-width="2"/>
                        <g>
                            <path
                                d="M25.1 23L29.225 18.875C29.825 18.275 29.825 17.375 29.225 16.775C29 16.475 28.625 16.25 28.25 16.25C27.875 16.25 27.5 16.4 27.2 16.7L23 20.9L18.875 16.775C18.275 16.175 17.3 16.175 16.775 16.775C16.475 17 16.25 17.375 16.25 17.825C16.25 18.275 16.4 18.575 16.7 18.875L20.825 23L16.7 27.125C16.475 27.425 16.25 27.8 16.25 28.25C16.25 28.625 16.4 29 16.7 29.3C17 29.6 17.375 29.75 17.75 29.75C18.125 29.75 18.5 29.6 18.8 29.3L22.925 25.175L27.05 29.3C27.65 29.9 28.625 29.9 29.15 29.3C29.75 28.7 29.75 27.725 29.15 27.2L25.1 23Z"
                                fill="#56A0F6"/>
                        </g>
                    </svg>

                    <p className={"profile__menu-members__close-butt-message-first"}>
                        Закрыть список
                        <p className={"profile__menu-members__close-butt-message-second"}>участников</p>
                    </p>
                </aside>

                <aside className={"profile__menu-members__lists"}>
                    <article className={"profile__menu-members__lists-main"}>
                        <img className={"profile__menu-members__lists-main-img"} src={catImg}/>

                        <input
                            placeholder={"Поиск по имени..."}
                            className={"profile__menu-members__lists-main-search"}
                        />
                        <svg className={"profile__menu-members__lists-main-search-svg"}
                             viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path fill-rule="evenodd" clip-rule="evenodd"
                                  d="M6.66675 0.666504C3.35304 0.666504 0.666748 3.3528 0.666748 6.6665C0.666748 9.98024 3.35304 12.6665 6.66675 12.6665C8.08342 12.6665 9.38542 12.1755 10.4119 11.3544L13.5287 14.4712C13.789 14.7316 14.2111 14.7316 14.4715 14.4712C14.7318 14.2109 14.7318 13.7888 14.4715 13.5284L11.3547 10.4116C12.1757 9.38517 12.6667 8.08317 12.6667 6.6665C12.6667 3.3528 9.98048 0.666504 6.66675 0.666504ZM2.00008 6.6665C2.00008 4.08918 4.08942 1.99984 6.66675 1.99984C9.24408 1.99984 11.3334 4.08918 11.3334 6.6665C11.3334 9.24384 9.24408 11.3332 6.66675 11.3332C4.08942 11.3332 2.00008 9.24384 2.00008 6.6665Z"
                                  fill="#1F364D"/>
                        </svg>

                        <article className={"profile__menu-members__lists-main-search-sortnick"}>
                            <p>По имени
                                <svg className={"profile__menu-members__lists-main-search-sortnick-svg"}
                                     viewBox="0 0 7 6" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M4.24061 0.816313C3.84375 0.378889 3.15625 0.37889 2.75939 0.816314L0.253744 3.57807C-0.32927 4.22068 0.12669 5.25 0.994358 5.25L6.00564 5.25C6.87331 5.25 7.32927 4.22067 6.74625 3.57807L4.24061 0.816313Z"
                                        fill="white"/>
                                </svg>
                            </p>
                        </article>

                        <article className={"profile__menu-members__lists-main-search-sortroot"}>
                            <p>По правам
                                <svg className={"profile__menu-members__lists-main-search-sortroot-svg"}
                                     viewBox="0 0 7 6" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M4.24061 0.816313C3.84375 0.378889 3.15625 0.37889 2.75939 0.816314L0.253744 3.57807C-0.32927 4.22068 0.12669 5.25 0.994358 5.25L6.00564 5.25C6.87331 5.25 7.32927 4.22067 6.74625 3.57807L4.24061 0.816313Z"
                                        fill="white"/>
                                </svg>
                            </p>
                        </article>

                        <button className={"profile__menu-members__lists-main-search-premium"}>Только PREMIUM</button>
                    </article>

                    <nav className={"profile__menu-members__lists-users"}>
                        <ul className={"profile__menu-members__lists-members"}>
                            <MemberCase nick={"Климушкин Даниил"} root={0}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={1}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={2}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={3}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={4}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={5}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={6}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={7}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={8}></MemberCase>
                            <MemberCase nick={"Климушкин Даниил"} root={8} premium={true}></MemberCase>
                        </ul>
                    </nav>
                </aside>
            </article>

            <>
                <article className={"profile__menu-block-mobile"}>
                    <svg width="900" className={"profile__menu-block-mobile__menu"} viewBox="0 0 693 538"
                         fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path
                            d="M33 0.5H182.968C215.267 55.5421 275.067 92.5 343.5 92.5C411.933 92.5 471.733 55.5421 504.032 0.5H655C675.711 0.5 692.5 17.2893 692.5 38V500C692.5 520.711 675.711 537.5 655 537.5H33C12.2893 537.5 -4.5 520.711 -4.5 500V38C-4.5 17.2893 12.2893 0.5 33 0.5Z"
                            fill="#10151B" stroke="#121C28"/>
                    </svg>

                    <aside className={"profile__menu-block-mobile__avatar"}>
                        <img className={"profile__menu-block-mobile__avatar-img"}
                             src={profileImg}/>

                        <p className={"profile__menu-block-mobile__avatar-first"}>Даниил
                            <p className={"profile__menu-block-mobile__avatar-second"}>Климушкин</p>
                        </p>

                        <div className={"profile__menu-block-mobile__avatar__lvl"}>
                            <p className={"profile__menu-block-mobile__avatar__lvl-text"}>3</p>
                        </div>
                    </aside>

                    <nav className={"profile__menu-block-mobile__information"}>
                        <ul className={"profile__menu-block-mobile__information-elements"}>
                            <li className={"profile__menu-block-mobile__information-element"}>
                                <svg viewBox="0 0 76 76" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <rect x="0.5" y="0.5" width="75" height="75" rx="15.5" fill="#10151B"
                                          stroke="#182C43"/>
                                    <path
                                        d="M48.6875 28.7375C48.3312 23.9875 44.4125 20.1875 39.5437 20.1875H29.45C24.3437 20.1875 20.1875 24.3438 20.1875 29.3313V46.3125C20.1875 46.7875 20.425 47.1437 20.9 47.3813C21.0187 47.5 21.2562 47.5 21.375 47.5C21.6125 47.5 21.9687 47.3812 22.2062 47.2625C23.75 45.9562 25.5312 44.8875 27.3125 44.0562V54.625C27.3125 55.1 27.55 55.4562 28.025 55.6937C28.1437 55.8125 28.3812 55.8125 28.5 55.8125C28.7375 55.8125 29.0937 55.6937 29.3312 55.575C32.775 52.4875 37.2875 50.825 41.9187 50.825H46.6687C51.775 50.825 55.9312 46.6688 55.9312 41.6812V37.6437C55.8125 33.3687 52.725 29.6875 48.6875 28.7375ZM53.4375 41.6812C53.4375 45.4813 50.35 48.45 46.55 48.45H41.8C37.525 48.45 33.25 49.7563 29.6875 52.25V43.225C31.35 42.75 33.0125 42.5125 34.7937 42.5125H39.5437C44.65 42.5125 48.8062 38.3563 48.8062 33.3688V31.2312C51.5375 32.0625 53.5562 34.675 53.5562 37.6437V41.6812H53.4375Z"
                                        fill="#152537"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__information-element-text"}>
                                    <p className={"profile__menu-block-mobile__information-element-text-first"}>
                                        Количество бесед с ботом:
                                    </p>
                                    <p className={"profile__menu-block-mobile__information-element-text-second"}>
                                        4
                                    </p>
                                </aside>
                            </li>

                            <li className={"profile__menu-block-mobile__information-element"}>
                                <svg viewBox="0 0 76 76" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <rect x="0.5" y="0.5" width="75" height="75" rx="15.5" fill="#10151B"
                                          stroke="#182C43"/>
                                    <path
                                        d="M49.6016 26.3953L28.0783 47.9187C27.2717 48.7253 25.915 48.6153 25.255 47.662C22.9817 44.3437 21.6433 40.4203 21.6433 36.387V28.3387C21.6433 26.8353 22.78 25.1303 24.1733 24.562L34.3849 20.382C36.6949 19.4287 39.2616 19.4287 41.5716 20.382L48.9966 23.407C50.2066 23.902 50.5183 25.4787 49.6016 26.3953Z"
                                        fill="#152537"/>
                                    <path
                                        d="M51.3284 28.9099C52.5201 27.9016 54.3351 28.7632 54.3351 30.3216V36.3899C54.3351 45.3549 47.8267 53.7516 38.9351 56.2082C38.3301 56.3732 37.6701 56.3732 37.0467 56.2082C34.4434 55.4749 32.0234 54.2466 29.9518 52.6332C29.0718 51.9549 28.9801 50.6716 29.7501 49.8832C33.7468 45.7949 45.4434 33.8782 51.3284 28.9099Z"
                                        fill="#152537"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__information-element-text"}>
                                    <p className={"profile__menu-block-mobile__information-element-text-first"}>
                                        Ваша репутация:
                                    </p>
                                    <p className={"profile__menu-block-mobile__information-element-text-second"}>
                                        0 (#199470)
                                    </p>
                                </aside>
                            </li>

                            <li className={"profile__menu-block-mobile__information-element--premium"}>
                                <svg viewBox="0 0 75 75" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <rect x="0.5" y="0.5" width="74" height="74" rx="15.5" fill="#10151B"
                                          stroke="#182C43"/>
                                    <path
                                        d="M57.1672 25.9431V44.3047C57.1672 49.5947 52.8738 53.888 47.5838 53.888H28.4172C27.5355 53.888 26.6922 53.773 25.868 53.543C24.6797 53.2172 24.2964 51.703 25.178 50.8214L45.5522 30.4472C45.9738 30.0256 46.6063 29.9297 47.2005 30.0447C47.8138 30.1597 48.4847 29.9872 48.9638 29.5272L53.8897 24.5822C55.6913 22.7806 57.1672 23.3747 57.1672 25.9431Z"
                                        fill="#152537"/>
                                    <path
                                        d="M43.0599 29.1056L22.9924 49.173C22.0724 50.093 20.5391 49.863 19.9258 48.713C19.2166 47.4097 18.8333 45.8955 18.8333 44.3047V25.9431C18.8333 23.3748 20.3091 22.7806 22.1108 24.5823L27.0558 29.5464C27.8033 30.2748 29.0299 30.2748 29.7774 29.5464L36.6391 22.6656C37.3866 21.9181 38.6133 21.9181 39.3608 22.6656L43.0791 26.3839C43.8074 27.1314 43.8074 28.3581 43.0599 29.1056Z"
                                        fill="#152537"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__information-element-text"}>
                                    <p className={"profile__menu-block-mobile__information-element-text-first"}>
                                        Premium:
                                    </p>
                                    <p className={"profile__menu-block-mobile__information-element-text-second"}>
                                        осталось дней: 1
                                    </p>
                                </aside>
                            </li>

                            <li className={"profile__menu-block-mobile__information-element--legend"}>
                                <svg viewBox="0 0 75 75" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <rect x="0.5" y="0.5" width="74" height="74" rx="15.5" fill="#10151B"
                                          stroke="#914400"/>
                                    <path
                                        d="M50.666 23.0449C50.6932 21.7575 50.6443 20.9441 50.6443 20.9441L38.0638 20.9346H38H37.9362L25.3544 20.9441C25.3544 20.9441 25.3068 21.7575 25.334 23.0449H17V24.4192C17 24.7329 17.053 32.1326 21.6199 36.1862C23.5252 37.8769 25.9016 38.727 28.7032 38.7284C29.1269 38.7284 29.5628 38.6998 30.0041 38.6618C31.5957 40.8414 33.4344 42.3678 35.5027 43.1282V49.1645H29.4311V52.9452H27.4253V55.065H37.9362H38.0638H48.5747V52.9465H46.5676V49.1659H40.496V43.1296C42.5629 42.3691 44.4029 40.8427 45.9945 38.6632C46.4386 38.7012 46.8745 38.7284 47.2982 38.7284C50.0984 38.7256 52.4748 37.8769 54.3801 36.1848C58.947 32.1312 59 24.7315 59 24.4178V23.0449H50.666ZM23.4532 34.137C20.8445 31.8284 20.0731 27.8766 19.845 25.7935H25.4915C25.7305 28.3886 26.2927 31.622 27.5896 34.4643C27.8273 34.9857 28.0771 35.48 28.3324 35.9635C26.3864 35.8888 24.7487 35.2818 23.4532 34.137ZM52.5468 34.137C51.2527 35.2831 49.6136 35.8888 47.6689 35.9635C47.9242 35.4814 48.1741 34.9857 48.4117 34.4643C49.7086 31.622 50.2708 28.3886 50.5085 25.7935H56.155C55.9269 27.8753 55.1569 31.827 52.5468 34.137Z"
                                        fill="#914400"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__information-element-text"}>
                                    <p className={"profile__menu-block-mobile__information-element-text-first"}>
                                        Ваша лига:
                                    </p>
                                    <p className={"profile__menu-block-mobile__information-element-text-second"}>
                                        Легенда
                                    </p>
                                </aside>
                            </li>
                        </ul>
                    </nav>

                    <nav className={"profile__menu-block-mobile__chats"}>
                        <ul className={"profile__menu-block-mobile__chats-elements"}>
                            <li className={"profile__menu-block-mobile__chats-element--premium"}>
                                <svg className={"profile__menu-block-mobile__chats-element-backsvg"}
                                     width="810" viewBox="0 0 647 152" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M16 0.5H631C639.56 0.50001 646.5 7.43959 646.5 16V75.5H0.5V16L0.504883 15.5996C0.717246 7.22424 7.57345 0.5 16 0.5Z"
                                        fill="#10151B" stroke="#182C43"/>
                                    <mask id="path-2-inside-1_0_1" fill="white">
                                        <path d="M0 76H324V152H16C7.16343 152 0 144.837 0 136V76Z"/>
                                    </mask>
                                    <path d="M0 76H324V152H16C7.16343 152 0 144.837 0 136V76Z" fill="#10151B"/>
                                    <path
                                        d="M0 76H324H0ZM325 153H16C6.61116 153 -1 145.389 -1 136H1C1 144.284 7.71573 151 16 151H323L325 153ZM16 153C6.61116 153 -1 145.389 -1 136V76H1V136C1 144.284 7.71573 151 16 151V153ZM325 76V153L323 151V76H325Z"
                                        fill="#182C43" mask="url(#path-2-inside-1_0_1)"/>
                                    <mask id="path-4-inside-2_0_1" fill="white">
                                        <path d="M324 76H647V136C647 144.837 639.837 152 631 152H324V76Z"/>
                                    </mask>
                                    <path d="M324 76H647V136C647 144.837 639.837 152 631 152H324V76Z" fill="#10151B"/>
                                    <path
                                        d="M324 76H647H324ZM648 136C648 145.389 640.389 153 631 153H324V151H631C639.284 151 646 144.284 646 136H648ZM324 152V76V152ZM648 76V136C648 145.389 640.389 153 631 153V151C639.284 151 646 144.284 646 136V76H648Z"
                                        fill="#182C43" mask="url(#path-4-inside-2_0_1)"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__chats-element-title"}>
                                    <img className={"profile__menu-block-mobile__chats-element-title-avatar"}
                                         src={catImg}/>

                                    <p className={"profile__menu-block-mobile__chats-element-text"}>
                                        Название чата:
                                        <p className={"profile__menu-block-mobile__chats-element-subtext"}>
                                            Мемы про котов
                                        </p>
                                    </p>

                                    <div className={"profile__menu-block-mobile__chats-element-title-button"}>
                                        <svg width="70" viewBox="0 0 56 56" fill="none"
                                             xmlns="http://www.w3.org/2000/svg">
                                            <rect width="56" height="56" rx="8" fill="#121C28"/>
                                            <path
                                                d="M35.833 22.0072C35.7338 21.993 35.6347 21.993 35.5355 22.0072C33.3397 21.9363 31.5972 20.1372 31.5972 17.9272C31.5972 15.6747 33.4247 13.833 35.6913 13.833C37.9438 13.833 39.7855 15.6605 39.7855 17.9272C39.7713 20.1372 38.0288 21.9363 35.833 22.0072Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M40.4549 31.8256C38.8682 32.8881 36.644 33.2847 34.5899 33.0156C35.1282 31.8539 35.4115 30.5647 35.4257 29.2047C35.4257 27.7881 35.114 26.4422 34.519 25.2664C36.6157 24.9831 38.8399 25.3797 40.4407 26.4422C42.679 27.9156 42.679 30.3381 40.4549 31.8256Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M20.1236 22.0072C20.2228 21.993 20.322 21.993 20.4211 22.0072C22.617 21.9363 24.3595 20.1372 24.3595 17.9272C24.3595 15.6605 22.532 13.833 20.2653 13.833C18.0128 13.833 16.1853 15.6605 16.1853 17.9272C16.1853 20.1372 17.9278 21.9363 20.1236 22.0072Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M20.2808 29.205C20.2808 30.5792 20.5783 31.8825 21.1166 33.0583C19.1191 33.2708 17.0366 32.8458 15.5066 31.84C13.2683 30.3525 13.2683 27.93 15.5066 26.4425C17.0225 25.4225 19.1616 25.0117 21.1733 25.2383C20.5925 26.4283 20.2808 27.7742 20.2808 29.205Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M28.1711 33.4825C28.0577 33.4683 27.9302 33.4683 27.8027 33.4825C25.1961 33.3975 23.1135 31.2583 23.1135 28.6233C23.1277 25.9317 25.2952 23.75 28.0011 23.75C30.6927 23.75 32.8744 25.9317 32.8744 28.6233C32.8602 31.2583 30.7919 33.3975 28.1711 33.4825Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M23.567 36.4162C21.4279 37.847 21.4279 40.1987 23.567 41.6154C26.0037 43.2445 29.9987 43.2445 32.4354 41.6154C34.5745 40.1845 34.5745 37.8329 32.4354 36.4162C30.0129 34.787 26.0179 34.787 23.567 36.4162Z"
                                                fill="#56A0F6"/>
                                        </svg>

                                        <svg width="70" viewBox="0 0 56 56" fill="none"
                                             xmlns="http://www.w3.org/2000/svg">
                                            <rect width="56" height="56" rx="8" fill="#121C28"/>
                                            <path
                                                d="M39.4749 25.0633C36.9108 25.0633 35.8624 23.25 37.1374 21.0258C37.8741 19.7367 37.4349 18.0933 36.1458 17.3567L33.6949 15.9542C32.5758 15.2883 31.1308 15.685 30.4649 16.8042L30.3091 17.0733C29.0341 19.2975 26.9374 19.2975 25.6483 17.0733L25.4924 16.8042C24.8549 15.685 23.4099 15.2883 22.2908 15.9542L19.8399 17.3567C18.5508 18.0933 18.1116 19.7508 18.8483 21.04C20.1374 23.25 19.0891 25.0633 16.5249 25.0633C15.0516 25.0633 13.8333 26.2675 13.8333 27.755V30.2483C13.8333 31.7217 15.0374 32.94 16.5249 32.94C19.0891 32.94 20.1374 34.7533 18.8483 36.9775C18.1116 38.2667 18.5508 39.91 19.8399 40.6467L22.2908 42.0492C23.4099 42.715 24.8549 42.3183 25.5208 41.1992L25.6766 40.93C26.9516 38.7058 29.0483 38.7058 30.3374 40.93L30.4933 41.1992C31.1591 42.3183 32.6041 42.715 33.7233 42.0492L36.1741 40.6467C37.4633 39.91 37.9024 38.2525 37.1658 36.9775C35.8766 34.7533 36.9249 32.94 39.4891 32.94C40.9624 32.94 42.1808 31.7358 42.1808 30.2483V27.755C42.1666 26.2817 40.9624 25.0633 39.4749 25.0633ZM27.9999 33.6058C25.4641 33.6058 23.3958 31.5375 23.3958 29.0017C23.3958 26.4658 25.4641 24.3975 27.9999 24.3975C30.5358 24.3975 32.6041 26.4658 32.6041 29.0017C32.6041 31.5375 30.5358 33.6058 27.9999 33.6058Z"
                                                fill="#56A0F6"/>
                                        </svg>
                                    </div>
                                </aside>

                                <aside className={"profile__menu-block-mobile__chats-element-members"}>
                                    <p className={"profile__menu-block-mobile__chats-element-text--members"}>
                                        Количество участников
                                        <p className={"profile__menu-block-mobile__chats-element-subtext--members"}>
                                            23
                                        </p>
                                    </p>
                                </aside>

                                <aside className={"profile__menu-block-mobile__chats-element-lvl"}>
                                    <p className={"profile__menu-block-mobile__chats-element-text--lvl"}>
                                        Уровень админ-прав
                                        <p className={"profile__menu-block-mobile__chats-element-subtext--lvl"}>
                                            Владелец
                                        </p>
                                    </p>
                                </aside>
                            </li>

                            <li className={"profile__menu-block-mobile__chats-element"}>
                                <svg className={"profile__menu-block-mobile__chats-element-backsvg"}
                                     width="810" viewBox="0 0 647 152" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M16 0.5H631C639.56 0.50001 646.5 7.43959 646.5 16V75.5H0.5V16L0.504883 15.5996C0.717246 7.22424 7.57345 0.5 16 0.5Z"
                                        fill="#10151B" stroke="#182C43"/>
                                    <mask id="path-2-inside-1_0_1" fill="white">
                                        <path d="M0 76H324V152H16C7.16343 152 0 144.837 0 136V76Z"/>
                                    </mask>
                                    <path d="M0 76H324V152H16C7.16343 152 0 144.837 0 136V76Z" fill="#10151B"/>
                                    <path
                                        d="M0 76H324H0ZM325 153H16C6.61116 153 -1 145.389 -1 136H1C1 144.284 7.71573 151 16 151H323L325 153ZM16 153C6.61116 153 -1 145.389 -1 136V76H1V136C1 144.284 7.71573 151 16 151V153ZM325 76V153L323 151V76H325Z"
                                        fill="#182C43" mask="url(#path-2-inside-1_0_1)"/>
                                    <mask id="path-4-inside-2_0_1" fill="white">
                                        <path d="M324 76H647V136C647 144.837 639.837 152 631 152H324V76Z"/>
                                    </mask>
                                    <path d="M324 76H647V136C647 144.837 639.837 152 631 152H324V76Z" fill="#10151B"/>
                                    <path
                                        d="M324 76H647H324ZM648 136C648 145.389 640.389 153 631 153H324V151H631C639.284 151 646 144.284 646 136H648ZM324 152V76V152ZM648 76V136C648 145.389 640.389 153 631 153V151C639.284 151 646 144.284 646 136V76H648Z"
                                        fill="#182C43" mask="url(#path-4-inside-2_0_1)"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__chats-element-title"}>
                                    <img className={"profile__menu-block-mobile__chats-element-title-avatar"}
                                         src={catImg}/>

                                    <p className={"profile__menu-block-mobile__chats-element-text"}>
                                        Название чата:
                                        <p className={"profile__menu-block-mobile__chats-element-subtext"}>
                                            Мемы про котов
                                        </p>
                                    </p>

                                    <div className={"profile__menu-block-mobile__chats-element-title-button"}>
                                        <svg width="70" viewBox="0 0 56 56" fill="none"
                                             xmlns="http://www.w3.org/2000/svg">
                                            <rect width="56" height="56" rx="8" fill="#121C28"/>
                                            <path
                                                d="M35.833 22.0072C35.7338 21.993 35.6347 21.993 35.5355 22.0072C33.3397 21.9363 31.5972 20.1372 31.5972 17.9272C31.5972 15.6747 33.4247 13.833 35.6913 13.833C37.9438 13.833 39.7855 15.6605 39.7855 17.9272C39.7713 20.1372 38.0288 21.9363 35.833 22.0072Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M40.4549 31.8256C38.8682 32.8881 36.644 33.2847 34.5899 33.0156C35.1282 31.8539 35.4115 30.5647 35.4257 29.2047C35.4257 27.7881 35.114 26.4422 34.519 25.2664C36.6157 24.9831 38.8399 25.3797 40.4407 26.4422C42.679 27.9156 42.679 30.3381 40.4549 31.8256Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M20.1236 22.0072C20.2228 21.993 20.322 21.993 20.4211 22.0072C22.617 21.9363 24.3595 20.1372 24.3595 17.9272C24.3595 15.6605 22.532 13.833 20.2653 13.833C18.0128 13.833 16.1853 15.6605 16.1853 17.9272C16.1853 20.1372 17.9278 21.9363 20.1236 22.0072Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M20.2808 29.205C20.2808 30.5792 20.5783 31.8825 21.1166 33.0583C19.1191 33.2708 17.0366 32.8458 15.5066 31.84C13.2683 30.3525 13.2683 27.93 15.5066 26.4425C17.0225 25.4225 19.1616 25.0117 21.1733 25.2383C20.5925 26.4283 20.2808 27.7742 20.2808 29.205Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M28.1711 33.4825C28.0577 33.4683 27.9302 33.4683 27.8027 33.4825C25.1961 33.3975 23.1135 31.2583 23.1135 28.6233C23.1277 25.9317 25.2952 23.75 28.0011 23.75C30.6927 23.75 32.8744 25.9317 32.8744 28.6233C32.8602 31.2583 30.7919 33.3975 28.1711 33.4825Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M23.567 36.4162C21.4279 37.847 21.4279 40.1987 23.567 41.6154C26.0037 43.2445 29.9987 43.2445 32.4354 41.6154C34.5745 40.1845 34.5745 37.8329 32.4354 36.4162C30.0129 34.787 26.0179 34.787 23.567 36.4162Z"
                                                fill="#56A0F6"/>
                                        </svg>

                                        <svg width="70" viewBox="0 0 56 56" fill="none"
                                             xmlns="http://www.w3.org/2000/svg">
                                            <rect width="56" height="56" rx="8" fill="#121C28"/>
                                            <path
                                                d="M39.4749 25.0633C36.9108 25.0633 35.8624 23.25 37.1374 21.0258C37.8741 19.7367 37.4349 18.0933 36.1458 17.3567L33.6949 15.9542C32.5758 15.2883 31.1308 15.685 30.4649 16.8042L30.3091 17.0733C29.0341 19.2975 26.9374 19.2975 25.6483 17.0733L25.4924 16.8042C24.8549 15.685 23.4099 15.2883 22.2908 15.9542L19.8399 17.3567C18.5508 18.0933 18.1116 19.7508 18.8483 21.04C20.1374 23.25 19.0891 25.0633 16.5249 25.0633C15.0516 25.0633 13.8333 26.2675 13.8333 27.755V30.2483C13.8333 31.7217 15.0374 32.94 16.5249 32.94C19.0891 32.94 20.1374 34.7533 18.8483 36.9775C18.1116 38.2667 18.5508 39.91 19.8399 40.6467L22.2908 42.0492C23.4099 42.715 24.8549 42.3183 25.5208 41.1992L25.6766 40.93C26.9516 38.7058 29.0483 38.7058 30.3374 40.93L30.4933 41.1992C31.1591 42.3183 32.6041 42.715 33.7233 42.0492L36.1741 40.6467C37.4633 39.91 37.9024 38.2525 37.1658 36.9775C35.8766 34.7533 36.9249 32.94 39.4891 32.94C40.9624 32.94 42.1808 31.7358 42.1808 30.2483V27.755C42.1666 26.2817 40.9624 25.0633 39.4749 25.0633ZM27.9999 33.6058C25.4641 33.6058 23.3958 31.5375 23.3958 29.0017C23.3958 26.4658 25.4641 24.3975 27.9999 24.3975C30.5358 24.3975 32.6041 26.4658 32.6041 29.0017C32.6041 31.5375 30.5358 33.6058 27.9999 33.6058Z"
                                                fill="#56A0F6"/>
                                        </svg>
                                    </div>
                                </aside>

                                <aside className={"profile__menu-block-mobile__chats-element-members"}>
                                    <p className={"profile__menu-block-mobile__chats-element-text--members"}>
                                        Количество участников
                                        <p className={"profile__menu-block-mobile__chats-element-subtext--members"}>
                                            23
                                        </p>
                                    </p>
                                </aside>

                                <aside className={"profile__menu-block-mobile__chats-element-lvl"}>
                                    <p className={"profile__menu-block-mobile__chats-element-text--lvl"}>
                                        Уровень админ-прав
                                        <p className={"profile__menu-block-mobile__chats-element-subtext--lvl"}>
                                            Владелец
                                        </p>
                                    </p>
                                </aside>
                            </li>

                            <li className={"profile__menu-block-mobile__chats-element"}>
                                <svg className={"profile__menu-block-mobile__chats-element-backsvg"}
                                     width="810" viewBox="0 0 647 152" fill="none"
                                     xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M16 0.5H631C639.56 0.50001 646.5 7.43959 646.5 16V75.5H0.5V16L0.504883 15.5996C0.717246 7.22424 7.57345 0.5 16 0.5Z"
                                        fill="#10151B" stroke="#182C43"/>
                                    <mask id="path-2-inside-1_0_1" fill="white">
                                        <path d="M0 76H324V152H16C7.16343 152 0 144.837 0 136V76Z"/>
                                    </mask>
                                    <path d="M0 76H324V152H16C7.16343 152 0 144.837 0 136V76Z" fill="#10151B"/>
                                    <path
                                        d="M0 76H324H0ZM325 153H16C6.61116 153 -1 145.389 -1 136H1C1 144.284 7.71573 151 16 151H323L325 153ZM16 153C6.61116 153 -1 145.389 -1 136V76H1V136C1 144.284 7.71573 151 16 151V153ZM325 76V153L323 151V76H325Z"
                                        fill="#182C43" mask="url(#path-2-inside-1_0_1)"/>
                                    <mask id="path-4-inside-2_0_1" fill="white">
                                        <path d="M324 76H647V136C647 144.837 639.837 152 631 152H324V76Z"/>
                                    </mask>
                                    <path d="M324 76H647V136C647 144.837 639.837 152 631 152H324V76Z" fill="#10151B"/>
                                    <path
                                        d="M324 76H647H324ZM648 136C648 145.389 640.389 153 631 153H324V151H631C639.284 151 646 144.284 646 136H648ZM324 152V76V152ZM648 76V136C648 145.389 640.389 153 631 153V151C639.284 151 646 144.284 646 136V76H648Z"
                                        fill="#182C43" mask="url(#path-4-inside-2_0_1)"/>
                                </svg>

                                <aside className={"profile__menu-block-mobile__chats-element-title"}>
                                    <img className={"profile__menu-block-mobile__chats-element-title-avatar"}
                                         src={catImg}/>

                                    <p className={"profile__menu-block-mobile__chats-element-text"}>
                                        Название чата:
                                        <p className={"profile__menu-block-mobile__chats-element-subtext"}>
                                            Мемы про котов
                                        </p>
                                    </p>

                                    <div className={"profile__menu-block-mobile__chats-element-title-button"}>
                                        <svg width="70" viewBox="0 0 56 56" fill="none"
                                             xmlns="http://www.w3.org/2000/svg">
                                            <rect width="56" height="56" rx="8" fill="#121C28"/>
                                            <path
                                                d="M35.833 22.0072C35.7338 21.993 35.6347 21.993 35.5355 22.0072C33.3397 21.9363 31.5972 20.1372 31.5972 17.9272C31.5972 15.6747 33.4247 13.833 35.6913 13.833C37.9438 13.833 39.7855 15.6605 39.7855 17.9272C39.7713 20.1372 38.0288 21.9363 35.833 22.0072Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M40.4549 31.8256C38.8682 32.8881 36.644 33.2847 34.5899 33.0156C35.1282 31.8539 35.4115 30.5647 35.4257 29.2047C35.4257 27.7881 35.114 26.4422 34.519 25.2664C36.6157 24.9831 38.8399 25.3797 40.4407 26.4422C42.679 27.9156 42.679 30.3381 40.4549 31.8256Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M20.1236 22.0072C20.2228 21.993 20.322 21.993 20.4211 22.0072C22.617 21.9363 24.3595 20.1372 24.3595 17.9272C24.3595 15.6605 22.532 13.833 20.2653 13.833C18.0128 13.833 16.1853 15.6605 16.1853 17.9272C16.1853 20.1372 17.9278 21.9363 20.1236 22.0072Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M20.2808 29.205C20.2808 30.5792 20.5783 31.8825 21.1166 33.0583C19.1191 33.2708 17.0366 32.8458 15.5066 31.84C13.2683 30.3525 13.2683 27.93 15.5066 26.4425C17.0225 25.4225 19.1616 25.0117 21.1733 25.2383C20.5925 26.4283 20.2808 27.7742 20.2808 29.205Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M28.1711 33.4825C28.0577 33.4683 27.9302 33.4683 27.8027 33.4825C25.1961 33.3975 23.1135 31.2583 23.1135 28.6233C23.1277 25.9317 25.2952 23.75 28.0011 23.75C30.6927 23.75 32.8744 25.9317 32.8744 28.6233C32.8602 31.2583 30.7919 33.3975 28.1711 33.4825Z"
                                                fill="#56A0F6"/>
                                            <path
                                                d="M23.567 36.4162C21.4279 37.847 21.4279 40.1987 23.567 41.6154C26.0037 43.2445 29.9987 43.2445 32.4354 41.6154C34.5745 40.1845 34.5745 37.8329 32.4354 36.4162C30.0129 34.787 26.0179 34.787 23.567 36.4162Z"
                                                fill="#56A0F6"/>
                                        </svg>

                                        <svg width="70" viewBox="0 0 56 56" fill="none"
                                             xmlns="http://www.w3.org/2000/svg">
                                            <rect width="56" height="56" rx="8" fill="#121C28"/>
                                            <path
                                                d="M39.4749 25.0633C36.9108 25.0633 35.8624 23.25 37.1374 21.0258C37.8741 19.7367 37.4349 18.0933 36.1458 17.3567L33.6949 15.9542C32.5758 15.2883 31.1308 15.685 30.4649 16.8042L30.3091 17.0733C29.0341 19.2975 26.9374 19.2975 25.6483 17.0733L25.4924 16.8042C24.8549 15.685 23.4099 15.2883 22.2908 15.9542L19.8399 17.3567C18.5508 18.0933 18.1116 19.7508 18.8483 21.04C20.1374 23.25 19.0891 25.0633 16.5249 25.0633C15.0516 25.0633 13.8333 26.2675 13.8333 27.755V30.2483C13.8333 31.7217 15.0374 32.94 16.5249 32.94C19.0891 32.94 20.1374 34.7533 18.8483 36.9775C18.1116 38.2667 18.5508 39.91 19.8399 40.6467L22.2908 42.0492C23.4099 42.715 24.8549 42.3183 25.5208 41.1992L25.6766 40.93C26.9516 38.7058 29.0483 38.7058 30.3374 40.93L30.4933 41.1992C31.1591 42.3183 32.6041 42.715 33.7233 42.0492L36.1741 40.6467C37.4633 39.91 37.9024 38.2525 37.1658 36.9775C35.8766 34.7533 36.9249 32.94 39.4891 32.94C40.9624 32.94 42.1808 31.7358 42.1808 30.2483V27.755C42.1666 26.2817 40.9624 25.0633 39.4749 25.0633ZM27.9999 33.6058C25.4641 33.6058 23.3958 31.5375 23.3958 29.0017C23.3958 26.4658 25.4641 24.3975 27.9999 24.3975C30.5358 24.3975 32.6041 26.4658 32.6041 29.0017C32.6041 31.5375 30.5358 33.6058 27.9999 33.6058Z"
                                                fill="#56A0F6"/>
                                        </svg>
                                    </div>
                                </aside>

                                <aside className={"profile__menu-block-mobile__chats-element-members"}>
                                    <p className={"profile__menu-block-mobile__chats-element-text--members"}>
                                        Количество участников
                                        <p className={"profile__menu-block-mobile__chats-element-subtext--members"}>
                                            23
                                        </p>
                                    </p>
                                </aside>

                                <aside className={"profile__menu-block-mobile__chats-element-lvl"}>
                                    <p className={"profile__menu-block-mobile__chats-element-text--lvl"}>
                                        Уровень админ-прав
                                        <p className={"profile__menu-block-mobile__chats-element-subtext--lvl"}>
                                            Владелец
                                        </p>
                                    </p>
                                </aside>
                            </li>
                        </ul>
                    </nav>
                </article>

                <article className={"profile__menu"}>
                    <article className={"profile__menu-block"}>
                        <svg className={"profile__menu-block-all"}
                             viewBox="0 0 1043 222" fill="none"
                             xmlns="http://www.w3.org/2000/svg">
                            <path fill-rule="evenodd" clip-rule="evenodd"
                                  d="M42.0004 2C19.909 2 2.00037 19.9086 2.00037 42L2.00049 179.5C2.00049 201.591 19.9091 219.5 42.0005 219.5H1001C1023.09 219.5 1041 201.591 1041 179.5L1041 42C1041 19.9086 1023.09 2 1001 2H669.931C660.016 2 652.099 10.063 650.715 19.8807C641.782 83.2505 587.334 132 521.499 132C455.665 132 401.218 83.2505 392.285 19.8807C390.901 10.063 382.984 2 373.069 2H42.0004Z"
                                  fill="#10151B"/>
                            <path
                                d="M373.069 1C383.564 1 391.833 9.51556 393.275 19.7412C402.139 82.6244 456.17 131 521.499 131C586.828 131 640.861 82.6244 649.725 19.7412C651.166 9.5156 659.436 1.00007 669.931 1H1001C1023.64 1 1042 19.3563 1042 42L1042 179.5L1041.99 180.559C1041.43 202.713 1023.29 220.5 1001 220.5H42.0004C19.3568 220.5 1.00037 202.144 1.00037 179.5V42L1.01404 40.9414C1.57553 18.787 19.7106 1 42.0004 1H373.069Z"
                                stroke="#121C28" stroke-width="2"/>
                        </svg>

                        <p className={"profile__menu-block-name"}>
                            <p className={"profile__menu-block-name-first"}>Даниил</p>
                            <p className={"profile__menu-block-name-last"}>Климушкин</p>
                        </p>

                        <aside className={"profile__menu-block-lvl"}>
                            <svg className={"profile__menu-block-lvl__exp"}
                                 viewBox="0 0 56 56" fill="none"
                                 xmlns="http://www.w3.org/2000/svg">
                                <foreignObject x="-5.5" y="-5.5" width="67" height="67">
                                    <div xmlns="http://www.w3.org/1999/xhtml"></div>
                                </foreignObject>
                                <rect data-figma-bg-blur-radius="5.5" x="1" y="1" width="54" height="54" rx="27"
                                      fill="#0076FF" fill-opacity="0.4" stroke="#56A0F6" stroke-width="2"/>
                                <defs>
                                    <clipPath id="bgblur_0_803_182_clip_path" transform="translate(5.5 5.5)">
                                        <rect x="1" y="1" width="54" height="54" rx="27"/>
                                    </clipPath>
                                </defs>
                            </svg>
                            <p className={"profile__menu-block-lvl__exp-text"}>3</p>


                            <img className={"profile__menu-block-lvl__avatar"}
                                 src={profileImg}/>
                        </aside>

                        <aside className={"profile__menu-block-chats-mini"}>
                            <svg className={"profile__menu-block-mini-svg"}
                                 viewBox="0 0 373 77" fill="none"
                                 xmlns="http://www.w3.org/2000/svg">
                                <path
                                    d="M335.442 0.5C348.586 0.5 359.242 11.1558 359.242 24.2998C359.242 33.5449 361.494 42.6508 365.804 50.8301L370.445 59.6396C374.48 67.2977 368.927 76.5 360.271 76.5H102C92.8873 76.5 85.5 69.1127 85.5 60V17C85.5 7.8873 92.8873 0.5 102 0.5H335.442Z"
                                    fill="#10151B" stroke="#182C43"/>
                                <rect x="0.5" y="1.5" width="74" height="74" rx="15.5" fill="#10151B" stroke="#182C43"/>
                                <path
                                    d="M48.6875 29.7375C48.3312 24.9875 44.4125 21.1875 39.5437 21.1875H29.45C24.3437 21.1875 20.1875 25.3438 20.1875 30.3313V47.3125C20.1875 47.7875 20.425 48.1437 20.9 48.3813C21.0187 48.5 21.2562 48.5 21.375 48.5C21.6125 48.5 21.9687 48.3812 22.2062 48.2625C23.75 46.9562 25.5312 45.8875 27.3125 45.0562V55.625C27.3125 56.1 27.55 56.4562 28.025 56.6937C28.1437 56.8125 28.3812 56.8125 28.5 56.8125C28.7375 56.8125 29.0937 56.6937 29.3312 56.575C32.775 53.4875 37.2875 51.825 41.9187 51.825H46.6687C51.775 51.825 55.9312 47.6688 55.9312 42.6812V38.6437C55.8125 34.3687 52.725 30.6875 48.6875 29.7375ZM53.4375 42.6812C53.4375 46.4813 50.35 49.45 46.55 49.45H41.8C37.525 49.45 33.25 50.7563 29.6875 53.25V44.225C31.35 43.75 33.0125 43.5125 34.7937 43.5125H39.5437C44.65 43.5125 48.8062 39.3563 48.8062 34.3688V32.2312C51.5375 33.0625 53.5562 35.675 53.5562 38.6437V42.6812H53.4375Z"
                                    fill="#152537"/>
                            </svg>

                            <article className={"profile__menu-block-mini-text"}>
                                <p className={"profile__menu-block-mini-text-first"}>Количество бесед с ботом:</p>
                                <p className={"profile__menu-block-mini-text-second"}>4</p>
                            </article>
                        </aside>

                        <aside className={"profile__menu-block-reput-mini"}>
                            <svg className={"profile__menu-block-mini-svg"}
                                 viewBox="0 0 373 77" fill="none"
                                 xmlns="http://www.w3.org/2000/svg">
                                <path
                                    d="M335.442 76.5C348.586 76.5 359.242 65.8442 359.242 52.7002C359.242 43.4551 361.494 34.3492 365.804 26.1699L370.445 17.3604C374.48 9.70226 368.927 0.5 360.271 0.5H102C92.8873 0.5 85.5 7.8873 85.5 17V60C85.5 69.1127 92.8873 76.5 102 76.5H335.442Z"
                                    fill="#10151B" stroke="#182C43"/>
                                <rect x="0.5" y="1.5" width="74" height="74" rx="15.5" fill="#10151B" stroke="#182C43"/>
                                <path
                                    d="M49.6016 27.3953L28.0783 48.9187C27.2717 49.7253 25.915 49.6153 25.255 48.662C22.9817 45.3437 21.6433 41.4203 21.6433 37.387V29.3387C21.6433 27.8353 22.78 26.1303 24.1733 25.562L34.3849 21.382C36.6949 20.4287 39.2616 20.4287 41.5716 21.382L48.9966 24.407C50.2066 24.902 50.5183 26.4787 49.6016 27.3953Z"
                                    fill="#152537"/>
                                <path
                                    d="M51.3284 29.9099C52.5201 28.9016 54.3351 29.7632 54.3351 31.3216V37.3899C54.3351 46.3549 47.8267 54.7516 38.9351 57.2082C38.3301 57.3732 37.6701 57.3732 37.0467 57.2082C34.4434 56.4749 32.0234 55.2466 29.9518 53.6332C29.0718 52.9549 28.9801 51.6716 29.7501 50.8832C33.7468 46.7949 45.4434 34.8782 51.3284 29.9099Z"
                                    fill="#152537"/>
                            </svg>

                            <article className={"profile__menu-block-mini-text"}>
                                <p className={"profile__menu-block-mini-text-first"}>Ваша репутация:</p>
                                <p className={"profile__menu-block-mini-text-second"}>0 (#199470)</p>
                            </article>
                        </aside>

                        <aside className={"profile__menu-block-premium-mini"}>
                            {/*<svg className={"profile__menu-block-mini-svg--premium"}*/}
                            <svg className={"profile__menu-block-mini-svg"}
                                 viewBox="0 0 371 77" fill="none"
                                 xmlns="http://www.w3.org/2000/svg">
                                <path className={"profile__menu-block-mini-svg-textbox"}
                                      d="M38.8252 0.5C26.7715 0.5 17 10.2715 17 22.3252C17 32.764 13.861 42.9616 7.99121 51.5938L3.27246 58.5332C-1.91926 66.1681 3.54939 76.5 12.7822 76.5H268.5C277.613 76.5 285 69.1127 285 60V17C285 7.8873 277.613 0.5 268.5 0.5H38.8252Z"
                                />
                                <rect x="296.5" y="1.5" width="74" height="74" rx="15.5" fill="#10151B"
                                      stroke="#182C43"/>
                                <path className={"profile__menu-block-mini-svg-icon"}
                                      d="M353.167 26.9435V45.3052C353.167 50.5952 348.874 54.8885 343.584 54.8885H324.417C323.536 54.8885 322.692 54.7735 321.868 54.5435C320.68 54.2177 320.296 52.7035 321.178 51.8219L341.552 31.4477C341.974 31.026 342.606 30.9302 343.201 31.0452C343.814 31.1602 344.485 30.9877 344.964 30.5277L349.89 25.5827C351.691 23.781 353.167 24.3752 353.167 26.9435Z"
                                      fill="#152537"/>
                                <path className={"profile__menu-block-mini-svg-icon"}
                                      d="M339.06 30.1061L318.992 50.1735C318.072 51.0935 316.539 50.8635 315.926 49.7135C315.217 48.4102 314.833 46.896 314.833 45.3052V26.9436C314.833 24.3753 316.309 23.7811 318.111 25.5828L323.056 30.5469C323.803 31.2753 325.03 31.2753 325.777 30.5469L332.639 23.6661C333.387 22.9186 334.613 22.9186 335.361 23.6661L339.079 27.3844C339.807 28.1319 339.807 29.3586 339.06 30.1061Z"
                                      fill="#152537"/>
                            </svg>

                            {/*<svg className={"profile__menu-block-mini-text--right--premium"}*/}
                            <article className={"profile__menu-block-mini-text--right"}>
                                <p className={"profile__menu-block-mini-text-first"}>Premium</p>
                                <p className={"profile__menu-block-mini-text-second"}>нет</p>
                            </article>
                        </aside>

                        <aside className={"profile__menu-block-leags-mini--legend"}>
                            <svg className={"profile__menu-block-mini-svg"}
                                 viewBox="0 0 371 77" fill="none"
                                 xmlns="http://www.w3.org/2000/svg">
                                <path className={"profile__menu-block-mini-svg-leags-textbox"}
                                      d="M38.8252 76.5C26.7715 76.5 17 66.7285 17 54.6748C17 44.236 13.861 34.0384 7.99121 25.4062L3.27246 18.4668C-1.91926 10.8319 3.54939 0.500023 12.7822 0.5H268.5C277.613 0.5 285 7.8873 285 17V60C285 69.1127 277.613 76.5 268.5 76.5H38.8252Z"
                                      stroke="#914400"/>
                                <rect x="296.5" y="1.5" width="74" height="74" rx="15.5" stroke="#914400"/>
                                <path className={"profile__menu-block-mini-svg-leags-icon"}
                                      d="M346.666 24.0449C346.693 22.7575 346.644 21.9441 346.644 21.9441L334.064 21.9346H334H333.936L321.354 21.9441C321.354 21.9441 321.307 22.7575 321.334 24.0449H313V25.4192C313 25.7329 313.053 33.1326 317.62 37.1862C319.525 38.8769 321.902 39.727 324.703 39.7284C325.127 39.7284 325.563 39.6998 326.004 39.6618C327.596 41.8414 329.434 43.3678 331.503 44.1282V50.1645H325.431V53.9452H323.425V56.065H333.936H334.064H344.575V53.9465H342.568V50.1659H336.496V44.1296C338.563 43.3691 340.403 41.8427 341.995 39.6632C342.439 39.7012 342.874 39.7284 343.298 39.7284C346.098 39.7256 348.475 38.8769 350.38 37.1848C354.947 33.1312 355 25.7315 355 25.4178V24.0449H346.666ZM319.453 35.137C316.844 32.8284 316.073 28.8766 315.845 26.7935H321.492C321.731 29.3886 322.293 32.622 323.59 35.4643C323.827 35.9857 324.077 36.48 324.332 36.9635C322.386 36.8888 320.749 36.2818 319.453 35.137ZM348.547 35.137C347.253 36.2831 345.614 36.8888 343.669 36.9635C343.924 36.4814 344.174 35.9857 344.412 35.4643C345.709 32.622 346.271 29.3886 346.508 26.7935H352.155C351.927 28.8753 351.157 32.827 348.547 35.137Z"
                                      fill="#914400"/>
                            </svg>

                            <article className={"profile__menu-block-mini-text--right"}>
                                <p className={"profile__menu-block-mini-text-first"}>Ваша лига:</p>
                                <p className={"profile__menu-block-mini-text-second--leags"}>Легенда</p>
                            </article>
                        </aside>
                    </article>

                    <article className={"profile__chats-block"}>
                        <nav>
                            <ul className={"profile__chats-block-elements"}>
                                <li className={"profile__chats-block-element--premium"}>
                                    <div className={"profile__chats-block-element__title"}>
                                        <img className={"profile__chats-block-element__title-avatar"}
                                             src={catImg}/>

                                        <aside className={"profile__chats-block-element__title-text"}>
                                            <p className={"profile__chats-block-element__title-text-first"}>
                                                Название чата
                                            </p>
                                            <p className={"profile__chats-block-element__title-text-second"}>
                                                Мемы про котов
                                            </p>
                                        </aside>

                                        <aside className={"profile__chats-block-element__title-svg"}>
                                            <svg className={"profile__chats-block-element__title-svg-people"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M25.5291 15.77C25.4591 15.76 25.3891 15.76 25.3191 15.77C23.7691 15.72 22.5391 14.45 22.5391 12.89C22.5391 11.3 23.8291 10 25.4291 10C27.0191 10 28.3191 11.29 28.3191 12.89C28.3091 14.45 27.0791 15.72 25.5291 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M28.7916 22.7004C27.6716 23.4504 26.1016 23.7304 24.6516 23.5404C25.0316 22.7204 25.2316 21.8104 25.2416 20.8504C25.2416 19.8504 25.0216 18.9004 24.6016 18.0704C26.0816 17.8704 27.6516 18.1504 28.7816 18.9004C30.3616 19.9404 30.3616 21.6504 28.7916 22.7004Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.4402 15.77C14.5102 15.76 14.5802 15.76 14.6502 15.77C16.2002 15.72 17.4302 14.45 17.4302 12.89C17.4302 11.29 16.1402 10 14.5402 10C12.9502 10 11.6602 11.29 11.6602 12.89C11.6602 14.45 12.8902 15.72 14.4402 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.5511 20.8506C14.5511 21.8206 14.7611 22.7406 15.1411 23.5706C13.7311 23.7206 12.2611 23.4206 11.1811 22.7106C9.60109 21.6606 9.60109 19.9506 11.1811 18.9006C12.2511 18.1806 13.7611 17.8906 15.1811 18.0506C14.7711 18.8906 14.5511 19.8406 14.5511 20.8506Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M20.1208 23.87C20.0408 23.86 19.9508 23.86 19.8608 23.87C18.0208 23.81 16.5508 22.3 16.5508 20.44C16.5608 18.54 18.0908 17 20.0008 17C21.9008 17 23.4408 18.54 23.4408 20.44C23.4308 22.3 21.9708 23.81 20.1208 23.87Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M16.8708 25.9406C15.3608 26.9506 15.3608 28.6106 16.8708 29.6106C18.5908 30.7606 21.4108 30.7606 23.1308 29.6106C24.6408 28.6006 24.6408 26.9406 23.1308 25.9406C21.4208 24.7906 18.6008 24.7906 16.8708 25.9406Z"
                                                    fill="#56A0F6"/>
                                            </svg>

                                            <svg className={"profile__chats-block-element__title-svg-setting"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M28.1 17.2214C26.29 17.2214 25.55 15.9414 26.45 14.3714C26.97 13.4614 26.66 12.3014 25.75 11.7814L24.02 10.7914C23.23 10.3214 22.21 10.6014 21.74 11.3914L21.63 11.5814C20.73 13.1514 19.25 13.1514 18.34 11.5814L18.23 11.3914C17.78 10.6014 16.76 10.3214 15.97 10.7914L14.24 11.7814C13.33 12.3014 13.02 13.4714 13.54 14.3814C14.45 15.9414 13.71 17.2214 11.9 17.2214C10.86 17.2214 10 18.0714 10 19.1214V20.8814C10 21.9214 10.85 22.7814 11.9 22.7814C13.71 22.7814 14.45 24.0614 13.54 25.6314C13.02 26.5414 13.33 27.7014 14.24 28.2214L15.97 29.2114C16.76 29.6814 17.78 29.4014 18.25 28.6114L18.36 28.4214C19.26 26.8514 20.74 26.8514 21.65 28.4214L21.76 28.6114C22.23 29.4014 23.25 29.6814 24.04 29.2114L25.77 28.2214C26.68 27.7014 26.99 26.5314 26.47 25.6314C25.56 24.0614 26.3 22.7814 28.11 22.7814C29.15 22.7814 30.01 21.9314 30.01 20.8814V19.1214C30 18.0814 29.15 17.2214 28.1 17.2214ZM20 23.2514C18.21 23.2514 16.75 21.7914 16.75 20.0014C16.75 18.2114 18.21 16.7514 20 16.7514C21.79 16.7514 23.25 18.2114 23.25 20.0014C23.25 21.7914 21.79 23.2514 20 23.2514Z"
                                                    fill="#56A0F6"/>
                                            </svg>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__users"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Участников:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>23</p>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__owner"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Права:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>Владелец</p>
                                        </aside>
                                    </div>
                                </li>

                                <li className={"profile__chats-block-element"}>
                                    <div className={"profile__chats-block-element__title"}>
                                        <img className={"profile__chats-block-element__title-avatar"}
                                             src={catImg}/>

                                        <aside className={"profile__chats-block-element__title-text"}>
                                            <p className={"profile__chats-block-element__title-text-first"}>
                                                Название чата
                                            </p>
                                            <p className={"profile__chats-block-element__title-text-second"}>
                                                Мемы про котов
                                            </p>
                                        </aside>

                                        <aside className={"profile__chats-block-element__title-svg"}>
                                            <svg className={"profile__chats-block-element__title-svg-people"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M25.5291 15.77C25.4591 15.76 25.3891 15.76 25.3191 15.77C23.7691 15.72 22.5391 14.45 22.5391 12.89C22.5391 11.3 23.8291 10 25.4291 10C27.0191 10 28.3191 11.29 28.3191 12.89C28.3091 14.45 27.0791 15.72 25.5291 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M28.7916 22.7004C27.6716 23.4504 26.1016 23.7304 24.6516 23.5404C25.0316 22.7204 25.2316 21.8104 25.2416 20.8504C25.2416 19.8504 25.0216 18.9004 24.6016 18.0704C26.0816 17.8704 27.6516 18.1504 28.7816 18.9004C30.3616 19.9404 30.3616 21.6504 28.7916 22.7004Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.4402 15.77C14.5102 15.76 14.5802 15.76 14.6502 15.77C16.2002 15.72 17.4302 14.45 17.4302 12.89C17.4302 11.29 16.1402 10 14.5402 10C12.9502 10 11.6602 11.29 11.6602 12.89C11.6602 14.45 12.8902 15.72 14.4402 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.5511 20.8506C14.5511 21.8206 14.7611 22.7406 15.1411 23.5706C13.7311 23.7206 12.2611 23.4206 11.1811 22.7106C9.60109 21.6606 9.60109 19.9506 11.1811 18.9006C12.2511 18.1806 13.7611 17.8906 15.1811 18.0506C14.7711 18.8906 14.5511 19.8406 14.5511 20.8506Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M20.1208 23.87C20.0408 23.86 19.9508 23.86 19.8608 23.87C18.0208 23.81 16.5508 22.3 16.5508 20.44C16.5608 18.54 18.0908 17 20.0008 17C21.9008 17 23.4408 18.54 23.4408 20.44C23.4308 22.3 21.9708 23.81 20.1208 23.87Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M16.8708 25.9406C15.3608 26.9506 15.3608 28.6106 16.8708 29.6106C18.5908 30.7606 21.4108 30.7606 23.1308 29.6106C24.6408 28.6006 24.6408 26.9406 23.1308 25.9406C21.4208 24.7906 18.6008 24.7906 16.8708 25.9406Z"
                                                    fill="#56A0F6"/>
                                            </svg>

                                            <svg className={"profile__chats-block-element__title-svg-setting"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M28.1 17.2214C26.29 17.2214 25.55 15.9414 26.45 14.3714C26.97 13.4614 26.66 12.3014 25.75 11.7814L24.02 10.7914C23.23 10.3214 22.21 10.6014 21.74 11.3914L21.63 11.5814C20.73 13.1514 19.25 13.1514 18.34 11.5814L18.23 11.3914C17.78 10.6014 16.76 10.3214 15.97 10.7914L14.24 11.7814C13.33 12.3014 13.02 13.4714 13.54 14.3814C14.45 15.9414 13.71 17.2214 11.9 17.2214C10.86 17.2214 10 18.0714 10 19.1214V20.8814C10 21.9214 10.85 22.7814 11.9 22.7814C13.71 22.7814 14.45 24.0614 13.54 25.6314C13.02 26.5414 13.33 27.7014 14.24 28.2214L15.97 29.2114C16.76 29.6814 17.78 29.4014 18.25 28.6114L18.36 28.4214C19.26 26.8514 20.74 26.8514 21.65 28.4214L21.76 28.6114C22.23 29.4014 23.25 29.6814 24.04 29.2114L25.77 28.2214C26.68 27.7014 26.99 26.5314 26.47 25.6314C25.56 24.0614 26.3 22.7814 28.11 22.7814C29.15 22.7814 30.01 21.9314 30.01 20.8814V19.1214C30 18.0814 29.15 17.2214 28.1 17.2214ZM20 23.2514C18.21 23.2514 16.75 21.7914 16.75 20.0014C16.75 18.2114 18.21 16.7514 20 16.7514C21.79 16.7514 23.25 18.2114 23.25 20.0014C23.25 21.7914 21.79 23.2514 20 23.2514Z"
                                                    fill="#56A0F6"/>
                                            </svg>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__users"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Участников:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>23</p>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__owner"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Права:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>Владелец</p>
                                        </aside>
                                    </div>
                                </li>

                                <li className={"profile__chats-block-element"}>
                                    <div className={"profile__chats-block-element__title"}>
                                        <img className={"profile__chats-block-element__title-avatar"}
                                             src={catImg}/>

                                        <aside className={"profile__chats-block-element__title-text"}>
                                            <p className={"profile__chats-block-element__title-text-first"}>
                                                Название чата
                                            </p>
                                            <p className={"profile__chats-block-element__title-text-second"}>
                                                Мемы про котов
                                            </p>
                                        </aside>

                                        <aside className={"profile__chats-block-element__title-svg"}>
                                            <svg className={"profile__chats-block-element__title-svg-people"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M25.5291 15.77C25.4591 15.76 25.3891 15.76 25.3191 15.77C23.7691 15.72 22.5391 14.45 22.5391 12.89C22.5391 11.3 23.8291 10 25.4291 10C27.0191 10 28.3191 11.29 28.3191 12.89C28.3091 14.45 27.0791 15.72 25.5291 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M28.7916 22.7004C27.6716 23.4504 26.1016 23.7304 24.6516 23.5404C25.0316 22.7204 25.2316 21.8104 25.2416 20.8504C25.2416 19.8504 25.0216 18.9004 24.6016 18.0704C26.0816 17.8704 27.6516 18.1504 28.7816 18.9004C30.3616 19.9404 30.3616 21.6504 28.7916 22.7004Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.4402 15.77C14.5102 15.76 14.5802 15.76 14.6502 15.77C16.2002 15.72 17.4302 14.45 17.4302 12.89C17.4302 11.29 16.1402 10 14.5402 10C12.9502 10 11.6602 11.29 11.6602 12.89C11.6602 14.45 12.8902 15.72 14.4402 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.5511 20.8506C14.5511 21.8206 14.7611 22.7406 15.1411 23.5706C13.7311 23.7206 12.2611 23.4206 11.1811 22.7106C9.60109 21.6606 9.60109 19.9506 11.1811 18.9006C12.2511 18.1806 13.7611 17.8906 15.1811 18.0506C14.7711 18.8906 14.5511 19.8406 14.5511 20.8506Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M20.1208 23.87C20.0408 23.86 19.9508 23.86 19.8608 23.87C18.0208 23.81 16.5508 22.3 16.5508 20.44C16.5608 18.54 18.0908 17 20.0008 17C21.9008 17 23.4408 18.54 23.4408 20.44C23.4308 22.3 21.9708 23.81 20.1208 23.87Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M16.8708 25.9406C15.3608 26.9506 15.3608 28.6106 16.8708 29.6106C18.5908 30.7606 21.4108 30.7606 23.1308 29.6106C24.6408 28.6006 24.6408 26.9406 23.1308 25.9406C21.4208 24.7906 18.6008 24.7906 16.8708 25.9406Z"
                                                    fill="#56A0F6"/>
                                            </svg>

                                            <svg className={"profile__chats-block-element__title-svg-setting"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M28.1 17.2214C26.29 17.2214 25.55 15.9414 26.45 14.3714C26.97 13.4614 26.66 12.3014 25.75 11.7814L24.02 10.7914C23.23 10.3214 22.21 10.6014 21.74 11.3914L21.63 11.5814C20.73 13.1514 19.25 13.1514 18.34 11.5814L18.23 11.3914C17.78 10.6014 16.76 10.3214 15.97 10.7914L14.24 11.7814C13.33 12.3014 13.02 13.4714 13.54 14.3814C14.45 15.9414 13.71 17.2214 11.9 17.2214C10.86 17.2214 10 18.0714 10 19.1214V20.8814C10 21.9214 10.85 22.7814 11.9 22.7814C13.71 22.7814 14.45 24.0614 13.54 25.6314C13.02 26.5414 13.33 27.7014 14.24 28.2214L15.97 29.2114C16.76 29.6814 17.78 29.4014 18.25 28.6114L18.36 28.4214C19.26 26.8514 20.74 26.8514 21.65 28.4214L21.76 28.6114C22.23 29.4014 23.25 29.6814 24.04 29.2114L25.77 28.2214C26.68 27.7014 26.99 26.5314 26.47 25.6314C25.56 24.0614 26.3 22.7814 28.11 22.7814C29.15 22.7814 30.01 21.9314 30.01 20.8814V19.1214C30 18.0814 29.15 17.2214 28.1 17.2214ZM20 23.2514C18.21 23.2514 16.75 21.7914 16.75 20.0014C16.75 18.2114 18.21 16.7514 20 16.7514C21.79 16.7514 23.25 18.2114 23.25 20.0014C23.25 21.7914 21.79 23.2514 20 23.2514Z"
                                                    fill="#56A0F6"/>
                                            </svg>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__users"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Участников:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>23</p>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__owner"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Права:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>Владелец</p>
                                        </aside>
                                    </div>
                                </li>

                                <li className={"profile__chats-block-element"}>
                                    <div className={"profile__chats-block-element__title"}>
                                        <img className={"profile__chats-block-element__title-avatar"}
                                             src={catImg}/>

                                        <aside className={"profile__chats-block-element__title-text"}>
                                            <p className={"profile__chats-block-element__title-text-first"}>
                                                Название чата
                                            </p>
                                            <p className={"profile__chats-block-element__title-text-second"}>
                                                Мемы про котов
                                            </p>
                                        </aside>

                                        <aside className={"profile__chats-block-element__title-svg"}>
                                            <svg className={"profile__chats-block-element__title-svg-people"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M25.5291 15.77C25.4591 15.76 25.3891 15.76 25.3191 15.77C23.7691 15.72 22.5391 14.45 22.5391 12.89C22.5391 11.3 23.8291 10 25.4291 10C27.0191 10 28.3191 11.29 28.3191 12.89C28.3091 14.45 27.0791 15.72 25.5291 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M28.7916 22.7004C27.6716 23.4504 26.1016 23.7304 24.6516 23.5404C25.0316 22.7204 25.2316 21.8104 25.2416 20.8504C25.2416 19.8504 25.0216 18.9004 24.6016 18.0704C26.0816 17.8704 27.6516 18.1504 28.7816 18.9004C30.3616 19.9404 30.3616 21.6504 28.7916 22.7004Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.4402 15.77C14.5102 15.76 14.5802 15.76 14.6502 15.77C16.2002 15.72 17.4302 14.45 17.4302 12.89C17.4302 11.29 16.1402 10 14.5402 10C12.9502 10 11.6602 11.29 11.6602 12.89C11.6602 14.45 12.8902 15.72 14.4402 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.5511 20.8506C14.5511 21.8206 14.7611 22.7406 15.1411 23.5706C13.7311 23.7206 12.2611 23.4206 11.1811 22.7106C9.60109 21.6606 9.60109 19.9506 11.1811 18.9006C12.2511 18.1806 13.7611 17.8906 15.1811 18.0506C14.7711 18.8906 14.5511 19.8406 14.5511 20.8506Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M20.1208 23.87C20.0408 23.86 19.9508 23.86 19.8608 23.87C18.0208 23.81 16.5508 22.3 16.5508 20.44C16.5608 18.54 18.0908 17 20.0008 17C21.9008 17 23.4408 18.54 23.4408 20.44C23.4308 22.3 21.9708 23.81 20.1208 23.87Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M16.8708 25.9406C15.3608 26.9506 15.3608 28.6106 16.8708 29.6106C18.5908 30.7606 21.4108 30.7606 23.1308 29.6106C24.6408 28.6006 24.6408 26.9406 23.1308 25.9406C21.4208 24.7906 18.6008 24.7906 16.8708 25.9406Z"
                                                    fill="#56A0F6"/>
                                            </svg>

                                            <svg className={"profile__chats-block-element__title-svg-setting"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M28.1 17.2214C26.29 17.2214 25.55 15.9414 26.45 14.3714C26.97 13.4614 26.66 12.3014 25.75 11.7814L24.02 10.7914C23.23 10.3214 22.21 10.6014 21.74 11.3914L21.63 11.5814C20.73 13.1514 19.25 13.1514 18.34 11.5814L18.23 11.3914C17.78 10.6014 16.76 10.3214 15.97 10.7914L14.24 11.7814C13.33 12.3014 13.02 13.4714 13.54 14.3814C14.45 15.9414 13.71 17.2214 11.9 17.2214C10.86 17.2214 10 18.0714 10 19.1214V20.8814C10 21.9214 10.85 22.7814 11.9 22.7814C13.71 22.7814 14.45 24.0614 13.54 25.6314C13.02 26.5414 13.33 27.7014 14.24 28.2214L15.97 29.2114C16.76 29.6814 17.78 29.4014 18.25 28.6114L18.36 28.4214C19.26 26.8514 20.74 26.8514 21.65 28.4214L21.76 28.6114C22.23 29.4014 23.25 29.6814 24.04 29.2114L25.77 28.2214C26.68 27.7014 26.99 26.5314 26.47 25.6314C25.56 24.0614 26.3 22.7814 28.11 22.7814C29.15 22.7814 30.01 21.9314 30.01 20.8814V19.1214C30 18.0814 29.15 17.2214 28.1 17.2214ZM20 23.2514C18.21 23.2514 16.75 21.7914 16.75 20.0014C16.75 18.2114 18.21 16.7514 20 16.7514C21.79 16.7514 23.25 18.2114 23.25 20.0014C23.25 21.7914 21.79 23.2514 20 23.2514Z"
                                                    fill="#56A0F6"/>
                                            </svg>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__users"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Участников:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>23</p>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__owner"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Права:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>Владелец</p>
                                        </aside>
                                    </div>
                                </li>

                                <li className={"profile__chats-block-element"}>
                                    <div className={"profile__chats-block-element__title"}>
                                        <img className={"profile__chats-block-element__title-avatar"}
                                             src={catImg}/>

                                        <aside className={"profile__chats-block-element__title-text"}>
                                            <p className={"profile__chats-block-element__title-text-first"}>
                                                Название чата
                                            </p>
                                            <p className={"profile__chats-block-element__title-text-second"}>
                                                Мемы про котов
                                            </p>
                                        </aside>

                                        <aside className={"profile__chats-block-element__title-svg"}>
                                            <svg className={"profile__chats-block-element__title-svg-people"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M25.5291 15.77C25.4591 15.76 25.3891 15.76 25.3191 15.77C23.7691 15.72 22.5391 14.45 22.5391 12.89C22.5391 11.3 23.8291 10 25.4291 10C27.0191 10 28.3191 11.29 28.3191 12.89C28.3091 14.45 27.0791 15.72 25.5291 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M28.7916 22.7004C27.6716 23.4504 26.1016 23.7304 24.6516 23.5404C25.0316 22.7204 25.2316 21.8104 25.2416 20.8504C25.2416 19.8504 25.0216 18.9004 24.6016 18.0704C26.0816 17.8704 27.6516 18.1504 28.7816 18.9004C30.3616 19.9404 30.3616 21.6504 28.7916 22.7004Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.4402 15.77C14.5102 15.76 14.5802 15.76 14.6502 15.77C16.2002 15.72 17.4302 14.45 17.4302 12.89C17.4302 11.29 16.1402 10 14.5402 10C12.9502 10 11.6602 11.29 11.6602 12.89C11.6602 14.45 12.8902 15.72 14.4402 15.77Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M14.5511 20.8506C14.5511 21.8206 14.7611 22.7406 15.1411 23.5706C13.7311 23.7206 12.2611 23.4206 11.1811 22.7106C9.60109 21.6606 9.60109 19.9506 11.1811 18.9006C12.2511 18.1806 13.7611 17.8906 15.1811 18.0506C14.7711 18.8906 14.5511 19.8406 14.5511 20.8506Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M20.1208 23.87C20.0408 23.86 19.9508 23.86 19.8608 23.87C18.0208 23.81 16.5508 22.3 16.5508 20.44C16.5608 18.54 18.0908 17 20.0008 17C21.9008 17 23.4408 18.54 23.4408 20.44C23.4308 22.3 21.9708 23.81 20.1208 23.87Z"
                                                    fill="#56A0F6"/>
                                                <path
                                                    d="M16.8708 25.9406C15.3608 26.9506 15.3608 28.6106 16.8708 29.6106C18.5908 30.7606 21.4108 30.7606 23.1308 29.6106C24.6408 28.6006 24.6408 26.9406 23.1308 25.9406C21.4208 24.7906 18.6008 24.7906 16.8708 25.9406Z"
                                                    fill="#56A0F6"/>
                                            </svg>

                                            <svg className={"profile__chats-block-element__title-svg-setting"}
                                                 viewBox="0 0 40 40" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <rect width="40" height="40" rx="8" fill="#121C28"/>
                                                <path
                                                    d="M28.1 17.2214C26.29 17.2214 25.55 15.9414 26.45 14.3714C26.97 13.4614 26.66 12.3014 25.75 11.7814L24.02 10.7914C23.23 10.3214 22.21 10.6014 21.74 11.3914L21.63 11.5814C20.73 13.1514 19.25 13.1514 18.34 11.5814L18.23 11.3914C17.78 10.6014 16.76 10.3214 15.97 10.7914L14.24 11.7814C13.33 12.3014 13.02 13.4714 13.54 14.3814C14.45 15.9414 13.71 17.2214 11.9 17.2214C10.86 17.2214 10 18.0714 10 19.1214V20.8814C10 21.9214 10.85 22.7814 11.9 22.7814C13.71 22.7814 14.45 24.0614 13.54 25.6314C13.02 26.5414 13.33 27.7014 14.24 28.2214L15.97 29.2114C16.76 29.6814 17.78 29.4014 18.25 28.6114L18.36 28.4214C19.26 26.8514 20.74 26.8514 21.65 28.4214L21.76 28.6114C22.23 29.4014 23.25 29.6814 24.04 29.2114L25.77 28.2214C26.68 27.7014 26.99 26.5314 26.47 25.6314C25.56 24.0614 26.3 22.7814 28.11 22.7814C29.15 22.7814 30.01 21.9314 30.01 20.8814V19.1214C30 18.0814 29.15 17.2214 28.1 17.2214ZM20 23.2514C18.21 23.2514 16.75 21.7914 16.75 20.0014C16.75 18.2114 18.21 16.7514 20 16.7514C21.79 16.7514 23.25 18.2114 23.25 20.0014C23.25 21.7914 21.79 23.2514 20 23.2514Z"
                                                    fill="#56A0F6"/>
                                            </svg>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__users"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Участников:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>23</p>
                                        </aside>
                                    </div>

                                    <div className={"profile__chats-block-element__owner"}>
                                        <aside className={"profile__chats-block-element__text"}>
                                            <p className={"profile__chats-block-element__text-first"}>
                                                Права:
                                            </p>
                                            <p className={"profile__chats-block-element__text-second"}>Владелец</p>
                                        </aside>
                                    </div>
                                </li>
                            </ul>
                        </nav>
                    </article>
                </article>
            </>
        </div>
    );
}

export default PersonalAccount;
