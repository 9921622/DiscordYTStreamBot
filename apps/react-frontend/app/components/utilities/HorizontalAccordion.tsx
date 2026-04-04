import { useState } from "react";

interface HorizontalAccordionProps {
    children: React.ReactNode;
    childrenClosed?: React.ReactNode;
    peek?: React.ReactNode;
    width?: string;
    closedWidth?: string;
    defaultOpen?: boolean;
    closeIcon?: React.ReactNode;
    openIcon?: React.ReactNode;
    iconSide?: "left" | "right";
}

export default function HorizontalAccordion({
    children,
    childrenClosed,
    peek,
    width = "w-112",
    closedWidth = "w-10",
    defaultOpen = true,
    closeIcon = "›",
    openIcon = "‹",
    iconSide = "right",
}: HorizontalAccordionProps) {
    const [open, setOpen] = useState(defaultOpen);

    const toggleButton = (
        <button
            onClick={() => setOpen((o) => !o)}
            className="btn btn-ghost btn-xs m-1 flex-shrink-0"
            title={open ? "Close" : "Open"}
        >
            {open ? closeIcon : openIcon}
        </button>
    );

    return (
        <div
            className={`flex-shrink-0 h-full flex flex-col transition-[width] duration-300 overflow-hidden ${
                open ? width : closedWidth
            }`}
        >
            {/* Toggle button row — left or right aligned */}
            <div
                className={`flex flex-shrink-0 ${
                    iconSide === "left" ? "justify-start" : "justify-end"
                }`}
            >
                {toggleButton}
            </div>

            {peek && <div className="flex-shrink-0">{peek}</div>}

            {open ? (
                <div className="flex flex-col flex-1 overflow-hidden">
                    {children}
                </div>
            ) : childrenClosed ? (
                <div className="flex flex-col flex-1 overflow-hidden">
                    {childrenClosed}
                </div>
            ) : (
                <div className="flex flex-col flex-1 overflow-hidden opacity-50 pointer-events-none">
                    {children}
                </div>
            )}
        </div>
    );
}
