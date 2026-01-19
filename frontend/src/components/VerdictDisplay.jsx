import React from "react";
import { Gavel, AlertCircle, CheckCircle2, ShieldAlert } from "lucide-react";

const VerdictDisplay = ({ verdictData }) => {
    if (!verdictData) return null;

    const {
        verdict,
        punishment_type,
        jail_term,
        fine_amount,
        legal_rationale,
    } = verdictData;

    const isGuilty =
        verdict?.toLowerCase().includes("guilty") &&
        !verdict?.toLowerCase().includes("not");
    const isNotGuilty = verdict?.toLowerCase().includes("not guilty");

    // Dynamic colors based on verdict
    const headerColor = isGuilty
        ? "bg-red-100 text-red-800"
        : isNotGuilty
          ? "bg-green-100 text-green-800"
          : "bg-blue-100 text-blue-800"; // Partial or uncertain

    const icon = isGuilty ? (
        <Gavel className="w-8 h-8" />
    ) : isNotGuilty ? (
        <CheckCircle2 className="w-8 h-8" />
    ) : (
        <AlertCircle className="w-8 h-8" />
    );

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-fade-in">
            {/* Header */}
            <div className={`p-6 flex items-center gap-4 ${headerColor}`}>
                <div className="p-3 bg-white/50 rounded-full backdrop-blur-sm shadow-sm">
                    {icon}
                </div>
                <div>
                    <h2 className="text-2xl font-bold tracking-tight uppercase">
                        {verdict}
                    </h2>
                    <p className="text-sm font-medium opacity-90">
                        {isGuilty
                            ? "Conviction Predicted"
                            : isNotGuilty
                              ? "Acquittal Predicted"
                              : "Complex Verdict"}
                    </p>
                </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
                {/* Punishment Section */}
                {isGuilty && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">
                                Jail Term
                            </h3>
                            <p className="text-lg font-bold text-gray-900">
                                {jail_term || "None"}
                            </p>
                        </div>
                        <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">
                                Fine Amount
                            </h3>
                            <p className="text-lg font-bold text-gray-900">
                                {fine_amount || "None"}
                            </p>
                        </div>
                    </div>
                )}

                {/* Rationale Section */}
                <div className="bg-blue-50/50 p-5 rounded-lg border border-blue-100">
                    <div className="flex items-start gap-3">
                        <ShieldAlert className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                        <div>
                            <h3 className="text-sm font-bold text-blue-800 mb-2">
                                Legal Rationale
                            </h3>
                            <p className="text-gray-700 leading-relaxed text-sm">
                                {legal_rationale}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="text-center">
                    <p className="text-xs text-gray-400 italic">
                        * This is an AI prediction based on the generated charge
                        sheet and is not a real judicial pronouncement.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default VerdictDisplay;
