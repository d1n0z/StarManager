export function TitleComponent({
                                   objectTitle,
                                   objectDescription,
                                   componentClassName = "component"
                               }) {
    return (
        <>
            <div className={ componentClassName }>
                <aside className={ `title-${componentClassName}` }>
                    { objectTitle }
                </aside>

                <aside className={ `description-${componentClassName}` }>
                    { objectDescription }
                </aside>
            </div>
        </>
    )
}