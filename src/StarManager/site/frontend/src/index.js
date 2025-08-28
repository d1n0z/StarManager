import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ReactDOM from 'react-dom/client';

// pages
import WelcomePage from "./Pages/Welcome";
import PersonalAccount from "./Pages/PersonalAccount";
import PaymentPage from "./Pages/Payment";
import LeaderBoard from "./Pages/LeaderBoard";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
      <BrowserRouter>
          <Routes>
              <Route path="/" element={<WelcomePage />} />
              <Route path="/personal" element={<PersonalAccount />} />
              <Route path="/payment" element={<PaymentPage />} />
              <Route path="/leaderboard" element={<LeaderBoard />}></Route>
          </Routes>
      </BrowserRouter>
  </React.StrictMode>
);
