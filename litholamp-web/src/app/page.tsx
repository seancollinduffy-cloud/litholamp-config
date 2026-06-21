"use client";

import React, { useState, useEffect } from 'react';
import { Loader2, Lightbulb, ChevronLeft, ChevronRight, UploadCloud } from 'lucide-react';
import { ThreeDViewer } from '../components/ThreeDViewer';

export default function LitholampPage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('');
  const [isPricing, setIsPricing] = useState(false);
  const [imageAspect, setImageAspect] = useState<number | null>(null);
  
  const hardwareOptions = ['RoundWoodBase', 'SquareWoodBase', 'DarkWoodBase', 'TiffanyDesk', 'TiffanyFloor'];
  const [hardware, setHardware] = useState<string>('RoundWoodBase');
  
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => setTouchStart(e.targetTouches[0].clientX);
  const handleTouchMove = (e: React.TouchEvent) => setTouchEnd(e.targetTouches[0].clientX);
  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const idx = hardwareOptions.indexOf(hardware);
    if (distance > 50) { // Swiped left -> next
      setHardware(hardwareOptions[(idx + 1) % hardwareOptions.length]);
    } else if (distance < -50) { // Swiped right -> prev
      setHardware(hardwareOptions[(idx - 1 + hardwareOptions.length) % hardwareOptions.length]);
    }
    setTouchStart(null);
    setTouchEnd(null);
  };
  
  useEffect(() => {
    if (imageSrc) {
      const img = new Image();
      img.onload = () => setImageAspect(img.width / img.height);
      img.src = imageSrc;
    } else {
      setImageAspect(null);
    }
  }, [imageSrc]);
  
  // Auto-mapped geometric properties
  const shapeMap: Record<string, string> = { RoundWoodBase: 'Cylinder', SquareWoodBase: 'Square', DarkWoodBase: 'Cylinder', TiffanyDesk: 'Tiffany', TiffanyFloor: 'Tiffany' };
  const sidesMap: Record<string, number> = { Cylinder: 1, Square: 4, Tiffany: 1 };
  const diameterMap: Record<string, number> = { RoundWoodBase: 90, SquareWoodBase: 90, DarkWoodBase: 90, TiffanyDesk: 140, TiffanyFloor: 194 };
  const heightMap: Record<string, number> = { 
    RoundWoodBase: 120, 
    SquareWoodBase: imageAspect ? (80 / imageAspect) + 10 : 120, 
    DarkWoodBase: 120, 
    TiffanyDesk: 140, 
    TiffanyFloor: 180 
  };

  const shape = shapeMap[hardware] || 'Cylinder';
  const sides = sidesMap[shape] || 1;
  const diameter = diameterMap[hardware] || 90;
  const height = heightMap[hardware] || 120;

  const prevHardware = hardwareOptions[(hardwareOptions.indexOf(hardware) - 1 + hardwareOptions.length) % hardwareOptions.length];
  const nextHardware = hardwareOptions[(hardwareOptions.indexOf(hardware) + 1) % hardwareOptions.length];

  const prevShape = shapeMap[prevHardware] || 'Cylinder';
  const prevDiameter = diameterMap[prevHardware] || 90;
  const prevHeight = heightMap[prevHardware] || 120;

  const nextShape = shapeMap[nextHardware] || 'Cylinder';
  const nextDiameter = diameterMap[nextHardware] || 90;
  const nextHeight = heightMap[nextHardware] || 120;

  
  const [jobId, setJobId] = useState<string | null>(null);
  const [thickness, setThickness] = useState(3.0);
  const [brightness, setBrightness] = useState(1.5);
  
  // Pricing State
  const [hardwareCost, setHardwareCost] = useState<number>(0);
  const [printCost, setPrintCost] = useState<number>(0);
  const [totalCost, setTotalCost] = useState<number>(0);
  const [pricingError, setPricingError] = useState<string | null>(null);

  const [generatedStlUrl, setGeneratedStlUrl] = useState<string | null>(null);

  // Update STL instantly when hardware changes!
  useEffect(() => {
    if (jobId) {
      setGeneratedStlUrl(`/api/download/${jobId}?hw=${hardware}`);
    }
  }, [jobId, hardware]);

  // Live Pricing Fetcher
  useEffect(() => {
    const fetchPrice = async () => {
      // Calculate approximate volume in mm3
      const radius = diameter / 2;
      const innerRadius = radius - thickness;
      const shellArea = Math.PI * (radius * radius - innerRadius * innerRadius);
      const wallVolume = shellArea * height;
      const roofFloorVolume = Math.PI * radius * radius * 5.5; // 2mm roof + 3.5mm floor approx
      const volume_mm3 = wallVolume + roofFloorVolume;

      setIsPricing(true);
      try {
        setPricingError(null);
        const res = await fetch(`/api/price`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ hardware, volume_mm3, height })
        });
        
        if (!res.ok) {
            const errData = await res.json();
            setPricingError(errData.detail || "Failed to fetch live pricing.");
            setHardwareCost(0); setPrintCost(0); setTotalCost(0);
            return;
        }
        
        const data = await res.json();
        setHardwareCost(data.hardware_cost);
        setPrintCost(data.print_cost);
        setTotalCost(data.total_cost);
        
      } catch (err) {
        setPricingError("Network error fetching live pricing.");
        console.error("Failed to fetch price", err);
      } finally {
        setIsPricing(false);
      }
    };
    
    // Debounce pricing fetch to avoid spamming
    const timeout = setTimeout(fetchPrice, 500);
    return () => clearTimeout(timeout);
  }, [height, diameter, thickness, hardware]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert("Please upload a valid image file (JPEG, PNG). You uploaded a " + (file.name.split('.').pop()?.toUpperCase() || 'unknown file') + ".");
        return;
      }
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setImageSrc(event.target?.result as string);
        setStep(2); // Auto-advance to Editor
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateSTL = async () => {
    setIsGenerating(true);
    setGenerationStatus('Compiling Mesh...');
    setGeneratedStlUrl(null);
    setJobId(null);
    
    try {
      const formData = new FormData();
      formData.append('hardware', hardware);
      formData.append('shape', shape);
      formData.append('sides', sides.toString());
      formData.append('height', height.toString());
      formData.append('diameter', diameter.toString());
      formData.append('thickness', thickness.toString());
      if (imageFile) {
        formData.append('files', imageFile);
      }

      const res = await fetch(`/api/generate`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      
      if (data.job_id) {
        setJobId(data.job_id);
        setGenerationStatus('Complete');
      } else {
        setGenerationStatus('Failed to generate.');
      }
    } catch(e) {
      console.error(e);
      setGenerationStatus('API unreachable.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Auto-generate when image is uploaded
  useEffect(() => {
    if (imageFile) {
      handleGenerateSTL();
    }
  }, [imageFile]);

  const handleCheckout = async () => {
    if (!jobId) {
      alert("Please wait for STL generation!");
      return;
    }
    setIsGenerating(true);
    setGenerationStatus('Redirecting to Stripe...');
    try {
      const res = await fetch(`/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          hardware: hardware,
          type: 'lithophane',
          height: heightMap[hardware] || 120.0
        })
      });
      const data = await res.json();
      if(data.url) {
        window.location.href = data.url;
      }
    } catch (e) {
       setGenerationStatus('API unreachable. Mocking redirect...');
       window.location.href = `/success?hardware=${hardware}&job_id=${jobId}`;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <nav className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 p-2 rounded-lg text-white">
            <Lightbulb size={24} />
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-800">LithoLamp<span className="text-blue-600">Pro</span></span>
        </div>
        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-widest">Creator Studio</span>
      </nav>

      {step === 1 && (
        <div className="flex flex-col items-center justify-center min-h-[85vh] p-6">
          <div className="max-w-3xl w-full text-center">
            <h1 className="text-5xl lg:text-6xl font-extrabold text-slate-900 mb-6 tracking-tight">
              Design Your Perfect <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Lithophane Lamp</span>
            </h1>
            <p className="text-xl text-slate-600 mb-12 max-w-2xl mx-auto leading-relaxed">
              Upload a photo and our engine will instantly carve it into a beautiful, 3D printable lamp shade wrapped perfectly to fit our curated selection of hardware bases.
            </p>
            
            <label className="flex flex-col items-center justify-center w-full max-w-xl mx-auto h-[350px] border-4 border-dashed border-blue-200 rounded-[2rem] bg-white hover:bg-blue-50/50 hover:border-blue-400 transition-all cursor-pointer shadow-sm hover:shadow-xl group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-blue-50/20 pointer-events-none"></div>
              <div className="bg-blue-100 text-blue-600 p-6 rounded-full mb-6 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300 shadow-sm">
                <UploadCloud size={48} />
              </div>
              <span className="text-2xl font-bold text-slate-800">Upload Photo</span>
              <span className="text-base text-slate-500 mt-2">JPEG, PNG, or HEIC (Up to 20MB)</span>
              <input type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="fixed inset-0 top-[73px] bg-slate-950 flex flex-col z-0">
          <div className="flex-1 relative overflow-hidden flex items-center justify-center">
            
            {/* Left Preview */}
            <div className="absolute inset-y-0 left-0 w-[20%] md:w-1/3 opacity-30 scale-[0.6] blur-[2px] pointer-events-none transition-all duration-700 z-20" style={{ maskImage: 'radial-gradient(circle, black 30%, transparent 70%)', WebkitMaskImage: 'radial-gradient(circle, black 30%, transparent 70%)' }}>
                <ThreeDViewer stlUrl={null} fallbackImage={imageSrc} generationType="lithophane" params={{ height: prevHeight, diameter: prevDiameter, thickness, brightness, hardware: prevHardware, shape: prevShape }} />
            </div>

            {/* Main Viewer */}
            <div className="absolute inset-0 z-10 transition-all duration-500" style={{ maskImage: 'radial-gradient(circle, black 60%, transparent 100%)', WebkitMaskImage: 'radial-gradient(circle, black 60%, transparent 100%)' }}>
                <ThreeDViewer stlUrl={generatedStlUrl} fallbackImage={imageSrc} generationType="lithophane" params={{ height, diameter, thickness, brightness, hardware, shape }} />
            </div>

            {/* Right Preview */}
            <div className="absolute inset-y-0 right-0 w-[20%] md:w-1/3 opacity-30 scale-[0.6] blur-[2px] pointer-events-none transition-all duration-700 z-20" style={{ maskImage: 'radial-gradient(circle, black 30%, transparent 70%)', WebkitMaskImage: 'radial-gradient(circle, black 30%, transparent 70%)' }}>
                <ThreeDViewer stlUrl={null} fallbackImage={imageSrc} generationType="lithophane" params={{ height: nextHeight, diameter: nextDiameter, thickness, brightness, hardware: nextHardware, shape: nextShape }} />
            </div>
            
            {/* Status Overlay */}
            {(isGenerating || isPricing) && (
              <div className="absolute top-8 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-md px-6 py-3 rounded-full flex items-center gap-3 text-sm font-bold text-slate-800 shadow-2xl animate-pulse z-50">
                <Loader2 className="animate-spin text-blue-600" size={18} />
                {isGenerating ? generationStatus : 'Calculating estimated print costs...'}
              </div>
            )}
          </div>

          {/* Hardware Carousel */}
          <div 
            className="bg-slate-950 py-6 border-b border-slate-800 w-full overflow-hidden z-20 shadow-[0_-10px_30px_rgba(0,0,0,0.5)] cursor-grab active:cursor-grabbing"
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
          >
            <div className="flex justify-center items-center gap-4 px-6 mx-auto w-full max-w-4xl relative">
              
              {/* Previous Item (Left) */}
              <div 
                onClick={() => setHardware(prevHardware)}
                className="opacity-40 scale-[0.6] md:scale-75 hover:opacity-70 transition-all duration-300 cursor-pointer"
              >
                <div className="bg-slate-900/50 border border-white/5 px-2 md:px-6 py-2 md:py-3 rounded-2xl text-center min-w-[120px] md:min-w-[200px]">
                  <div className="text-white font-bold text-sm md:text-lg tracking-tight mb-1 truncate">
                    {prevHardware.replace('WoodBase', ' Base').replace('Desk', ' Desk').replace('Floor', ' Floor')}
                  </div>
                </div>
              </div>

              {/* Current Item (Center) */}
              <div className="bg-slate-900/90 backdrop-blur-xl border border-white/20 px-10 py-5 rounded-3xl text-center min-w-[280px] md:min-w-[320px] shadow-2xl transform transition-all duration-300 scale-100 z-10">
                <div className="text-white font-extrabold text-2xl tracking-tight mb-1 truncate">{hardware.replace('WoodBase', ' Base').replace('Desk', ' Desk').replace('Floor', ' Floor')}</div>
                <div className="text-blue-400 text-sm font-bold uppercase tracking-widest">{shapeMap[hardware]} Frame</div>
                <div className="text-slate-500 text-xs mt-2 md:hidden">Swipe to explore</div>
              </div>

              {/* Next Item (Right) */}
              <div 
                onClick={() => setHardware(nextHardware)}
                className="opacity-40 scale-[0.6] md:scale-75 hover:opacity-70 transition-all duration-300 cursor-pointer"
              >
                <div className="bg-slate-900/50 border border-white/5 px-2 md:px-6 py-2 md:py-3 rounded-2xl text-center min-w-[120px] md:min-w-[200px]">
                  <div className="text-white font-bold text-sm md:text-lg tracking-tight mb-1 truncate">
                    {nextHardware.replace('WoodBase', ' Base').replace('Desk', ' Desk').replace('Floor', ' Floor')}
                  </div>
                </div>
              </div>

            </div>
          </div>
            
            {/* Bottom Pricing & Buy Bar */}
            <div className="bg-white border-t border-slate-200 px-6 py-5 z-20 shadow-[0_-20px_40px_rgba(0,0,0,0.15)] relative">
              <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                <div>
                  <div className="text-slate-500 text-sm font-bold uppercase tracking-wider mb-1">Total Package Cost</div>
                  <div className="flex items-baseline gap-2">
                    {pricingError ? (
                        <div className="text-sm font-bold text-red-500 max-w-[300px] break-words">{pricingError}</div>
                    ) : (
                        <>
                            <div className="text-4xl font-extrabold text-slate-900">
                                {isPricing ? <Loader2 className="animate-spin inline text-blue-600" size={32} /> : `$${totalCost.toFixed(2)}`}
                            </div>
                            <div className="text-sm font-bold text-slate-500 tracking-wide uppercase">+ Shipping (Estimated)</div>
                        </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <button onClick={() => { setStep(1); setImageFile(null); setImageSrc(null); setGeneratedStlUrl(null); }} className="px-6 py-4 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-colors">
                    Upload New Photo
                  </button>
                  <button 
                    onClick={handleCheckout}
                    disabled={!generatedStlUrl || isGenerating || isPricing}
                    className={`px-12 py-4 text-white font-extrabold text-lg rounded-2xl flex items-center justify-center gap-2 transition-all shadow-xl ${
                      !generatedStlUrl || isGenerating || isPricing ? 'bg-slate-300 text-slate-500 cursor-not-allowed shadow-none' : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 hover:scale-[1.02] hover:shadow-2xl hover:shadow-blue-500/30'
                    }`}
                  >
                     {isGenerating ? 'Generating...' : isPricing ? 'Calculating Estimate...' : 'Buy Custom Lamp'}
                  </button>
                </div>
              </div>
            </div>
          </div>
      )}
    </div>
  );
}
