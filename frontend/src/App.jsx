import React, { useState } from 'react';
import axios from 'axios';
import { Gavel } from 'lucide-react';
import FIRForm from './components/FIRForm';
import FIRDisplay from './components/FIRDisplay';

function App() {
  const [firText, setFirText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async (formData) => {
    setLoading(true);
    setError('');
    setFirText('');

    try {
      // Map frontend form data to backend API schema
      const payload = {
        case_description: formData.caseDescription,
        complainant: {
          name: formData.complainantName || "Not provided",
          address: formData.complainantAddress || "Not provided",
          contact: formData.complainantContact || "Not provided"
        },
        accused: {
          name: formData.accusedName || "Unknown person(s)",
          address: formData.accusedAddress || "Not provided"
        },
        date_time_place: formData.incidentDetails || "Not provided",
        police_station: formData.policeStation || "Not provided",
        fir_number: formData.firNumber || "Not provided",
        registration_date: formData.registrationDate || "Not provided",
        officer_name: formData.officerName || "Not provided",
        officer_rank: formData.officerRank || "Not provided"
      };

      const response = await axios.post('http://127.0.0.1:8000/api/generate_fir', payload);
      setFirText(response.data.fir);
    } catch (err) {
      console.error(err);
      setError('Failed to generate FIR. Please check the backend connection.');
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
              Police <span className="text-[#d32f2f]">DraftAssist</span>
            </h1>
          </div>
          <div className="text-sm font-medium text-[#1a3c6e] hidden sm:block">
            AI-Powered Legal Documentation
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-8rem)]">
          {/* Left Column: Input */}
          <div className="h-full overflow-y-auto pb-8 hide-scrollbar">
            <div className="lg:max-w-xl">
              <div className="mb-6">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">Create New Report</h2>
                <p className="text-gray-600">Enter the incident details below to generate a formal First Information Report (FIR).</p>
              </div>
              
              {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 border border-red-100 text-sm">
                  {error}
                </div>
              )}

              <FIRForm onSubmit={handleGenerate} loading={loading} />
            </div>
          </div>

          {/* Right Column: Output */}
          <div className="h-full">
            {firText ? (
              <FIRDisplay firText={firText} />
            ) : (
              <div className="bg-white/50 border border-dashed border-gray-300 rounded-xl h-full flex flex-col items-center justify-center text-gray-400 p-8 text-center">
                <div className="bg-white p-4 rounded-full mb-4 shadow-sm">
                  <Gavel className="w-8 h-8 text-police-200" />
                </div>
                <p className="font-medium text-gray-500">No FIR Generated Yet</p>
                <p className="text-sm mt-1 max-w-xs">Fill out the details on the left and click "Generate FIR" to see the preview here.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
