import React, { useRef } from "react";
import { Download, Printer } from "lucide-react";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";

const ChargeSheetDisplay = ({
    chargeSheetText,
    firNumber,
    language = "en",
}) => {
    const contentRef = useRef(null);

    if (!chargeSheetText) return null;

    const generatePDF = (action = "download") => {
        try {
            const pdf = new jsPDF("p", "mm", "a4");

            const safeFir = (firNumber || "Draft").replace(
                /[^a-z0-9\-_]/gi,
                "_",
            );
            const filename = `ChargeSheet_${safeFir}.pdf`;

            pdf.setFont("helvetica", "bold");
            pdf.setFontSize(14);
            pdf.text(
                "FINAL REPORT UNDER SECTION 173 CrPC (CHARGE SHEET)",
                105,
                20,
                { align: "center" },
            );

            pdf.setFont("helvetica", "normal");
            pdf.setFontSize(11);

            let y = 35;
            const lines = chargeSheetText.split("\n");

            for (let i = 0; i < lines.length; i++) {
                if (y > 280) {
                    pdf.addPage();
                    y = 20;
                }

                let line = lines[i].trim();

                if (!line) {
                    y += 4;
                    continue;
                }

                if (line.startsWith("#")) {
                    pdf.setFont("helvetica", "bold");
                    pdf.setFontSize(12);
                    pdf.text(line.replace(/^#+\s*/, "").toUpperCase(), 15, y);
                    pdf.setFont("helvetica", "normal");
                    pdf.setFontSize(11);
                    y += 8;
                } else if (line.startsWith("- ")) {
                    pdf.text(
                        "• " + line.substring(2).replace(/\*\*/g, ""),
                        20,
                        y,
                    );
                    y += 6;
                } else {
                    const cleanLine = line.replace(/\*\*/g, ""); // Strip markdown bold logic for simple text rendering
                    const splitLines = pdf.splitTextToSize(cleanLine, 180);
                    for (let j = 0; j < splitLines.length; j++) {
                        if (y > 280) {
                            pdf.addPage();
                            y = 20;
                        }
                        pdf.text(splitLines[j], 15, y);
                        y += 6;
                    }
                }
            }

            // Signature block
            if (y > 250) {
                pdf.addPage();
                y = 20;
            }
            pdf.setFont("helvetica", "normal");
            pdf.text("Date: _________________", 15, y + 15);
            pdf.text("Place: _________________", 15, y + 22);

            pdf.setFont("helvetica", "bold");
            pdf.text("Signature of Officer In-Charge", 195, y + 15, {
                align: "right",
            });
            pdf.setFont("helvetica", "normal");
            pdf.setFontSize(9);
            pdf.text("(Name, Rank & Designation)", 195, y + 22, {
                align: "right",
            });

            if (action === "download") {
                pdf.save(filename);
            } else if (action === "print") {
                pdf.autoPrint();
                window.open(pdf.output("bloburl"), "_blank");
            }
        } catch (err) {
            console.error("PDF Generation failed:", err);
            alert("Failed to generate PDF. Please try again.");
        }
    };

    return (
        <div className="bg-white p-8 rounded-xl shadow-lg border border-[#dccba0] legal-paper h-full flex flex-col">
            <div className="flex justify-between items-start mb-6 border-b border-[#dccba0] pb-4">
                <div>
                    <h2 className="text-2xl font-bold font-serif text-black">
                        Final Charge Sheet
                    </h2>
                    <p className="text-[#8b7d5b] text-sm mt-1">
                        Generated Draft • Non-Legally Binding
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => generatePDF("print")}
                        className="p-2 hover:bg-[#f4f0e6] rounded-full text-[#1a3c6e] transition-colors"
                        title="Print Charge Sheet"
                    >
                        <Printer className="w-5 h-5" />
                    </button>
                    <button
                        onClick={() => generatePDF("download")}
                        className="p-2 hover:bg-[#f4f0e6] rounded-full text-[#1a3c6e] transition-colors"
                        title="Download PDF"
                    >
                        <Download className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-auto pr-4 custom-scrollbar">
                {/* Render formatted Charge Sheet content wrapped in a div for capture */}
                <div
                    ref={contentRef}
                    className="font-serif text-[#0a1629] whitespace-pre-wrap leading-relaxed print-content bg-white p-4"
                >
                    {/* Explicit Header for PDF */}
                    <div className="text-center font-bold text-xl mb-6 underline">
                        FINAL REPORT UNDER SECTION 173 CrPC (CHARGE SHEET)
                    </div>

                    {/* Content Rendering Logic */}
                    {(() => {
                        // Helper to parse bold text (**text**) within a string
                        const parseLine = (text) => {
                            if (!text) return null;
                            const parts = text.split(/(\*\*.*?\*\*)/g);
                            return parts.map((part, i) => {
                                if (
                                    part.startsWith("**") &&
                                    part.endsWith("**")
                                ) {
                                    return (
                                        <span key={i} className="font-bold">
                                            {part.slice(2, -2)}
                                        </span>
                                    );
                                }
                                return <span key={i}>{part}</span>;
                            });
                        };

                        return chargeSheetText
                            .split("\n")
                            .map((line, index) => {
                                const trimmed = line.trim();
                                if (!trimmed)
                                    return <div key={index} className="h-4" />; // Spacer for empty lines

                                // 1. Headers (Start with #)
                                if (trimmed.startsWith("#")) {
                                    return (
                                        <div
                                            key={index}
                                            className="font-bold mt-6 mb-3 text-lg uppercase underline tracking-wide"
                                        >
                                            {trimmed.replace(/^#+\s*/, "")}
                                        </div>
                                    );
                                }

                                // 2. Bold headers or Section Titles (End with :)
                                // Also handles cases like "**1. DETAILS:**"
                                if (trimmed.endsWith(":")) {
                                    return (
                                        <div
                                            key={index}
                                            className="font-bold mt-4 mb-2 uppercase underline"
                                        >
                                            {parseLine(trimmed)}
                                        </div>
                                    );
                                }

                                // 3. Bullet Points (Start with -)
                                if (trimmed.startsWith("- ")) {
                                    return (
                                        <div
                                            key={index}
                                            className="mb-1 pl-4 relative"
                                        >
                                            <span className="absolute left-0 top-0">
                                                •
                                            </span>
                                            {parseLine(trimmed.substring(2))}
                                        </div>
                                    );
                                }

                                // 4. Key-Value Pairs (contain :)
                                // Handles "**Name:** John Doe"
                                if (
                                    trimmed.includes(":") &&
                                    !trimmed.includes("http")
                                ) {
                                    const splitIndex = trimmed.indexOf(":");
                                    const key = trimmed.slice(
                                        0,
                                        splitIndex + 1,
                                    ); // Include :
                                    const value = trimmed.slice(splitIndex + 1);

                                    // Only treat as KV if key isn't too long (avoid sentences with colons)
                                    if (key.length < 60) {
                                        return (
                                            <div key={index} className="mb-1">
                                                <span className="font-semibold text-gray-900 mr-2">
                                                    {parseLine(key)}
                                                </span>
                                                <span className="text-gray-800">
                                                    {parseLine(value)}
                                                </span>
                                            </div>
                                        );
                                    }
                                }

                                // 5. Standard Text Paragraph
                                return (
                                    <div
                                        key={index}
                                        className="mb-1 text-justify"
                                    >
                                        {parseLine(trimmed)}
                                    </div>
                                );
                            });
                    })()}

                    <div className="mt-12 pt-8 border-t border-dashed border-gray-400 flex justify-between items-end">
                        <div className="text-sm">
                            Date: _________________
                            <br />
                            Place: _________________
                        </div>
                        <div className="text-right">
                            <div className="font-bold">
                                Signature of Officer In-Charge
                            </div>
                            <div className="text-sm text-gray-500 mt-1">
                                (Name, Rank & Designation)
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: #f4f0e6;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #1a3c6e;
                    border-radius: 4px;
                }

                @media print {
                    body * {
                        visibility: hidden;
                    }
                    .legal-paper,
                    .legal-paper * {
                        visibility: visible;
                    }
                    .legal-paper {
                        position: absolute;
                        left: 0;
                        top: 0;
                        width: 100%;
                        margin: 0;
                        padding: 20px;
                        background: white !important;
                        box-shadow: none !important;
                        border: none !important;
                    }
                    .print\\:hidden,
                    button {
                        display: none !important;
                    }
                    .print-content {
                        font-size: 12pt;
                        color: black !important;
                        height: auto;
                        overflow: visible;
                    }
                }
            `}</style>
        </div>
    );
};

export default ChargeSheetDisplay;
