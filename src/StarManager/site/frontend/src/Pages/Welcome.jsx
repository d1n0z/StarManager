// react
import React, { useEffect } from 'react';

// css
import "../styles/welcome-page.css";

// js
import { MiniProfile } from "../Components/mini-profile";

import { WelcomeHeader } from "../Components/Welcome/welcome-header";
import { Advantages } from "../Components/Welcome/advantages";
import { Premium } from "../Components/Welcome/premium";

/*
================== Welcome Page====================
import { WelcomeHeader } from "../Components/Welcome/welcome-header";
import { Advantages } from "../Components/Welcome/advantages";
import { Premium } from "../Components/Welcome/premium";
===================================================
*/

import { loadWindowEvent } from "../scripts/WelcomePage/events";


function WelcomePage() {
    useEffect(() => {
        loadWindowEvent();
    }, []);
    return (
        <div className={"welcome"}>
            <MiniProfile></MiniProfile>
            <WelcomeHeader></WelcomeHeader>
            <Advantages></Advantages>
            <Premium></Premium>
        </div>
    );
}

export default WelcomePage;
