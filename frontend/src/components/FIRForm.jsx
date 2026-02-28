import React, { useState } from "react";
import { Send, FileText, MapPin, User, ShieldAlert, Mic } from "lucide-react";

const FIRForm = ({ onSubmit, loading }) => {
    const [formData, setFormData] = useState({
        // Official Details
        policeStation: "",
        firNumber: "",
        registrationDate: "",
        officerName: "",
        officerRank: "",
        // Original Fields
        complainantName: "",
        complainantAddress: "",
        complainantContact: "",
        accusedName: "",
        accusedAddress: "",
        incidentDetails: "",
        caseDescription: "",
    });

    const [listeningField, setListeningField] = useState(null);

    const startListening = (fieldName) => {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert("Speech Recognition not supported in this browser");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "en-IN"; // change if needed
        recognition.interimResults = false;

        recognition.start();
        setListeningField(fieldName);

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;

            setFormData((prev) => ({
                ...prev,
                [fieldName]: prev[fieldName]
                    ? prev[fieldName] + " " + transcript
                    : transcript,
            }));

            setListeningField(null);
        };

        recognition.onerror = () => {
            setListeningField(null);
        };

        recognition.onend = () => {
            setListeningField(null);
        };
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const text = formData.caseDescription.trim();

        // Basic gibberish heuristics
        const isGibberish = (str) => {
            if (str.length < 10) return true; // Too short
            if (/^(.)\1+$/.test(str)) return true; // Repeating single character
            if (str.length > 20 && !str.includes(" ")) return true; // Long string without spaces
            if (!/[aeiouyAEIOUY]/.test(str)) return true; // No vowels
            if (/[bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ]{6,}/.test(str))
                return true; // 6+ consonants in a row

            // Calculate unique characters for repeating patterns
            const chars = str.replace(/\s/g, "");
            const uniqueChars = new Set(chars).size;
            if (chars.length > 15 && uniqueChars < 5) return true;

            return false;
        };

        if (isGibberish(text)) {
            alert("enter meaning full description");
            return;
        }

        onSubmit(formData);
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-[#dccba0]">
            <div className="flex items-center gap-2 mb-6 text-[#1a3c6e]">
                <ShieldAlert className="w-6 h-6" />
                <h2 className="text-xl font-bold font-serif">
                    Incident Details
                </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* OFFICIAL USE ONLY Section */}
                <div className="bg-[#f4f0e6] p-4 rounded-lg border border-[#dccba0] -mx-2">
                    <h3 className="text-sm font-bold text-[#1a3c6e] uppercase tracking-wider mb-3 flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4" /> Official Details
                        (Police Use)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input
                            type="text"
                            name="policeStation"
                            placeholder="Police Station Name"
                            className="input-field"
                            value={formData.policeStation}
                            onChange={handleChange}
                        />
                        <input
                            type="text"
                            name="firNumber"
                            placeholder="FIR Number (e.g. 123/2023)"
                            className="input-field"
                            value={formData.firNumber}
                            onChange={handleChange}
                        />
                        <input
                            type="datetime-local"
                            name="registrationDate"
                            className="input-field text-gray-500"
                            value={formData.registrationDate}
                            onChange={handleChange}
                        />
                        <div className="flex gap-2">
                            <input
                                type="text"
                                name="officerName"
                                placeholder="IO Name"
                                className="input-field flex-1"
                                value={formData.officerName}
                                onChange={handleChange}
                            />
                            <input
                                type="text"
                                name="officerRank"
                                placeholder="Rank"
                                className="input-field w-1/3"
                                value={formData.officerRank}
                                onChange={handleChange}
                            />
                        </div>
                    </div>
                </div>

                {/* Complainant Section */}
                <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-[#8b7d5b] uppercase tracking-wider flex items-center gap-2">
                        <User className="w-4 h-4" /> Complainant (Plaintiff)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input
                            type="text"
                            name="complainantName"
                            placeholder="Full Name"
                            className="input-field"
                            value={formData.complainantName}
                            onChange={handleChange}
                            required
                        />
                        <input
                            type="text"
                            name="complainantContact"
                            placeholder="Contact Number"
                            className="input-field"
                            value={formData.complainantContact}
                            onChange={handleChange}
                            required
                        />
                        <input
                            type="text"
                            name="complainantAddress"
                            placeholder="Address"
                            className="input-field md:col-span-2"
                            value={formData.complainantAddress}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                <div className="h-px bg-[#e8dec3] my-4" />

                {/* Accused Section */}
                <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-[#8b7d5b] uppercase tracking-wider flex items-center gap-2">
                        <User className="w-4 h-4 text-[#d32f2f]" /> Accused
                        (Defendant)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input
                            type="text"
                            name="accusedName"
                            placeholder="Name (or 'Unknown')"
                            className="input-field"
                            value={formData.accusedName}
                            onChange={handleChange}
                        />
                        <input
                            type="text"
                            name="accusedAddress"
                            placeholder="Address (if known)"
                            className="input-field"
                            value={formData.accusedAddress}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                <div className="h-px bg-[#e8dec3] my-4" />

                <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-[#8b7d5b] uppercase tracking-wider flex items-center gap-2">
                        <FileText className="w-4 h-4" /> Case Details
                    </h3>

                    {/* Incident Details with Mic */}
                    <div className="relative">
                        <input
                            type="text"
                            name="incidentDetails"
                            placeholder="Date, Time, and Place (e.g., 12th Dec at 4PM, Main Market)"
                            className={`input-field w-full pr-28 transition-all ${listeningField === "incidentDetails" ? "border-red-400 ring-2 ring-red-100 bg-red-50" : ""}`}
                            value={formData.incidentDetails}
                            onChange={handleChange}
                        />
                        {listeningField === "incidentDetails" && (
                            <span className="absolute right-10 top-2.5 text-xs font-bold text-red-500 animate-pulse flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
                                Listening...
                            </span>
                        )}
                        <button
                            type="button"
                            onClick={() => startListening("incidentDetails")}
                            className={`absolute right-2 top-2 p-1 rounded-full transition-colors ${listeningField === "incidentDetails" ? "bg-red-100 text-red-600 shadow-sm" : "text-[#1a3c6e] hover:bg-gray-200"}`}
                            title={
                                listeningField === "incidentDetails"
                                    ? "Recording active"
                                    : "Click to speak"
                            }
                        >
                            <Mic className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Case Description with Mic */}
                    <div className="relative">
                        <textarea
                            name="caseDescription"
                            placeholder="Describe the incident in detail... (What happened?)"
                            className={`input-field w-full h-32 resize-none pr-28 transition-all ${listeningField === "caseDescription" ? "border-red-400 ring-2 ring-red-100 bg-red-50" : ""}`}
                            value={formData.caseDescription}
                            onChange={handleChange}
                            required
                        />
                        {listeningField === "caseDescription" && (
                            <span className="absolute right-10 top-2.5 text-xs font-bold text-red-500 animate-pulse flex items-center gap-1 bg-white px-2 py-0.5 rounded-full shadow-sm">
                                <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
                                Listening...
                            </span>
                        )}
                        <button
                            type="button"
                            onClick={() => startListening("caseDescription")}
                            className={`absolute right-2 top-2 p-1 rounded-full transition-colors ${listeningField === "caseDescription" ? "bg-red-100 text-red-600 shadow-sm" : "text-[#1a3c6e] hover:bg-gray-200"}`}
                            title={
                                listeningField === "caseDescription"
                                    ? "Recording active"
                                    : "Click to speak"
                            }
                        >
                            <Mic className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-[#1a3c6e] hover:bg-[#122849] text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg disabled:opacity-70"
                >
                    {loading ? (
                        "Processing Legal Data..."
                    ) : (
                        <>
                            Generate FIR <Send className="w-4 h-4" />
                        </>
                    )}
                </button>
            </form>

            <style jsx>{`
                .input-field {
                    @apply w-full px-4 py-2 border border-[#dccba0] rounded-lg focus:ring-2 focus:ring-[#1a3c6e] focus:border-transparent outline-none transition-all text-sm bg-[#faf9f6];
                }
            `}</style>
        </div>
    );
};

export default FIRForm;
