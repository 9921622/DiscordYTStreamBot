import { useState } from "react";

interface HorizontalAccordionProps {
    children: React.ReactNode;
    childrenClosed?: React.ReactNode,
    peek?: React.ReactNode;
    width?: string;
    closedWidth?: string;
    defaultOpen?: boolean;
}

export default function HorizontalAccordion({
    children,
    childrenClosed,
    peek,
    width = "w-112",
    closedWidth = "w-10",
    defaultOpen = true
}: HorizontalAccordionProps) {
    const [open, setOpen] = useState(defaultOpen);

    return (
        <div className={`flex-shrink-0 h-full flex flex-col transition-[width] duration-300 overflow-hidden ${open ? width : closedWidth}`}>

            <button
                onClick={() => setOpen(o => !o)}
                className="btn btn-ghost btn-xs self-end m-1 flex-shrink-0"
                title={open ? "Close" : "Open"}
            >
                {open ? "›" : "‹"}
            </button>

            {peek && <div className="flex-shrink-0">{peek}</div>}

            {open ? (
                <div className="flex flex-col flex-1 overflow-hidden">
                    {children}
                </div>
            ) : (
                childrenClosed && (
                    <div className="flex flex-col flex-1 overflow-hidden">
                        {childrenClosed}
                    </div>
                )
            )}
        </div>
    );
}
