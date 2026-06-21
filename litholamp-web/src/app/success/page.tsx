"use client";

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { CheckCircle, Package } from 'lucide-react';
import { ThreeDViewer } from '../../components/ThreeDViewer';

function SuccessContent() {
  const searchParams = useSearchParams();
  const hardware = searchParams.get('hardware') || 'Base';
  const jobId = searchParams.get('job_id');
  const stlUrl = jobId ? `/api/download/${jobId}` : null;

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-4xl w-full bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden flex flex-col md:flex-row">
        
        {/* Left Side - 3D Viewer */}
        <div className="md:w-1/2 bg-slate-900 relative min-h-[400px] flex">
          {stlUrl ? (
            <ThreeDViewer stlUrl={stlUrl} />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-slate-500">No Model Data</div>
          )}
        </div>

        {/* Right Side - Success Message */}
        <div className="md:w-1/2 p-10 text-center flex flex-col justify-center">
          <div className="w-20 h-20 bg-green-100 text-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={40} />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Order Confirmed!</h1>
          <p className="text-slate-500 mb-8">
            Order #{jobId?.substring(0,8).toUpperCase() || 'UNKNOWN'}
          </p>

          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 text-left mb-8">
            <h3 className="font-bold text-blue-900 mb-2 flex items-center gap-2">
              <Package size={20} /> Fulfillment Status
            </h3>
            <p className="text-sm text-blue-700">
              Your custom shade is now queued for Formlabs SLA production. 
              The <strong>{hardware}</strong> hardware kit is also confirmed and will ship independently from our fulfillment partner. Both items were fully paid for in this single checkout.
            </p>
          </div>

          <button onClick={() => window.location.href='/'} className="w-full bg-slate-900 text-white font-bold py-3 rounded-xl hover:bg-slate-800 transition">
            Create Another Lamp
          </button>
        </div>

      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SuccessContent />
    </Suspense>
  );
}
