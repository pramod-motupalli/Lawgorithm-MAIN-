import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Gavel, MoveRight } from "lucide-react";
import FIRForm from "./components/FIRForm";
import FIRDisplay from "./components/FIRDisplay";
import QuestionnaireForm from "./components/QuestionnaireForm";
import ChargeSheetDisplay from "./components/ChargeSheetDisplay";
import VerdictDisplay from "./components/VerdictDisplay";
import FairnessPanel from "./components/FairnessPanel";

function App() {
    const [firText, setFirText] = useState("");

    const [formData, setFormData] = useState(null); // Store form data for sequential steps

    const [questionnaire, setQuestionnaire] = useState(null);
    const [chargeSheet, setChargeSheet] = useState(null);
    const [verdict, setVerdict] = useState(null);
    const [fairnessReport, setFairnessReport] = useState(null);
    const [fairnessLoading, setFairnessLoading] = useState(false);
    // Store answers for fairness analysis
    const [lastAnswers, setLastAnswers] = useState({ p: {}, d: {} });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // Track active step: 1=FIR, 2=Questionnaire, 3=ChargeSheet
    const [activeStep, setActiveStep] = useState(1);

    // Scroll ref
    const outputRef = useRef(null);

    const handleGenerateFIR = async (data) => {
        setLoading(true);
        setError("");
        setFirText("");
        setQuestionnaire(null);
        setFirText("");
        setQuestionnaire(null);
        setChargeSheet(null);
        setVerdict(null);
        setFormData(data);
        setActiveStep(1);

        try {
            const payload = {
                case_description: data.caseDescription,
                complainant: {
                    name: data.complainantName || "Not provided",
                    address: data.complainantAddress || "Not provided",
                    contact: data.complainantContact || "Not provided",
                },
                accused: {
                    name: data.accusedName || "Unknown person(s)",
                    address: data.accusedAddress || "Not provided",
                },
                date_time_place: data.incidentDetails || "Not provided",
                police_station: data.policeStation || "Not provided",
                fir_number: data.firNumber || "Not provided",
                registration_date: data.registrationDate || "Not provided",
                officer_name: data.officerName || "Not provided",
                officer_rank: data.officerRank || "Not provided",
            };

            const response = await axios.post(
                "http://127.0.0.1:8000/api/generate_fir",
                payload,
            );
            setFirText(response.data.fir);
        } catch (err) {
            console.error(err);
            setError(
                "Failed to generate FIR. Please check the backend connection.",
            );
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateQuestionnaire = async () => {
        if (!firText || !formData) return;
        setLoading(true);
        setError("");

        try {
            const response = await axios.post(
                "http://127.0.0.1:8000/api/generate_questionnaire",
                {
                    fir_content: firText,
                    case_description: formData.caseDescription,
                },
            );
            setQuestionnaire(response.data);
            setActiveStep(2);
        } catch (err) {
            console.error(err);
            setError("Failed to generate questionnaire.");
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateChargeSheet = async (pAnswers, dAnswers, summary) => {
        setLoading(true);
        setError("");
        // Store answers for later fairness analysis
        setLastAnswers({ p: pAnswers, d: dAnswers });

        try {
            const payload = {
                fir_content: firText,
                case_description: formData.caseDescription,
                plaintiff_answers: pAnswers,
                defendant_answers: dAnswers,
                investigation_summary: summary || "",
                officer_name: formData.officerName || "Not provided",
                officer_rank: formData.officerRank || "Not provided",
                police_station: formData.policeStation || "Not provided",
            };

            const response = await axios.post(
                "http://127.0.0.1:8000/api/generate_charge_sheet",
                payload,
            );
            setChargeSheet(response.data.charge_sheet);
            setActiveStep(3);
        } catch (err) {
            console.error(err);
            setError("Failed to generate Charge Sheet.");
        } finally {
            setLoading(false);
        }
    };

    const handlePredictVerdict = async () => {
        if (!chargeSheet || !formData) return;
        setLoading(true);
        setFairnessReport(null);
        setError("");

        try {
            const response = await axios.post(
                "http://127.0.0.1:8000/api/predict_verdict",
                {
                    charge_sheet_content: chargeSheet,
                    case_description: formData.caseDescription,
                },
            );
            const verdictData = response.data;
            setVerdict(verdictData);
            setActiveStep(4);

            // Auto-run fairness analysis after verdict
            setFairnessLoading(true);
            try {
                const fairnessResponse = await axios.post(
                    "http://127.0.0.1:8000/api/analyze_fairness",
                    {
                        charge_sheet_content: chargeSheet,
                        case_description: formData.caseDescription,
                        original_verdict: verdictData.verdict || "Guilty",
                        plaintiff_answers: lastAnswers.p,
                        defendant_answers: lastAnswers.d,
                        accused_name:
                            formData.accusedName || "Unknown person(s)",
                    },
                );
                setFairnessReport(fairnessResponse.data);
            } catch (fairErr) {
                console.error("Fairness analysis failed:", fairErr);
            } finally {
                setFairnessLoading(false);
            }
        } catch (err) {
            console.error(err);
            setError("Failed to predict verdict.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#f4f0e6] flex flex-col font-sans">
            {/* Header */}
            <header className="bg-white border-b border-[#dccba0] sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-[#1a3c6e] text-white p-2 rounded-lg">
                            <Gavel className="w-5 h-5" />
                        </div>
                        <h1 className="text-xl font-bold text-[#1a3c6e] tracking-tight">
                            Lawgorithm
                        </h1>
                    </div>

                    <div className="flex items-center gap-4 text-sm font-semibold text-gray-500">
                        <span
                            className={activeStep === 1 ? "text-[#1a3c6e]" : ""}
                        >
                            1. FIR
                        </span>
                        <MoveRight className="w-4 h-4" />
                        <span
                            className={activeStep === 2 ? "text-[#1a3c6e]" : ""}
                        >
                            2. Investigation
                        </span>
                        <MoveRight className="w-4 h-4" />
                        <span
                            className={activeStep === 3 ? "text-[#1a3c6e]" : ""}
                        >
                            3. Charge Sheet
                        </span>
                        <MoveRight className="w-4 h-4" />
                        <span
                            className={activeStep === 4 ? "text-[#1a3c6e]" : ""}
                        >
                            4. Verdict
                        </span>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-8rem)]">
                    {/* Left Column: Input */}
                    <div className="h-full overflow-y-auto pb-8 hide-scrollbar">
                        {activeStep === 1 && (
                            <div className="lg:max-w-xl">
                                <div className="mb-6">
                                    <h2 className="text-3xl font-bold text-gray-900 mb-2">
                                        Create New Report
                                    </h2>
                                    <p className="text-gray-600">
                                        Enter the incident details below to
                                        generate a formal First Information
                                        Report (FIR).
                                    </p>
                                </div>
                                {error && (
                                    <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 border border-red-100 text-sm">
                                        {error}
                                    </div>
                                )}
                                <FIRForm
                                    onSubmit={handleGenerateFIR}
                                    loading={loading}
                                    language="en"
                                />
                            </div>
                        )}

                        {activeStep === 2 && questionnaire && (
                            <div className="lg:max-w-xl">
                                <div className="mb-6 flex justify-between items-center">
                                    <div>
                                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                                            Conduct Investigation
                                        </h2>
                                        <p className="text-gray-600">
                                            Cross-examine both parties based on
                                            the generated FIR.
                                        </p>
                                    </div>
                                </div>
                                {error && (
                                    <div className="text-red-600 mb-4">
                                        {error}
                                    </div>
                                )}
                                <QuestionnaireForm
                                    questionnaire={questionnaire}
                                    onGenerateChargeSheet={
                                        handleGenerateChargeSheet
                                    }
                                    loading={loading}
                                    language="en"
                                />
                            </div>
                        )}

                        {activeStep === 3 && (
                            <div className="lg:max-w-xl flex flex-col justify-center items-center h-full text-center">
                                <div className="bg-green-100 p-6 rounded-full mb-6 text-green-700">
                                    <Gavel className="w-12 h-12" />
                                </div>
                                <h2 className="text-3xl font-bold text-[#1a3c6e] mb-2">
                                    Process Complete
                                </h2>
                                <p className="text-gray-600 mb-8 max-w-xs">
                                    The Charge Sheet has been successfully
                                    drafted based on your investigation
                                    findings.
                                </p>

                                <div className="mb-8 w-full max-w-xs">
                                    <button
                                        onClick={handlePredictVerdict}
                                        disabled={loading}
                                        className="w-full bg-[#1a3c6e] text-white py-3 rounded-lg font-bold hover:bg-[#15325b] transition-colors flex justify-center items-center gap-2"
                                    >
                                        {loading
                                            ? "Processing..."
                                            : "Predict Verdict"}
                                        <Gavel className="w-4 h-4" />
                                    </button>
                                </div>

                                <button
                                    onClick={() => {
                                        setActiveStep(1);
                                        setFirText("");
                                        setQuestionnaire(null);
                                        setChargeSheet(null);
                                    }}
                                    className="text-[#1a3c6e] font-semibold hover:underline"
                                >
                                    Start New Case
                                </button>
                            </div>
                        )}

                        {activeStep === 4 && (
                            <div className="lg:max-w-xl flex flex-col justify-center items-center h-full text-center">
                                <div className="bg-blue-100 p-6 rounded-full mb-6 text-blue-700">
                                    <Gavel className="w-12 h-12" />
                                </div>
                                <h2 className="text-3xl font-bold text-[#1a3c6e] mb-2">
                                    Process Complete
                                </h2>
                                <p className="text-gray-600 mb-8 max-w-xs">
                                    Verdict has been predicted based on the
                                    charge sheet.
                                </p>

                                <button
                                    onClick={() => {
                                        setActiveStep(1);
                                        setFirText("");
                                        setQuestionnaire(null);
                                        setChargeSheet(null);
                                        setVerdict(null);
                                    }}
                                    className="text-[#1a3c6e] font-semibold hover:underline"
                                >
                                    Start New Case
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Right Column: Output */}
                    <div className="h-full" ref={outputRef}>
                        {activeStep === 1 && firText ? (
                            <div className="h-full flex flex-col">
                                <div className="flex-1 overflow-y-auto mb-4 border rounded-xl shadow-sm">
                                    <FIRDisplay firText={firText} />
                                </div>
                                <button
                                    onClick={handleGenerateQuestionnaire}
                                    disabled={loading}
                                    className="w-full bg-[#1a3c6e] text-white py-3 rounded-lg font-bold hover:bg-[#15325b] transition-colors flex justify-center items-center gap-2"
                                >
                                    {loading ? (
                                        "Processing..."
                                    ) : (
                                        <>
                                            Proceed to Investigation{" "}
                                            <MoveRight className="w-5 h-5" />
                                        </>
                                    )}
                                </button>
                            </div>
                        ) : activeStep === 2 ? (
                            // During Step 2, we can show the FIR for reference or just a placeholder
                            <div className="h-full flex flex-col opacity-75">
                                <h3 className="text-sm font-bold text-gray-400 mb-2 uppercase tracking-wide">
                                    Reference: FIR Content
                                </h3>
                                <div className="flex-1 overflow-y-auto border rounded-xl shadow-sm bg-gray-100 pointer-events-none">
                                    <FIRDisplay firText={firText} />
                                </div>
                            </div>
                        ) : activeStep === 3 && chargeSheet ? (
                            <ChargeSheetDisplay
                                firNumber={formData?.firNumber}
                                chargeSheetText={chargeSheet}
                            />
                        ) : activeStep === 4 && verdict ? (
                            <div className="h-full flex flex-col overflow-y-auto pb-8">
                                <div className="p-1">
                                    <VerdictDisplay verdictData={verdict} />
                                    <FairnessPanel
                                        fairnessData={fairnessReport}
                                        loading={fairnessLoading}
                                    />
                                </div>
                                <div className="opacity-50 pointer-events-none h-64 overflow-hidden border rounded-xl mt-4 bg-gray-50 relative shrink-0">
                                    <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent z-10"></div>
                                    <ChargeSheetDisplay
                                        firNumber={formData?.firNumber}
                                        chargeSheetText={chargeSheet}
                                    />
                                </div>
                            </div>
                        ) : (
                            // Default Empty State
                            !firText && (
                                <div className="bg-white/50 border border-dashed border-gray-300 rounded-xl h-full flex flex-col items-center justify-center text-gray-400 p-8 text-center">
                                    <div className="bg-white p-4 rounded-full mb-4 shadow-sm">
                                        <Gavel className="w-8 h-8 text-police-200" />
                                    </div>
                                    <p className="font-medium text-gray-500">
                                        No Document Generated
                                    </p>
                                    <p className="text-sm mt-1 max-w-xs">
                                        Start by generating an FIR to begin the
                                        legal documentation process.
                                    </p>
                                </div>
                            )
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;
