// css
import "../styles/payment.css";

// js
import { MiniProfile } from "../Components/mini-profile";

import { PaymentMenu } from "../Components/Payment/payment-menu";


function PaymentPage() {
    return (
        <div className={"payment"}>
            <MiniProfile></MiniProfile>
            <PaymentMenu></PaymentMenu>
        </div>
    );
}

export default PaymentPage;
