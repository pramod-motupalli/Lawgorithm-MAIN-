import React, { useState } from "react";
import {
    ShieldCheck,
    ShieldAlert,
    ShieldX,
    ChevronDown,
    ChevronUp,
} from "lucide-react";

// ─── Main Component ─────────────────────────────────────────────────────────────

const FairnessPanel = ({ fairnessData, loading }) => {
    const [expanded, setExpanded] = useState(false);

    // Loading state
    if (loading) {
        return (
            <div className="mt-6 bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex items-center gap-3 text-gray-500">
                <div className="w-5 h-5 border-2 border-gray-300 border-t-purple-600 rounded-full animate-spin" />
                <span className="text-sm">
                    Running fairness analysis and bias check…
                </span>
            </div>
        );
    }

    if (!fairnessData) return null;

    const {
        overall_label,
        explanation
    } = fairnessData;

    // Header style by overall label
    const headerStyle =
        overall_label === "Fair"
            ? {
                  bg: "bg-green-50 border-green-200",
                  text: "text-green-700",
                  icon: ShieldCheck,
                  iconColor: "text-green-600",
              }
            : overall_label === "Needs Review"
              ? {
                    bg: "bg-yellow-50 border-yellow-200",
                    text: "text-yellow-700",
                    icon: ShieldAlert,
                    iconColor: "text-yellow-600",
                }
              : {
                    bg: "bg-red-50 border-red-200",
                    text: "text-red-700",
                    icon: ShieldX,
                    iconColor: "text-red-600",
                };

    const HeaderIcon = headerStyle.icon;

    return (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* ── Header ── */}
            <div
                className={`p-4 border ${headerStyle.bg} flex items-center justify-between gap-3 cursor-pointer`}
                onClick={() => setExpanded((p) => !p)}
            >
                <div className="flex items-center gap-3">
                    <HeaderIcon
                        className={`w-6 h-6 ${headerStyle.iconColor}`}
                    />
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-1">
                            AI Fairness Analysis
                        </p>
                        <h3 className={`text-lg font-bold ${headerStyle.text}`}>
                            {overall_label}
                        </h3>
                    </div>
                </div>
                
                <button
                    className="text-gray-400 hover:text-gray-600 transition-colors shrink-0"
                    title={expanded ? "Collapse" : "Expand details"}
                >
                    {expanded ? (
                        <ChevronUp className="w-5 h-5" />
                    ) : (
                        <ChevronDown className="w-5 h-5" />
                    )}
                </button>
            </div>

            {/* ── Expanded Detail ── */}
            {expanded && (
                <div className="p-4 bg-gray-50 space-y-4">
                    <div className="bg-white rounded-lg p-4 border border-gray-100 shadow-sm text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {explanation}
                    </div>

                    <p className="text-xs text-gray-400 italic text-center pt-2">
                        * Fairness analysis is AI-assisted and not a substitute
                        for human legal review.
                    </p>
                </div>
            )}
        </div>
    );
};

export default FairnessPanel;
