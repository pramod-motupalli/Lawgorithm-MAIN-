import React, { useState, useEffect } from "react";
import {
    User,
    UserX,
    Wand2,
    FileText,
    CheckCircle,
    Plus,
    Trash2,
    Mic,
} from "lucide-react";

const QuestionnaireForm = ({
    questionnaire,
    onGenerateChargeSheet,
    loading,
    language = "en",
}) => {
    const [plaintiffAnswers, setPlaintiffAnswers] = useState({});
    const [defendantAnswers, setDefendantAnswers] = useState({});
    const [summary, setSummary] = useState("");
    const [listeningField, setListeningField] = useState(null);

    const t = {}; // Placeholder or removed completely if unused elsewhere, but since t is used heavily, I need to replace all t. usage.
    // Actually, I am deleting this line. The replacements below handle t. usage.

    // Dynamic questions state: array of { id: number, question: string, answer: string }
    const [customPQuestions, setCustomPQuestions] = useState([]);
    const [customDQuestions, setCustomDQuestions] = useState([]);

    const handlePChange = (q, val) => {
        setPlaintiffAnswers((prev) => ({ ...prev, [q]: val }));
    };

    const handleDChange = (q, val) => {
        setDefendantAnswers((prev) => ({ ...prev, [q]: val }));
    };

    const handleAutoFill = () => {
        const p_answers = questionnaire.plaintiff_simulated_answers || [];
        const d_answers = questionnaire.defendant_simulated_answers || [];

        const dummyP = {};
        questionnaire.plaintiff_questions.forEach((q, idx) => {
            dummyP[q] =
                p_answers[idx] ||
                "This is a simulated answer verifying the facts.";
        });
        setPlaintiffAnswers(dummyP);

        const dummyD = {};
        questionnaire.defendant_questions.forEach((q, idx) => {
            dummyD[q] =
                d_answers[idx] ||
                "This is a simulated answer denying the allegations.";
        });
        setDefendantAnswers(dummyD);
    };

    // Custom Question Handlers
    const addCustomQuestion = (type) => {
        const newQ = { id: Date.now(), question: "", answer: "" };
        if (type === "plaintiff") {
            setCustomPQuestions([...customPQuestions, newQ]);
        } else {
            setCustomDQuestions([...customDQuestions, newQ]);
        }
    };

    const updateCustomQuestion = (type, id, field, value) => {
        if (type === "plaintiff") {
            setCustomPQuestions((prev) =>
                prev.map((q) => (q.id === id ? { ...q, [field]: value } : q)),
            );
        } else {
            setCustomDQuestions((prev) =>
                prev.map((q) => (q.id === id ? { ...q, [field]: value } : q)),
            );
        }
    };

    const removeCustomQuestion = (type, id) => {
        if (type === "plaintiff") {
            setCustomPQuestions((prev) => prev.filter((q) => q.id !== id));
        } else {
            setCustomDQuestions((prev) => prev.filter((q) => q.id !== id));
        }
    };

    const isFormValid = () => {
        // Standard questions must be answered
        const pDone = questionnaire.plaintiff_questions.every(
            (q) => plaintiffAnswers[q] && plaintiffAnswers[q].trim() !== "",
        );
        const dDone = questionnaire.defendant_questions.every(
            (q) => defendantAnswers[q] && defendantAnswers[q].trim() !== "",
        );

        // Custom questions must have both Q and A if they exist
        const customPDone = customPQuestions.every(
            (q) => q.question.trim() !== "" && q.answer.trim() !== "",
        );
        const customDDone = customDQuestions.every(
            (q) => q.question.trim() !== "" && q.answer.trim() !== "",
        );

        return pDone && dDone && customPDone && customDDone;
    };

    const handleSubmit = () => {
        // Merge standard and custom answers
        const finalPAnswers = { ...plaintiffAnswers };
        customPQuestions.forEach((q) => {
            if (q.question.trim()) finalPAnswers[q.question] = q.answer;
        });

        const finalDAnswers = { ...defendantAnswers };
        customDQuestions.forEach((q) => {
            if (q.question.trim()) finalDAnswers[q.question] = q.answer;
        });

        onGenerateChargeSheet(finalPAnswers, finalDAnswers, summary);
    };

    const startListening = (callbackKey, setter) => {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert("Speech Recognition not supported in this browser");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "en-IN";
        recognition.interimResults = false;

        recognition.start();
        setListeningField(callbackKey);

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;

            setter((prev) => (prev ? prev + " " + transcript : transcript));

            setListeningField(null);
        };

        recognition.onerror = () => setListeningField(null);
        recognition.onend = () => setListeningField(null);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg border border-[#e0e0e0] overflow-hidden">
            <div className="bg-[#1a3c6e] p-4 flex justify-between items-center">
                <h2 className="text-white font-bold flex items-center gap-2">
                    <Wand2 className="w-5 h-5" /> Investigation Questionnaire
                </h2>
                <button
                    onClick={handleAutoFill}
                    className="text-xs bg-[#ffffff20] hover:bg-[#ffffff40] text-white px-3 py-1 rounded transition-colors"
                >
                    Auto-Fill (Demo)
                </button>
            </div>

            <div className="p-6 space-y-8">
                {/* Synopsis Section */}
                <div>
                    <h3 className="text-lg font-semibold text-[#1a3c6e] flex items-center gap-2 mb-4 border-b pb-2">
                        <FileText className="w-5 h-5" /> Investigation Synopsis
                        (Summary)
                    </h3>
                    <div className="relative">
                        <textarea
                            value={summary}
                            onChange={(e) => setSummary(e.target.value)}
                            placeholder="Enter a brief synopsis of the investigation findings..."
                            className="w-full p-3 pr-10 border border-gray-300 rounded focus:ring-2 focus:ring-[#1a3c6e] focus:border-transparent outline-none text-sm"
                            rows={3}
                        />
                        <button
                            type="button"
                            onClick={() =>
                                startListening("summary", setSummary)
                            }
                            className="absolute right-2 top-2 text-[#1a3c6e]"
                        >
                            <Mic
                                className={`w-5 h-5 ${
                                    listeningField === "summary"
                                        ? "text-red-500 animate-pulse"
                                        : ""
                                }`}
                            />
                        </button>
                    </div>
                </div>

                {/* Plaintiff Section */}
                <div>
                    <h3 className="text-lg font-semibold text-[#1a3c6e] flex items-center gap-2 mb-4 border-b pb-2">
                        <User className="w-5 h-5" /> Cross-Examination:
                        Plaintiff
                    </h3>
                    <div className="space-y-4">
                        {questionnaire.plaintiff_questions.map((q, idx) => (
                            <div
                                key={idx}
                                className="bg-gray-50 p-4 rounded-lg border border-gray-100"
                            >
                                <p className="font-medium text-gray-800 mb-2">
                                    {idx + 1}. {q}
                                </p>
                                <div className="relative">
                                    <textarea
                                        value={plaintiffAnswers[q] || ""}
                                        onChange={(e) =>
                                            handlePChange(q, e.target.value)
                                        }
                                        placeholder="Enter answer..."
                                        className="w-full p-2 pr-10 border border-gray-300 rounded focus:ring-2 focus:ring-[#1a3c6e] focus:border-transparent outline-none text-sm"
                                        rows={2}
                                    />
                                    <button
                                        type="button"
                                        onClick={() =>
                                            startListening(
                                                `plaintiff-${idx}`,
                                                (updateFn) =>
                                                    setPlaintiffAnswers(
                                                        (prev) => ({
                                                            ...prev,
                                                            [q]: updateFn(
                                                                prev[q] || "",
                                                            ),
                                                        }),
                                                    ),
                                            )
                                        }
                                        className="absolute right-2 top-2 text-[#1a3c6e]"
                                    >
                                        <Mic
                                            className={`w-4 h-4 ${
                                                listeningField ===
                                                `plaintiff-${idx}`
                                                    ? "text-red-500 animate-pulse"
                                                    : ""
                                            }`}
                                        />
                                    </button>
                                </div>
                            </div>
                        ))}

                        {/* Custom Plaintiff Questions */}
                        {customPQuestions.map((item, idx) => (
                            <div
                                key={item.id}
                                className="bg-blue-50 p-4 rounded-lg border border-blue-100 relative group"
                            >
                                <div className="mb-2 pr-8">
                                    <input
                                        type="text"
                                        placeholder="Type your question here..."
                                        value={item.question}
                                        onChange={(e) =>
                                            updateCustomQuestion(
                                                "plaintiff",
                                                item.id,
                                                "question",
                                                e.target.value,
                                            )
                                        }
                                        className="w-full p-2 border border-blue-200 rounded text-sm font-medium focus:outline-none focus:border-blue-400"
                                    />
                                </div>
                                <textarea
                                    value={item.answer}
                                    onChange={(e) =>
                                        updateCustomQuestion(
                                            "plaintiff",
                                            item.id,
                                            "answer",
                                            e.target.value,
                                        )
                                    }
                                    placeholder="Enter answer..."
                                    className="w-full p-2 border border-blue-200 rounded focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none text-sm"
                                    rows={2}
                                />
                                <button
                                    onClick={() =>
                                        removeCustomQuestion(
                                            "plaintiff",
                                            item.id,
                                        )
                                    }
                                    className="absolute top-2 right-2 text-red-400 hover:text-red-600 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}

                        <button
                            onClick={() => addCustomQuestion("plaintiff")}
                            className="flex items-center gap-2 text-sm text-[#1a3c6e] font-medium hover:bg-blue-50 px-3 py-2 rounded transition-colors"
                        >
                            <Plus className="w-4 h-4" /> Add Question
                        </button>
                    </div>
                </div>

                {/* Defendant Section */}
                <div>
                    <h3 className="text-lg font-semibold text-red-700 flex items-center gap-2 mb-4 border-b pb-2">
                        <UserX className="w-5 h-5" /> Cross-Examination:
                        Defendant
                    </h3>
                    <div className="space-y-4">
                        {questionnaire.defendant_questions.map((q, idx) => (
                            <div
                                key={idx}
                                className="bg-red-50 p-4 rounded-lg border border-red-100"
                            >
                                <p className="font-medium text-gray-800 mb-2">
                                    {idx + 1}. {q}
                                </p>
                                <div className="relative">
                                    <textarea
                                        value={defendantAnswers[q] || ""}
                                        onChange={(e) =>
                                            handleDChange(q, e.target.value)
                                        }
                                        placeholder="Enter answer..."
                                        className="w-full p-2 pr-10 border border-gray-300 rounded focus:ring-2 focus:ring-red-700 focus:border-transparent outline-none text-sm"
                                        rows={2}
                                    />
                                    <button
                                        type="button"
                                        onClick={() =>
                                            startListening(
                                                `defendant-${idx}`,
                                                (updateFn) =>
                                                    setDefendantAnswers(
                                                        (prev) => ({
                                                            ...prev,
                                                            [q]: updateFn(
                                                                prev[q] || "",
                                                            ),
                                                        }),
                                                    ),
                                            )
                                        }
                                        className="absolute right-2 top-2 text-red-700"
                                    >
                                        <Mic
                                            className={`w-4 h-4 ${
                                                listeningField ===
                                                `defendant-${idx}`
                                                    ? "text-red-500 animate-pulse"
                                                    : ""
                                            }`}
                                        />
                                    </button>
                                </div>
                            </div>
                        ))}

                        {/* Custom Defendant Questions */}
                        {customDQuestions.map((item, idx) => (
                            <div
                                key={item.id}
                                className="bg-red-50 p-4 rounded-lg border border-red-200 relative group"
                            >
                                <div className="mb-2 pr-8">
                                    <input
                                        type="text"
                                        placeholder="Type your question here..."
                                        value={item.question}
                                        onChange={(e) =>
                                            updateCustomQuestion(
                                                "defendant",
                                                item.id,
                                                "question",
                                                e.target.value,
                                            )
                                        }
                                        className="w-full p-2 border border-red-200 rounded text-sm font-medium focus:outline-none focus:border-red-400"
                                    />
                                </div>
                                <textarea
                                    value={item.answer}
                                    onChange={(e) =>
                                        updateCustomQuestion(
                                            "defendant",
                                            item.id,
                                            "answer",
                                            e.target.value,
                                        )
                                    }
                                    placeholder="Enter answer..."
                                    className="w-full p-2 border border-red-200 rounded focus:ring-2 focus:ring-red-700 focus:border-transparent outline-none text-sm"
                                    rows={2}
                                />
                                <button
                                    onClick={() =>
                                        removeCustomQuestion(
                                            "defendant",
                                            item.id,
                                        )
                                    }
                                    className="absolute top-2 right-2 text-red-400 hover:text-red-600 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}

                        <button
                            onClick={() => addCustomQuestion("defendant")}
                            className="flex items-center gap-2 text-sm text-red-700 font-medium hover:bg-red-50 px-3 py-2 rounded transition-colors"
                        >
                            <Plus className="w-4 h-4" /> Add Question
                        </button>
                    </div>
                </div>
            </div>

            <div className="bg-gray-50 p-4 border-t border-gray-200 flex justify-end">
                <button
                    onClick={handleSubmit}
                    disabled={!isFormValid() || loading}
                    className={`
            flex items-center gap-2 px-6 py-2 rounded-lg font-semibold transition-all shadow-md
            ${
                !isFormValid() || loading
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-green-600 text-white hover:bg-green-700 hover:shadow-lg"
            }
          `}
                >
                    {loading ? (
                        <span className="flex items-center gap-2">
                            Generating...
                        </span>
                    ) : (
                        <>
                            Generate Charge Sheet{" "}
                            <CheckCircle className="w-4 h-4" />
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default QuestionnaireForm;
