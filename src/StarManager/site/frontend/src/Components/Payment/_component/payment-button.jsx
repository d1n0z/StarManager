export default function PaymentButton({ id, text, startState="--select", onClickEvent}) {
    return (
        <>
            <button id={id} className={`payment__menu-title__button${startState}`} onClick={() => onClickEvent(id)}>
                { text }</button>
        </>
    )
}