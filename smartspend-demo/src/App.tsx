import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Mic, FileText, Keyboard, LayoutDashboard, Send, 
  TrendingUp, DollarSign, ShieldAlert, Award, FileSpreadsheet, 
  ArrowRight, User, Settings, CheckCircle2, ChevronRight, 
  Play, RefreshCw, X, AlertTriangle, AlertCircle, Check, 
  HelpCircle, Volume2, ShieldCheck, Landmark, Briefcase, FileInput, 
  Calendar, Layers, Clock, Users, ArrowUpRight, ArrowDownRight, Menu
} from 'lucide-react';

// Define the Scene IDs and names
const SCENES = [
  { id: 1, name: "Scene 1: Microsoft SSO Login" },
  { id: 2, name: "Scene 2: Employee Dashboard" },
  { id: 3, name: "Scene 3: Voice Assistant Modal" },
  { id: 4, name: "Scene 4: AI Parsed Request" },
  { id: 5, name: "Scene 5: Budget Validation" },
  { id: 6, name: "Scene 6: Contract Check" },
  { id: 7, name: "Scene 7: Vendor Discovery" },
  { id: 8, name: "Scene 8: RFQ Comparison Matrix" },
  { id: 9, name: "Scene 9: AI Negotiation Lounge" },
  { id: 10, name: "Scene 10: Manager Approval" },
  { id: 11, name: "Scene 11: Amazon-Style Tracking" },
  { id: 12, name: "Scene 12: CEO spend Analytics & Fraud Logs" }
];

interface ChatMessage {
  sender: 'ai' | 'vendor';
  text: string;
  timestamp: string;
}

export default function App() {
  // Global States
  const [activeScene, setActiveScene] = useState<number>(1);
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  
  // Login State
  const [isSsoLoading, setIsSsoLoading] = useState<boolean>(false);
  const [userRole, setUserRole] = useState<string>("Employee"); // Employee, Manager, SCM Buyer, CEO
  
  // Voice state
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'processing' | 'done'>('idle');
  const [voiceSeconds, setVoiceSeconds] = useState<number>(0);
  const [speechText, setSpeechText] = useState<string>("");
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Parsed Request State
  const [productName, setProductName] = useState<string>("Dell Latitude Laptops");
  const [productQty, setProductQty] = useState<number>(20);
  const [targetPrice, setTargetPrice] = useState<number>(70000);
  const [location, setLocation] = useState<string>("Bangalore Office");
  const [expenseCategory, setExpenseCategory] = useState<string>("IT Hardware & Laptops");
  
  // Budget State
  const [budgetBreach, setBudgetBreach] = useState<boolean>(false);
  const [budgetAction, setBudgetAction] = useState<string>("default"); // default, transfer, split, emergency
  
  // Sourcing & Contract State
  const [hasContract, setHasContract] = useState<boolean>(false);
  const [draftPartnerCreated, setDraftPartnerCreated] = useState<boolean>(false);
  const [selectedVendor, setSelectedVendor] = useState<string>("Primus Technologies");
  
  // AI Negotiation State
  const [negotiationStep, setNegotiationStep] = useState<number>(0);
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [currentOfferPrice, setCurrentOfferPrice] = useState<number>(68000);
  const [negotiationComplete, setNegotiationComplete] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  
  // Approval & Timeline State
  const [isApproved, setIsApproved] = useState<boolean>(false);
  
  // Voice simulation messages
  const sampleTranscript = "I need twenty Dell Latitude laptops under seventy thousand rupees each for the Bangalore office.";
  
  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog]);
  
  // Voice Recording simulation timer
  useEffect(() => {
    if (voiceState === 'listening') {
      setVoiceSeconds(0);
      timerRef.current = setInterval(() => {
        setVoiceSeconds(prev => {
          if (prev >= 4) {
            clearInterval(timerRef.current!);
            setVoiceState('processing');
            simulateProcessing();
            return 4;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [voiceState]);
  
  const simulateProcessing = () => {
    setTimeout(() => {
      setSpeechText(sampleTranscript);
      setVoiceState('done');
    }, 1500);
  };
  
  const startRecording = () => {
    setVoiceState('listening');
    setSpeechText("");
  };
  
  const resetVoiceModal = () => {
    setVoiceState('idle');
    setVoiceSeconds(0);
    setSpeechText("");
  };
  
  // AI Negotiation Simulation Step-by-Step
  const triggerNextNegotiationStep = () => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    if (negotiationStep === 0) {
      setChatLog([
        { sender: 'ai', text: "Hello Primus Sales Bot. We are looking to place an immediate order for 20 Dell Latitude laptops. Your catalog price is listed at ₹68,000. Under our standard volume discount agreement, we are requesting a final target price of ₹64,000 with Net-30 payment terms.", timestamp }
      ]);
      setNegotiationStep(1);
    } else if (negotiationStep === 1) {
      setChatLog(prev => [
        ...prev,
        { sender: 'vendor', text: "Thank you for reaching out. We appreciate the volume request. However, due to supply chain constraints on the Dell Latitude series, our absolute bottom margin is ₹66,500 for a quantity of 20 units. Alternatively, we can offer the requested ₹64,000 price if we adjust payment terms to Net-7 advance.", timestamp }
      ]);
      setNegotiationStep(2);
    } else if (negotiationStep === 2) {
      setChatLog(prev => [
        ...prev,
        { sender: 'ai', text: "Our corporate finance policy mandates Net-30 payment terms for compliance auditing. Can we compromise at ₹65,000 per unit under Net-30 terms, and in exchange, we will commit to Primus Technologies as our primary supplier for the upcoming Q3 hardware refresh?", timestamp }
      ]);
      setNegotiationStep(3);
    } else if (negotiationStep === 3) {
      setChatLog(prev => [
        ...prev,
        { sender: 'vendor', text: "Understood. The primary supplier status for Q3 is highly valuable to us. We accept the counter-offer: ₹65,000 per unit, Net-30 terms, including 3 Years On-Site Support. I will register this rate contract in Odoo immediately.", timestamp }
      ]);
      setCurrentOfferPrice(65000);
      setNegotiationComplete(true);
      setNegotiationStep(4);
    }
  };
  
  const resetNegotiation = () => {
    setChatLog([]);
    setNegotiationStep(0);
    setCurrentOfferPrice(68000);
    setNegotiationComplete(false);
  };
  
  // Trigger MS SSO Login simulation
  const handleSsoLogin = () => {
    setIsSsoLoading(true);
    setTimeout(() => {
      setIsSsoLoading(false);
      setActiveScene(2); // Go to Dashboard
    }, 1200);
  };
  
  // Quick navigation
  const nextScene = () => {
    if (activeScene < 12) {
      setActiveScene(activeScene + 1);
    }
  };
  
  const prevScene = () => {
    if (activeScene > 1) {
      setActiveScene(activeScene - 1);
    }
  };
  
  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${darkMode ? 'bg-[#0b0f19] text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      
      {/* --- SCENE 1: LOGIN (FULL SCREEN OVERLAY) --- */}
      {activeScene === 1 && (
        <div className="flex-grow flex flex-col lg:flex-row min-h-screen">
          {/* Left Panel: Brand & Tagline */}
          <div className="lg:w-7/12 bg-gradient-to-tr from-[#0F172A] via-[#1E1B4B] to-[#311042] flex flex-col justify-between p-8 lg:p-16 text-white relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(99,102,241,0.15),transparent)] pointer-events-none" />
            <div className="z-10 flex items-center space-x-2">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <span className="font-outfit text-2xl font-bold tracking-tight">SmartSpend</span>
            </div>
            
            <div className="z-10 my-auto py-12 max-w-xl">
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 uppercase tracking-widest">
                AI Orchestration Gateway
              </span>
              <h1 className="font-outfit text-4xl lg:text-6xl font-extrabold tracking-tight mt-6 leading-tight">
                Request Anything.<br />
                <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Track Everything.</span>
              </h1>
              <p className="text-slate-300 text-lg mt-6 leading-relaxed">
                Experience corporate procurement simplified. SmartSpend abstracts complex Odoo ERP processes into a single, intelligent workspace. No forms, no jargon, no training required.
              </p>
              
              <div className="grid grid-cols-2 gap-6 mt-12 pt-12 border-t border-slate-800">
                <div>
                  <h3 className="font-outfit font-bold text-white text-base">Zero ERP Complexity</h3>
                  <p className="text-sm text-slate-400 mt-2">All database rules and cost codes are managed behind the scenes by AI.</p>
                </div>
                <div>
                  <h3 className="font-outfit font-bold text-white text-base">Conversational Workflows</h3>
                  <p className="text-sm text-slate-400 mt-2">Just speak or type your requirements. The platform takes care of the rest.</p>
                </div>
              </div>
            </div>
            
            <div className="z-10 flex items-center justify-between text-xs text-slate-500">
              <span>Powered by Odoo ERP Backend</span>
              <span>CONFIDENTIAL PROTOTYPE</span>
            </div>
          </div>
          
          {/* Right Panel: SSO Login UI */}
          <div className="lg:w-5/12 flex flex-col justify-center px-6 py-12 md:px-16 lg:px-20 bg-slate-900 border-l border-slate-800">
            <div className="max-w-md w-full mx-auto space-y-8">
              <div>
                <h2 className="font-outfit text-3xl font-extrabold text-white tracking-tight">Sign In</h2>
                <p className="mt-3 text-sm text-slate-400">
                  Authenticate via your secure corporate gateway to access SmartSpend.
                </p>
              </div>
              
              <div className="space-y-4">
                <button
                  onClick={handleSsoLogin}
                  disabled={isSsoLoading}
                  className="w-full flex items-center justify-center space-x-3 py-3.5 px-4 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 text-white font-medium shadow-sm transition-all duration-200"
                >
                  {isSsoLoading ? (
                    <div className="h-5 w-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <svg className="h-5 w-5" viewBox="0 0 23 23" fill="currentColor">
                        <path fill="#f35325" d="M1 1h10v10H1z" />
                        <path fill="#81bc06" d="M12 1h10v10H12z" />
                        <path fill="#05a6f0" d="M1 12h10v10H1z" />
                        <path fill="#ffba08" d="M12 12h10v10H12z" />
                      </svg>
                      <span>Continue with Microsoft SSO</span>
                    </>
                  )}
                </button>
                
                <div className="relative flex py-4 items-center">
                  <div className="flex-grow border-t border-slate-800"></div>
                  <span className="flex-shrink mx-4 text-slate-500 text-xs font-semibold uppercase tracking-wider">or test accounts</span>
                  <div className="flex-grow border-t border-slate-800"></div>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => { setUserRole("Employee"); handleSsoLogin(); }}
                    className="p-3 bg-slate-800/50 hover:bg-indigo-600/20 border border-slate-800 hover:border-indigo-500/30 rounded-xl text-center text-xs text-slate-300 font-medium transition-all"
                  >
                    Employee Portal
                  </button>
                  <button 
                    onClick={() => { setUserRole("Manager"); handleSsoLogin(); }}
                    className="p-3 bg-slate-800/50 hover:bg-amber-600/20 border border-slate-800 hover:border-amber-500/30 rounded-xl text-center text-xs text-slate-300 font-medium transition-all"
                  >
                    Manager Inbox
                  </button>
                  <button 
                    onClick={() => { setUserRole("SCM Buyer"); handleSsoLogin(); }}
                    className="p-3 bg-slate-800/50 hover:bg-purple-600/20 border border-slate-800 hover:border-purple-500/30 rounded-xl text-center text-xs text-slate-300 font-medium transition-all col-span-2"
                  >
                    Procurement Buyer Dashboard
                  </button>
                </div>
              </div>
              
              <div className="text-center">
                <span className="text-xs text-slate-650">
                  By signing in, you agree to our Terms of Service & Privacy Standards.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* --- SCENES 2 - 12: INTEGRATED DEMO DASHBOARD LAYOUT --- */}
      {activeScene > 1 && (
        <div className="flex-grow flex overflow-hidden h-screen">
          
          {/* LEFT SIDEBAR */}
          {sidebarOpen && (
            <aside className={`w-64 flex-shrink-0 flex flex-col justify-between border-r ${darkMode ? 'bg-[#0f1422] border-slate-800' : 'bg-white border-slate-200'}`}>
              <div>
                {/* Brand Logo Header */}
                <div className="p-6 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center">
                      <Sparkles className="h-4.5 w-4.5 text-white" />
                    </div>
                    <span className="font-outfit font-bold text-lg tracking-tight">SmartSpend</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-semibold uppercase tracking-wider border border-indigo-500/25">V1.0</span>
                </div>
                
                {/* Current Role Indicator */}
                <div className="mx-4 mb-4 p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 flex items-center space-x-3">
                  <div className="h-8 w-8 rounded-full bg-slate-700 flex items-center justify-center text-slate-300 font-bold text-sm">
                    {userRole[0]}
                  </div>
                  <div className="overflow-hidden">
                    <p className="text-xs text-slate-400 font-medium">Logged in as:</p>
                    <p className="text-xs text-white font-bold truncate">{userRole}</p>
                  </div>
                </div>
                
                {/* Navigation Items */}
                <nav className="px-3 space-y-1">
                  <button 
                    onClick={() => setActiveScene(2)}
                    className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeScene === 2 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                  >
                    <LayoutDashboard className="h-4.5 w-4.5" />
                    <span>Dashboard</span>
                  </button>
                  <button 
                    onClick={() => setActiveScene(10)}
                    className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeScene === 10 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                  >
                    <CheckCircle2 className="h-4.5 w-4.5" />
                    <span>Approvals</span>
                    <span className="ml-auto bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs px-2 py-0.5 rounded-full font-bold">1</span>
                  </button>
                  <button 
                    onClick={() => setActiveScene(7)}
                    className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeScene === 7 || activeScene === 8 || activeScene === 9 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                  >
                    <Briefcase className="h-4.5 w-4.5" />
                    <span>Sourcing Portal</span>
                  </button>
                  <button 
                    onClick={() => setActiveScene(11)}
                    className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeScene === 11 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                  >
                    <Clock className="h-4.5 w-4.5" />
                    <span>My Requests</span>
                  </button>
                  <button 
                    onClick={() => setActiveScene(12)}
                    className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeScene === 12 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                  >
                    <TrendingUp className="h-4.5 w-4.5" />
                    <span>Spend Analytics</span>
                  </button>
                </nav>
              </div>
              
              {/* Bottom Quick Controls */}
              <div className="p-4 space-y-3 border-t border-slate-850">
                <div className="flex items-center justify-between text-xs text-slate-500 px-2">
                  <span>Theme</span>
                  <button 
                    onClick={() => setDarkMode(!darkMode)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    {darkMode ? 'Light' : 'Dark'}
                  </button>
                </div>
                
                <button
                  onClick={() => setActiveScene(1)}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg border border-slate-800 bg-slate-850 hover:bg-slate-800 text-xs text-slate-400 hover:text-white font-medium transition-all"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Logout / Reset</span>
                </button>
              </div>
            </aside>
          )}
          
          {/* MAIN WORKSPACE CONTENT */}
          <main className="flex-grow flex flex-col min-w-0 overflow-y-auto">
            
            {/* TOP NAVIGATION HEADER */}
            <header className={`h-16 px-6 border-b flex items-center justify-between flex-shrink-0 ${darkMode ? 'bg-[#0f1422] border-slate-800' : 'bg-white border-slate-200'}`}>
              <div className="flex items-center space-x-4">
                <button 
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
                >
                  <Menu className="h-5 w-5" />
                </button>
                <div className="h-4 w-[1px] bg-slate-750" />
                
                {/* Scene Indicator for Testing */}
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-semibold text-slate-405 text-indigo-400">DEMO STEP:</span>
                  <select 
                    value={activeScene}
                    onChange={(e) => setActiveScene(Number(e.target.value))}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-white font-bold"
                  >
                    {SCENES.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Demo Mode Actions */}
              <div className="flex items-center space-x-3">
                <button 
                  onClick={prevScene} 
                  disabled={activeScene === 2}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-750 text-white disabled:opacity-30 transition-all border border-slate-750"
                >
                  Back
                </button>
                <button 
                  onClick={nextScene}
                  disabled={activeScene === 12}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-30 transition-all flex items-center space-x-1"
                >
                  <span>Next Step</span>
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </header>
            
            {/* SCENE MAIN WORKSPACE */}
            <div className="p-6 md:p-8 flex-grow">
              
              {/* --- SCENE 2: DASHBOARD (CHOOSE TYPE) --- */}
              {activeScene === 2 && (
                <div className="space-y-8 animate-fadeIn">
                  {/* Headline */}
                  <div className="text-center py-6">
                    <h2 className="font-outfit text-3xl font-extrabold tracking-tight">How would you like to create a purchase request?</h2>
                    <p className="text-sm text-slate-400 mt-2">Just tell us what you need. AI will parse it and coordinate with Odoo automatically.</p>
                  </div>
                  
                  {/* Three Hero Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
                    {/* Voice Card (Highlight Hero) */}
                    <div 
                      onClick={() => setActiveScene(3)}
                      className="cursor-pointer group relative p-6 bg-gradient-to-tr from-indigo-900/30 via-indigo-950/20 to-purple-950/20 rounded-2xl border border-indigo-500/40 hover:border-indigo-400 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300 transform hover:-translate-y-1 flex flex-col justify-between h-56"
                    >
                      <div className="absolute top-4 right-4 h-2.5 w-2.5 rounded-full bg-indigo-400 animate-ping" />
                      <div className="h-12 w-12 rounded-xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30 text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
                        <Mic className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-outfit font-extrabold text-xl text-white group-hover:text-indigo-300 transition-colors">Voice Procurement</h3>
                        <p className="text-xs text-slate-400 mt-2">Speak naturally. Best for requests on mobile or when on the go.</p>
                      </div>
                    </div>
                    
                    {/* Type Card */}
                    <div 
                      onClick={() => setActiveScene(3)}
                      className="cursor-pointer group p-6 bg-slate-900/60 rounded-2xl border border-slate-800 hover:border-indigo-500/30 hover:shadow-xl transition-all transform hover:-translate-y-1 flex flex-col justify-between h-56"
                    >
                      <div className="h-12 w-12 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-750 text-slate-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
                        <Keyboard className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-outfit font-extrabold text-xl text-white group-hover:text-indigo-300 transition-colors">Type Request</h3>
                        <p className="text-xs text-slate-400 mt-2">Write a quick search-style message. Simple text extraction.</p>
                      </div>
                    </div>
                    
                    {/* Upload Card */}
                    <div 
                      onClick={() => setActiveScene(3)}
                      className="cursor-pointer group p-6 bg-slate-900/60 rounded-2xl border border-slate-800 hover:border-indigo-500/30 hover:shadow-xl transition-all transform hover:-translate-y-1 flex flex-col justify-between h-56"
                    >
                      <div className="h-12 w-12 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-750 text-slate-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-outfit font-extrabold text-xl text-white group-hover:text-indigo-300 transition-colors">Upload Requirement</h3>
                        <p className="text-xs text-slate-400 mt-2">Drag and drop a PDF, specification sheet, or vendor quote.</p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Dashboard Metrics widgets */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl mx-auto pt-6">
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                      <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold">
                        <Landmark className="h-4 w-4" />
                        <span>Budget Allocated</span>
                      </div>
                      <p className="text-2xl font-outfit font-bold text-white mt-1.5">₹1.5 Crore</p>
                    </div>
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                      <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold">
                        <DollarSign className="h-4 w-4" />
                        <span>Spent MTD</span>
                      </div>
                      <p className="text-2xl font-outfit font-bold text-white mt-1.5">₹45.89 Lakhs</p>
                    </div>
                    <div className="p-4 bg-[#10b981]/10 border border-[#10b981]/20 rounded-xl">
                      <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold">
                        <TrendingUp className="h-4 w-4" />
                        <span>AI Saved Capital</span>
                      </div>
                      <p className="text-2xl font-outfit font-bold text-emerald-400 mt-1.5">₹28.45 Lakhs</p>
                    </div>
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                      <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold">
                        <Users className="h-4 w-4" />
                        <span>Rate Contracts</span>
                      </div>
                      <p className="text-2xl font-outfit font-bold text-white mt-1.5">32 Agreements</p>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 3: VOICE ASSISTANT MODAL SIMULATOR --- */}
              {activeScene === 3 && (
                <div className="max-w-2xl mx-auto py-8 animate-fadeIn">
                  <div className="p-8 rounded-2xl border border-slate-800 bg-[#0f1422]/60 backdrop-blur-xl shadow-2xl space-y-8 relative overflow-hidden">
                    <div className="absolute top-4 right-4 flex items-center space-x-2">
                      <Volume2 className="h-4 w-4 text-indigo-400 animate-bounce" />
                      <span className="text-xs text-indigo-400 font-bold uppercase tracking-wider">Voice Portal</span>
                    </div>
                    
                    <div className="text-center space-y-2">
                      <h2 className="font-outfit text-2xl font-extrabold text-white">SmartSpend Voice Assistant</h2>
                      <p className="text-sm text-slate-400 max-w-md mx-auto">Click the microphone to simulate recording your purchase request details.</p>
                    </div>
                    
                    {/* Microphone Soundwave Visual Area */}
                    <div className="flex flex-col items-center justify-center py-6 space-y-4">
                      {voiceState === 'idle' && (
                        <button 
                          onClick={startRecording}
                          className="h-24 w-24 rounded-full bg-slate-800 hover:bg-indigo-600 text-slate-350 hover:text-white flex items-center justify-center shadow-lg border border-slate-700/50 transition-all duration-300 hover:scale-105"
                        >
                          <Mic className="h-10 w-10" />
                        </button>
                      )}
                      
                      {voiceState === 'listening' && (
                        <div className="flex flex-col items-center space-y-4">
                          <button 
                            onClick={() => setVoiceState('processing')}
                            className="h-24 w-24 rounded-full bg-indigo-600 text-white flex items-center justify-center relative shadow-2xl shadow-indigo-500/20"
                          >
                            <span className="absolute inset-0 rounded-full bg-indigo-500/40 animate-ping" />
                            <Mic className="h-10 w-10" />
                          </button>
                          
                          {/* Animated soundwaves */}
                          <div className="flex items-center space-x-1.5 h-10 py-1">
                            <div className="w-1 bg-indigo-400 rounded animate-[wave_0.8s_infinite_ease-in-out_delay-100] h-6" />
                            <div className="w-1 bg-indigo-300 rounded animate-[wave_0.8s_infinite_ease-in-out_delay-300] h-10" />
                            <div className="w-1 bg-indigo-400 rounded animate-[wave_0.8s_infinite_ease-in-out_delay-200] h-8" />
                            <div className="w-1 bg-indigo-500 rounded animate-[wave_0.8s_infinite_ease-in-out_delay-400] h-5" />
                            <div className="w-1 bg-indigo-300 rounded animate-[wave_0.8s_infinite_ease-in-out_delay-150] h-9" />
                          </div>
                          
                          <div className="text-center">
                            <span className="text-sm font-semibold text-indigo-400">Listening...</span>
                            <span className="text-xs text-slate-500 block mt-1">Simulated Duration: 0:0{voiceSeconds}</span>
                          </div>
                        </div>
                      )}
                      
                      {voiceState === 'processing' && (
                        <div className="flex flex-col items-center space-y-4">
                          <div className="h-24 w-24 rounded-full bg-indigo-900/40 border border-indigo-500/30 flex items-center justify-center">
                            <div className="h-8 w-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                          </div>
                          <div className="text-center">
                            <span className="text-sm font-semibold text-indigo-400">Transcribing Speech to Text...</span>
                            <span className="text-xs text-slate-500 block mt-1">Analyzing Intent &amp; Catalog entities</span>
                          </div>
                        </div>
                      )}
                      
                      {voiceState === 'done' && (
                        <div className="w-full space-y-4">
                          <div className="p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl">
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Converted Text:</p>
                            <p className="text-sm text-slate-200 mt-2 font-medium italic">"{speechText}"</p>
                          </div>
                          
                          <div className="flex justify-center space-x-3">
                            <button 
                              onClick={resetVoiceModal}
                              className="px-4 py-2 border border-slate-700 hover:bg-slate-800 text-xs font-semibold rounded-lg text-slate-300 transition-all"
                            >
                              Record Again
                            </button>
                            <button 
                              onClick={() => setActiveScene(4)}
                              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                            >
                              <span>Continue</span>
                              <ChevronRight className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {voiceState === 'idle' && (
                        <span className="text-sm text-slate-500 font-medium">Click to Speak Simulated Command</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 4: PARSED REQUEST FORM & ADDRESS --- */}
              {activeScene === 4 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">AI Parsed Requisition Form</h2>
                      <p className="text-xs text-slate-400">Review and edit the values extracted from your voice recording.</p>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/25 flex items-center space-x-1">
                      <ShieldCheck className="h-3 w-3" />
                      <span>98% Parse Confidence</span>
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Left Form: Editable details */}
                    <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                      <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">Extracted Parameters</h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="col-span-2">
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Product Description</label>
                          <input 
                            type="text" 
                            value={productName}
                            onChange={(e) => setProductName(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Quantity</label>
                          <input 
                            type="number" 
                            value={productQty}
                            onChange={(e) => setProductQty(Number(e.target.value))}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Target Price (per unit)</label>
                          <input 
                            type="number" 
                            value={targetPrice}
                            onChange={(e) => setTargetPrice(Number(e.target.value))}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Category (Mapped)</label>
                          <input 
                            type="text" 
                            value={expenseCategory}
                            onChange={(e) => setExpenseCategory(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Expense Type</label>
                          <span className="w-full bg-slate-800/50 border border-slate-750 rounded-lg p-2 text-sm text-slate-350 block">Capital Expenditure (CapEx)</span>
                        </div>
                      </div>
                      
                      <div className="pt-4 flex justify-end space-x-3">
                        <button onClick={() => setActiveScene(2)} className="px-4 py-2 text-xs text-slate-400 hover:text-white transition-all font-semibold">Cancel</button>
                        <button onClick={() => setActiveScene(5)} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all">Submit for Validation</button>
                      </div>
                    </div>
                    
                    {/* Right Card: Address Resolution Mappings */}
                    <div className="space-y-4">
                      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                        <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">Branch Mapped Addresses</h3>
                        
                        <div className="space-y-3">
                          <div>
                            <span className="text-[10px] text-slate-550 font-bold uppercase tracking-wider block mb-0.5">Input location:</span>
                            <span className="text-xs font-semibold text-slate-300">"{location}"</span>
                          </div>
                          
                          <div className="pt-2 border-t border-slate-800">
                            <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block">Resolved Bill-To Address</span>
                            <span className="text-xs text-slate-300 font-medium block mt-1">Kuttukaran Corporate HQ, Metro Pillar 32, Kochi, KL - 682025</span>
                            <span className="text-[9px] text-slate-500 block mt-0.5">GSTIN: 32AAAAB1234C1Z0</span>
                          </div>
                          
                          <div className="pt-2 border-t border-slate-800">
                            <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block">Resolved Ship-To Address</span>
                            <span className="text-xs text-slate-300 font-medium block mt-1">Kuttukaran Regional Warehouse, IT Park, Bangalore, KA - 560066</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-4 bg-indigo-950/20 border border-indigo-900/40 rounded-xl text-xs text-indigo-400 flex items-start space-x-2">
                        <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0" />
                        <span>SmartSpend automatically mapped the Bangalore region tag to the correct warehouse database index without requiring dropdown input.</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 5: BUDGET VALIDATION & BREACH OPTIONS --- */}
              {activeScene === 5 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white font-bold">Scene 5: Smart Budget Verification</h2>
                      <p className="text-xs text-slate-400">The platform cross-references available cost center funds in real-time.</p>
                    </div>
                    
                    {/* Simulator Switch */}
                    <div className="flex items-center space-x-3 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
                      <span className="font-semibold text-slate-350">Simulate Budget Status:</span>
                      <button 
                        onClick={() => { setBudgetBreach(false); setBudgetAction("default"); }}
                        className={`px-2 py-1 rounded font-bold ${!budgetBreach ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-400'}`}
                      >
                        Within Limit
                      </button>
                      <button 
                        onClick={() => { setBudgetBreach(true); }}
                        className={`px-2 py-1 rounded font-bold ${budgetBreach ? 'bg-rose-600 text-white' : 'bg-slate-700 text-slate-400'}`}
                      >
                        Limit Exceeded
                      </button>
                    </div>
                  </div>
                  
                  {/* Budget breakdown display */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                      <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">IT Hardware Cost Center (Q3 Budget)</h3>
                      
                      <div className="space-y-4">
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>Total Allocated Q3 Budget:</span>
                          <span className="font-bold text-slate-200">₹30,00,000</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>Committed Spend:</span>
                          <span className="font-bold text-slate-200">₹12,00,000</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>Current Request (20 Laptops):</span>
                          <span className="font-bold text-indigo-400">₹14,00,000</span>
                        </div>
                        
                        {/* Visual Bar Chart Mocks */}
                        <div className="relative pt-2">
                          <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden flex">
                            {/* MTD Spent */}
                            <div className="h-full bg-slate-500" style={{ width: '40%' }} />
                            {/* Requested */}
                            <div className={`h-full ${budgetBreach ? 'bg-rose-500' : 'bg-indigo-500'}`} style={{ width: budgetBreach ? '70%' : '46%' }} />
                          </div>
                          
                          <div className="flex justify-between text-[10px] text-slate-500 mt-1.5 font-semibold">
                            <span>0% MTD</span>
                            <span>40% Spent (₹12L)</span>
                            <span>{budgetBreach ? '110% Over (₹33L)' : '86% Used (₹26L)'}</span>
                            <span>100% (₹30L)</span>
                          </div>
                        </div>
                      </div>
                      
                      {/* Budget Outcomes */}
                      {!budgetBreach ? (
                        <div className="p-4 bg-emerald-950/20 border border-emerald-900/40 rounded-xl flex items-start space-x-3 text-emerald-400 text-xs">
                          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0 text-emerald-400" />
                          <div>
                            <p className="font-bold">Budget Verification Passed</p>
                            <p className="mt-1 text-slate-350">Funds are available. Mapped to Cost M-2026-IT. No pre-approvals required for budget allocation.</p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 bg-rose-950/20 border border-rose-900/40 rounded-xl flex items-start space-x-3 text-rose-400 text-xs">
                          <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0 text-rose-400 animate-pulse" />
                          <div>
                            <p className="font-bold">Budget Limit Exceeded by ₹2,00,000</p>
                            <p className="mt-1 text-slate-350">The requested ₹14,00,000 exceeds the remaining allocated IT hardware budget.</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="pt-2 flex justify-end space-x-3">
                        <button onClick={() => setActiveScene(4)} className="px-4 py-2 text-xs text-slate-400 font-semibold hover:text-white">Modify Request</button>
                        <button onClick={() => setActiveScene(6)} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all">Proceed to Sourcing Check</button>
                      </div>
                    </div>
                    
                    {/* Alternative Actions in case of Breach */}
                    <div className="space-y-4">
                      {budgetBreach && (
                        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 animate-fadeIn">
                          <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">AI Alternative Options</h3>
                          
                          <div className="space-y-3 text-xs">
                            <button 
                              onClick={() => setBudgetAction("transfer")}
                              className={`w-full text-left p-3 rounded-xl border transition-all ${budgetAction === 'transfer' ? 'bg-indigo-950/30 border-indigo-500 text-white' : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'}`}
                            >
                              <div className="flex items-center space-x-2 font-bold text-indigo-400">
                                <Landmark className="h-4 w-4" />
                                <span>1. Budget Transfer</span>
                              </div>
                              <p className="mt-1 text-[11px] text-slate-400">Initiate automated transfer of surplus ₹2,00,000 from Regional IT Office surplus.</p>
                            </button>
                            
                            <button 
                              onClick={() => setBudgetAction("split")}
                              className={`w-full text-left p-3 rounded-xl border transition-all ${budgetAction === 'split' ? 'bg-indigo-950/30 border-indigo-500 text-white' : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'}`}
                            >
                              <div className="flex items-center space-x-2 font-bold text-indigo-400">
                                <Layers className="h-4 w-4" />
                                <span>2. Split Purchase order</span>
                              </div>
                              <p className="mt-1 text-[11px] text-slate-400">Deliver 15 units this month and 5 units next month to balance quarterly quotas.</p>
                            </button>
                            
                            <button 
                              onClick={() => setBudgetAction("emergency")}
                              className={`w-full text-left p-3 rounded-xl border transition-all ${budgetAction === 'emergency' ? 'bg-indigo-950/30 border-indigo-500 text-white' : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'}`}
                            >
                              <div className="flex items-center space-x-2 font-bold text-indigo-400">
                                <ShieldAlert className="h-4 w-4" />
                                <span>3. CFO Exception Bypass</span>
                              </div>
                              <p className="mt-1 text-[11px] text-slate-400">Flag as "Operational Emergency" to request CEO exception approval.</p>
                            </button>
                          </div>
                        </div>
                      )}
                      
                      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-400">
                        <span className="font-bold text-slate-200 block mb-1">Audit Log:</span>
                        The system stores a permanent ledger record of all budget checks, alternatives suggested, and user selections for governance tracking in Odoo.
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 6: CONTRACT CHECK & ROUTING --- */}
              {activeScene === 6 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 6: Active Contract Search</h2>
                      <p className="text-xs text-slate-400">AI queries the Odoo registry for valid Rate Contracts or pricing agreements.</p>
                    </div>
                    
                    {/* Toggle Selector */}
                    <div className="flex items-center space-x-3 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
                      <span className="font-semibold text-slate-350">Active Contract exists?</span>
                      <button 
                        onClick={() => setHasContract(true)}
                        className={`px-2.5 py-1 rounded font-bold ${hasContract ? 'bg-[#10b981] text-white' : 'bg-slate-700 text-slate-400'}`}
                      >
                        Yes
                      </button>
                      <button 
                        onClick={() => setHasContract(false)}
                        className={`px-2.5 py-1 rounded font-bold ${!hasContract ? 'bg-amber-600 text-white' : 'bg-slate-700 text-slate-400'}`}
                      >
                        No
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                    {hasContract ? (
                      <div className="space-y-6 animate-fadeIn">
                        <div className="p-5 bg-emerald-950/20 border border-emerald-900/40 rounded-2xl flex items-start space-x-4">
                          <div className="h-12 w-12 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/25 text-emerald-400">
                            <ShieldCheck className="h-6 w-6" />
                          </div>
                          <div className="space-y-1">
                            <h3 className="font-outfit font-extrabold text-lg text-emerald-400">Active Rate Contract Mapped</h3>
                            <p className="text-sm text-slate-300">Found active agreement <strong>RC-2026-IT-09</strong> registered in Odoo for Dell Latitude series.</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
                          <div className="p-4 bg-slate-850/40 border border-slate-800 rounded-xl">
                            <span className="text-xs text-slate-500 font-bold block">Contract Vendor</span>
                            <span className="text-sm font-semibold text-white mt-1 block">Dell India Ltd</span>
                          </div>
                          <div className="p-4 bg-slate-850/40 border border-slate-800 rounded-xl">
                            <span className="text-xs text-slate-500 font-bold block">Pre-Negotiated Price</span>
                            <span className="text-sm font-semibold text-white mt-1 block">₹63,500 / unit</span>
                          </div>
                          <div className="p-4 bg-slate-850/40 border border-slate-800 rounded-xl">
                            <span className="text-xs text-slate-500 font-bold block">Delivery SLA</span>
                            <span className="text-sm font-semibold text-white mt-1 block">4 Business Days</span>
                          </div>
                          <div className="p-4 bg-slate-850/40 border border-slate-800 rounded-xl">
                            <span className="text-xs text-slate-550 font-bold block text-emerald-400">Negotiated Savings</span>
                            <span className="text-sm font-semibold text-emerald-400 mt-1 block">₹1,30,000 Saved</span>
                          </div>
                        </div>
                        
                        <div className="bg-indigo-950/20 border border-indigo-900/40 p-4 rounded-xl text-xs text-indigo-400 flex items-start space-x-2">
                          <Sparkles className="h-4.5 w-4.5 mt-0.5 flex-shrink-0" />
                          <span><strong>Fast-Path Trigger:</strong> Since an active contract exists, the sourcing approval matrix is bypassed. The system will skip quotation comparisons and route directly to Purchase Order Creation.</span>
                        </div>
                        
                        <div className="flex justify-end space-x-3 pt-2">
                          <button onClick={() => setActiveScene(11)} className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                            <span>Auto-Generate Purchase Order</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-6 animate-fadeIn">
                        <div className="p-5 bg-amber-950/25 border border-amber-900/45 rounded-2xl flex items-start space-x-4">
                          <div className="h-12 w-12 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/25 text-amber-400">
                            <AlertCircle className="h-6 w-6" />
                          </div>
                          <div className="space-y-1">
                            <h3 className="font-outfit font-extrabold text-lg text-amber-400">No Active Contract Found</h3>
                            <p className="text-sm text-slate-300">The product category does not have a pre-negotiated volume contract. Sourcing is required.</p>
                          </div>
                        </div>
                        
                        <p className="text-sm text-slate-400">
                          To satisfy compliance and secure the best pricing, SmartSpend will automatically delegate this request to SCM buyer queues and trigger vendor discovery.
                        </p>
                        
                        <div className="p-4 bg-slate-800/40 border border-slate-750/70 rounded-xl space-y-3">
                          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block">Auto-Routing Matrix Status</span>
                          <div className="flex items-center space-x-4 text-xs">
                            <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                              <Check className="h-4 w-4" />
                              <span>SCM Buyer Allocated (Workload check passed)</span>
                            </span>
                            <span className="flex items-center space-x-1 text-slate-400 font-medium">
                              <Check className="h-4 w-4" />
                              <span>Buyer ID: SCM-IT-14</span>
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex justify-end space-x-3 pt-2">
                          <button onClick={() => setActiveScene(7)} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                            <span>Launch Vendor Discovery</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* --- SCENE 7: VENDOR DISCOVERY & DRAFT CREATION --- */}
              {activeScene === 7 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 7: AI SCM Sourcing &amp; Discovery</h2>
                      <p className="text-xs text-slate-400">Auto-onboard and find new catalog suppliers based on product requirements.</p>
                    </div>
                    
                    <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 rounded-full text-xs font-bold flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>SCM Buyer Workload: 4 Tasks (Low)</span>
                    </span>
                  </div>
                  
                  {/* Vendor suggestions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {/* Supplier Card 1 */}
                    <div className="p-6 rounded-2xl bg-slate-900 border border-indigo-500/30 shadow-xl relative overflow-hidden flex flex-col justify-between h-72">
                      <div className="absolute top-4 right-4 bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider">
                        Recommended Match
                      </div>
                      
                      <div className="space-y-3">
                        <div className="flex items-center space-x-3">
                          <div className="h-10 w-10 rounded-lg bg-indigo-500/15 flex items-center justify-center border border-indigo-500/20 text-indigo-400 font-bold text-lg">P</div>
                          <div>
                            <h3 className="font-outfit font-extrabold text-lg text-white">Primus Technologies</h3>
                            <p className="text-xs text-slate-400">IT Solutions &amp; Infrastructure distributor</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs border-t border-b border-slate-800 py-3">
                          <div>
                            <span className="text-slate-500 block">AI Match Score:</span>
                            <span className="font-bold text-slate-200">94%</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Est. Lead Time:</span>
                            <span className="font-bold text-slate-200">5 Business Days</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Health Rating:</span>
                            <span className="font-bold text-slate-200">96 / 100</span>
                          </div>
                          <div>
                            <span className="text-slate-555 block text-indigo-400">Expected Price:</span>
                            <span className="font-bold text-indigo-400">₹68,000 / unit</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-semibold">Registered Draft Partner in Odoo</span>
                        <button 
                          onClick={() => { setSelectedVendor("Primus Technologies"); setDraftPartnerCreated(true); setActiveScene(8); }}
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all"
                        >
                          Select &amp; Compare
                        </button>
                      </div>
                    </div>
                    
                    {/* Supplier Card 2 */}
                    <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between h-72">
                      <div className="space-y-3">
                        <div className="flex items-center space-x-3">
                          <div className="h-10 w-10 rounded-lg bg-slate-800 flex items-center justify-center border border-slate-750 text-slate-400 font-bold text-lg">A</div>
                          <div>
                            <h3 className="font-outfit font-extrabold text-lg text-white">Apex Systems</h3>
                            <p className="text-xs text-slate-400">Corporate Hardware Reseller</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs border-t border-b border-slate-800 py-3">
                          <div>
                            <span className="text-slate-500 block">AI Match Score:</span>
                            <span className="font-bold text-slate-200">88%</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Est. Lead Time:</span>
                            <span className="font-bold text-slate-200">10 Business Days</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Health Rating:</span>
                            <span className="font-bold text-slate-200">90 / 100</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Expected Price:</span>
                            <span className="font-bold text-slate-200">₹71,000 / unit</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-semibold">B2B Directory Entry</span>
                        <button 
                          onClick={() => { setSelectedVendor("Apex Systems"); setDraftPartnerCreated(true); setActiveScene(8); }}
                          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-bold rounded-lg text-white transition-all"
                        >
                          Select &amp; Compare
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-450 flex items-start space-x-2">
                    <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0 text-indigo-400" />
                    <span><strong>Frictionless Intake:</strong> Selecting a vendor automatically populates basic business credentials (GST/PAN details fetched by AI) into a draft partner card. It sends a secure passwordless magic link to their bidding desk, bypassing legacy registration bottlenecks.</span>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 8: RFQ COMPARISON MATRIX --- */}
              {activeScene === 8 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 8: Side-by-Side RFQ Comparison</h2>
                      <p className="text-xs text-slate-400">Value scorecard generated from parsed vendor quotations (No PDF clutter).</p>
                    </div>
                    
                    <span className="px-3 py-1 bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 rounded-full text-xs font-bold flex items-center space-x-1">
                      <Award className="h-3.5 w-3.5" />
                      <span>Best Value: Primus Tech</span>
                    </span>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase font-bold tracking-wider">
                          <th className="py-3 px-4">Evaluation Criteria</th>
                          <th className="py-3 px-4 bg-indigo-950/20 text-indigo-400">Primus Technologies</th>
                          <th className="py-3 px-4">Apex Systems</th>
                        </tr>
                      </thead>
                      <tbody className="text-xs text-slate-300">
                        <tr className="border-b border-slate-800/50">
                          <td className="py-3 px-4 font-semibold">Unit Quote Price</td>
                          <td className="py-3 px-4 bg-indigo-950/15 font-bold text-white">₹68,000</td>
                          <td className="py-3 px-4">₹71,000</td>
                        </tr>
                        <tr className="border-b border-slate-800/50">
                          <td className="py-3 px-4 font-semibold">Warranty Terms</td>
                          <td className="py-3 px-4 bg-indigo-950/15">3 Years On-Site Support</td>
                          <td className="py-3 px-4">1 Year Carry-In Warranty</td>
                        </tr>
                        <tr className="border-b border-slate-800/50">
                          <td className="py-3 px-4 font-semibold">Delivery Timeframe</td>
                          <td className="py-3 px-4 bg-indigo-950/15 font-bold text-emerald-400">5 Business Days</td>
                          <td className="py-3 px-4">10 Business Days</td>
                        </tr>
                        <tr className="border-b border-slate-800/50">
                          <td className="py-3 px-4 font-semibold">Payment Milestones</td>
                          <td className="py-3 px-4 bg-indigo-950/15">Net-30 Audited Terms</td>
                          <td className="py-3 px-4">Net-15 Invoice Terms</td>
                        </tr>
                        <tr className="border-b border-slate-800/50">
                          <td className="py-3 px-4 font-semibold">Risk &amp; Health Score</td>
                          <td className="py-3 px-4 bg-indigo-950/15">Low Risk (Score: 96)</td>
                          <td className="py-3 px-4 text-amber-400 font-medium">Medium Risk (Score: 88)</td>
                        </tr>
                        <tr className="border-b border-slate-800/50">
                          <td className="py-3 px-4 font-semibold">AI Negotiation Potential</td>
                          <td className="py-3 px-4 bg-indigo-950/15 font-semibold text-indigo-400">5% Discount Opportunity Mapped</td>
                          <td className="py-3 px-4">Low Margin scope</td>
                        </tr>
                        <tr>
                          <td className="py-3 px-4 font-semibold">AI Recommendation</td>
                          <td className="py-3 px-4 bg-indigo-950/20">
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold text-[10px]">RECOMMENDED FIT</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-slate-500 font-medium">Not Recommended</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    
                    <div className="pt-6 flex justify-end space-x-3">
                      <button onClick={() => setActiveScene(7)} className="px-4 py-2 text-xs text-slate-400 font-semibold hover:text-white">Reselect Suppliers</button>
                      <button onClick={() => setActiveScene(9)} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                        <span>Trigger AI Negotiation</span>
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 9: AI NEGOTIATION LOUNGE --- */}
              {activeScene === 9 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 9: AI Autonomous Negotiation</h2>
                      <p className="text-xs text-slate-400">Watch the AI agent negotiate rates and terms directly with the supplier bot.</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="px-3 py-1 bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/25 rounded-full text-xs font-bold">
                        Savings: ₹{((68000 - currentOfferPrice) * 20).toLocaleString()} (₹{(68000 - currentOfferPrice).toLocaleString()}/unit)
                      </span>
                      <button 
                        onClick={resetNegotiation}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300"
                        title="Restart Negotiation"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Left chat console: 2 cols */}
                    <div className="md:col-span-2 flex flex-col h-[400px] rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
                      <div className="p-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
                        <span className="text-xs text-slate-200 font-bold uppercase tracking-wider">Live Agent Log</span>
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                      </div>
                      
                      {/* Messages scroll area */}
                      <div className="flex-grow p-4 overflow-y-auto space-y-4">
                        {chatLog.length === 0 ? (
                          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                            <div className="h-12 w-12 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                              <Sparkles className="h-6 w-6" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-300">Negotiation Lounge Ready</p>
                              <p className="text-xs text-slate-500 mt-1">Click the button below to simulate the AI autonomous pricing discussion.</p>
                            </div>
                          </div>
                        ) : (
                          chatLog.map((m, idx) => (
                            <div key={idx} className={`flex ${m.sender === 'ai' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                              <div className={`max-w-md p-3.5 rounded-2xl text-xs space-y-1 ${m.sender === 'ai' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-250 rounded-tl-none border border-slate-700/60'}`}>
                                <div className="flex items-center justify-between text-[9px] opacity-75 font-bold uppercase tracking-wider mb-1">
                                  <span>{m.sender === 'ai' ? '🤖 SmartSpend AI' : '👤 Primus Bot'}</span>
                                  <span>{m.timestamp}</span>
                                </div>
                                <p className="leading-relaxed">{m.text}</p>
                              </div>
                            </div>
                          ))
                        )}
                        <div ref={chatEndRef} />
                      </div>
                      
                      <div className="p-3 bg-slate-850/60 border-t border-slate-800 flex justify-between items-center">
                        <span className="text-[10px] text-slate-500">Autonomous API negotiation active</span>
                        {!negotiationComplete ? (
                          <button 
                            onClick={triggerNextNegotiationStep}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                          >
                            <span>{negotiationStep === 0 ? 'Start Agent Session' : 'Continue Negotiation'}</span>
                            <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        ) : (
                          <span className="text-xs text-emerald-400 font-bold flex items-center space-x-1">
                            <CheckCircle2 className="h-4 w-4" />
                            <span>Agreement Locked &amp; Confirmed</span>
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Right tracker dashboard details */}
                    <div className="space-y-4">
                      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                        <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">Deal Tracker</h3>
                        
                        <div className="space-y-3 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Original Quote:</span>
                            <span className="font-semibold text-slate-350">₹68,000 / unit</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Negotiated Rate:</span>
                            <span className="font-bold text-emerald-400">₹{currentOfferPrice.toLocaleString()} / unit</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Volume savings (20 Laptops):</span>
                            <span className="font-bold text-emerald-400">₹{((68000 - currentOfferPrice) * 20).toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-slate-800">
                            <span className="text-slate-500">Payment SLA:</span>
                            <span className="font-semibold text-slate-300">Net-30 (Audited)</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Warranty Mapped:</span>
                            <span className="font-semibold text-slate-300">3 Years On-Site (Inc.)</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-[11px] text-slate-400 leading-relaxed">
                        <span className="font-bold text-slate-200 block mb-1">Contract Auto-Registration:</span>
                        Confirming pricing automatically generates a new <strong>Rate Contract</strong> in Odoo, updating vendor lists and bypassing sourcing for subsequent purchases.
                      </div>
                      
                      {negotiationComplete && (
                        <button 
                          onClick={() => { setActiveScene(10); }}
                          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-xl text-white transition-all shadow-lg shadow-indigo-500/10 flex items-center justify-center space-x-2"
                        >
                          <span>Route to Manager Approval</span>
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 10: MANAGER APPROVAL INBOX --- */}
              {activeScene === 10 && (
                <div className="max-w-2xl mx-auto py-8 animate-fadeIn">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 10: Unified Approval Panel</h2>
                      <p className="text-xs text-slate-400">Simplifying decision metrics for managers. No dense database tables.</p>
                    </div>
                    
                    <span className="px-3 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/25 rounded-full text-xs font-bold">
                      Pending Action
                    </span>
                  </div>
                  
                  {/* Approval Card */}
                  <div className="p-6 rounded-2xl bg-slate-900 border border-indigo-500/30 shadow-2xl space-y-6">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                      <div className="flex items-center space-x-3">
                        <div className="h-10 w-10 rounded-full bg-slate-850 flex items-center justify-center text-slate-350 font-bold text-sm">AV</div>
                        <div>
                          <p className="text-xs text-slate-400">Requisition Initiator:</p>
                          <p className="text-sm font-bold text-white">Anjitha V (IT Ops Specialist)</p>
                        </div>
                      </div>
                      <span className="text-xs text-slate-400">Ref: PR-2026-089</span>
                    </div>
                    
                    <div className="space-y-4">
                      <h3 className="font-outfit font-bold text-white text-base">20x Dell Latitude 5440 Laptops</h3>
                      
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <span className="text-slate-500 block">Total cost:</span>
                          <span className="font-bold text-white">₹13,00,000</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-emerald-400">Negotiated Savings:</span>
                          <span className="font-bold text-emerald-400">₹60,000 Saved (5%)</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Budget Mapped:</span>
                          <span className="font-bold text-slate-300">IT Hardware (Q3 Budget Mapped)</span>
                        </div>
                        <div>
                          <span className="text-slate-555 block">Resolved Vendor:</span>
                          <span className="font-bold text-slate-300">Primus Technologies</span>
                        </div>
                      </div>
                      
                      <div className="p-4 bg-slate-800/40 border border-slate-750/70 rounded-xl space-y-2 text-xs">
                        <span className="text-xs text-indigo-400 font-bold block">AI Audit Summary:</span>
                        <div className="flex items-start space-x-2 text-slate-300">
                          <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                          <span>Within budget parameters (Passes 3-way check).</span>
                        </div>
                        <div className="flex items-start space-x-2 text-slate-300">
                          <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                          <span>Supplier health checked. Mapped as Approved Vendor.</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-end space-x-3 border-t border-slate-800 pt-4">
                      <button 
                        onClick={() => { setIsApproved(false); alert("Request Rejected"); }}
                        className="px-4 py-2 border border-slate-700 hover:bg-rose-900/20 hover:border-rose-500 text-xs font-semibold rounded-lg text-slate-300 hover:text-rose-400 transition-all"
                      >
                        Reject Requisition
                      </button>
                      <button 
                        onClick={() => { setIsApproved(true); setActiveScene(11); }}
                        className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                      >
                        <Check className="h-4.5 w-4.5" />
                        <span>Approve Request</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 11: AMAZON-STYLE ORDER TRACKING --- */}
              {activeScene === 11 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 11: Procurement Tracking Milestone</h2>
                      <p className="text-xs text-slate-400">Amazon-style simple progress tracker hiding deep transactional ERP states.</p>
                    </div>
                    
                    <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 rounded-full text-xs font-bold">
                      PO Confirmed: PO-2026-004
                    </span>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-8">
                    {/* Sleek timeline map */}
                    <div className="relative flex justify-between items-center max-w-2xl mx-auto py-4">
                      {/* Gray Connector Line */}
                      <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-slate-800 z-0" />
                      {/* Active green Connector Line */}
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-emerald-500 z-0" style={{ width: '40%' }} />
                      
                      {/* Node 1: Submitted */}
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs shadow-lg shadow-emerald-500/20">
                          <Check className="h-4 w-4" />
                        </div>
                        <div>
                          <span className="text-[10px] font-bold text-slate-200 block">Submitted</span>
                          <span className="text-[8px] text-slate-500 block">July 08, 08:30</span>
                        </div>
                      </div>
                      
                      {/* Node 2: Sourcing Approved */}
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs shadow-lg shadow-emerald-500/20">
                          <Check className="h-4 w-4" />
                        </div>
                        <div>
                          <span className="text-[10px] font-bold text-slate-200 block">Sourcing Approved</span>
                          <span className="text-[8px] text-slate-500 block">July 08, 08:38</span>
                        </div>
                      </div>
                      
                      {/* Node 3: PO Created */}
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs shadow-lg shadow-emerald-500/20">
                          <Check className="h-4 w-4" />
                        </div>
                        <div>
                          <span className="text-[10px] font-bold text-slate-200 block">PO Confirmed</span>
                          <span className="text-[8px] text-slate-500 block">July 08, 08:42</span>
                        </div>
                      </div>
                      
                      {/* Node 4: Transit */}
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 text-slate-500 flex items-center justify-center font-bold text-xs">
                          4
                        </div>
                        <div>
                          <span className="text-[10px] font-bold text-slate-400 block">In Transit</span>
                          <span className="text-[8px] text-slate-500 block">Pending</span>
                        </div>
                      </div>
                      
                      {/* Node 5: Match & Paid */}
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 text-slate-500 flex items-center justify-center font-bold text-xs">
                          5
                        </div>
                        <div>
                          <span className="text-[10px] font-bold text-slate-400 block">3-Way Match</span>
                          <span className="text-[8px] text-slate-500 block">Pending</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Underlying Odoo Transaction Cards (Accordion style) */}
                    <div className="border-t border-slate-800 pt-6 space-y-3 max-w-2xl mx-auto">
                      <h4 className="text-xs text-slate-500 font-bold uppercase tracking-wider">Underlying ERP Audit Trail</h4>
                      
                      <div className="p-3 bg-slate-850/40 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2">
                          <FileText className="h-4 w-4 text-indigo-400" />
                          <span className="font-semibold text-slate-200">Requisition Mapped:</span>
                          <span className="text-slate-400">PR-2026-089</span>
                        </div>
                        <span className="text-[10px] text-emerald-400 font-bold">Closed (Approved)</span>
                      </div>
                      
                      <div className="p-3 bg-slate-850/40 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2">
                          <CheckCircle2 className="h-4 w-4 text-indigo-400" />
                          <span className="font-semibold text-slate-200">Rate Contract registered:</span>
                          <span className="text-slate-400">RC-2026-IT-14</span>
                        </div>
                        <span className="text-[10px] text-emerald-400 font-bold">Active Agreement</span>
                      </div>
                      
                      <div className="p-3 bg-slate-850/40 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2">
                          <FileInput className="h-4 w-4 text-indigo-400" />
                          <span className="font-semibold text-slate-200">Purchase Order generated:</span>
                          <span className="text-slate-400">PO-2026-004</span>
                        </div>
                        <span className="text-[10px] text-emerald-400 font-bold">Sent to Supplier Vendor</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 12: CEO DASHBOARD & FRAUD LOGS --- */}
              {activeScene === 12 && (
                <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 12: Spend Intelligence Dashboard</h2>
                      <p className="text-xs text-slate-400">High-level capital monitoring and automated fraud detection audits.</p>
                    </div>
                    
                    <span className="px-3 py-1 bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/25 rounded-full text-xs font-bold flex items-center space-x-1">
                      <ShieldCheck className="h-4 w-4 text-emerald-400" />
                      <span>Security Shield Active</span>
                    </span>
                  </div>
                  
                  {/* Top Analytics row */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block">Total Capital Audited</span>
                        <p className="text-3xl font-outfit font-extrabold text-white mt-1">₹4.58 Crore</p>
                      </div>
                      <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
                        <Landmark className="h-6 w-6" />
                      </div>
                    </div>
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs text-slate-550 font-bold uppercase tracking-wider block text-emerald-400">Autonomous AI Savings</span>
                        <p className="text-3xl font-outfit font-extrabold text-emerald-400 mt-1">₹28.45 Lakhs</p>
                      </div>
                      <div className="h-12 w-12 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 text-emerald-400">
                        <TrendingUp className="h-6 w-6" />
                      </div>
                    </div>
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs text-slate-550 font-bold uppercase tracking-wider block text-rose-400">Alert Flags Blocked</span>
                        <p className="text-3xl font-outfit font-extrabold text-rose-400 mt-1">4 Breaches</p>
                      </div>
                      <div className="h-12 w-12 rounded-xl bg-rose-500/10 flex items-center justify-center border border-rose-500/20 text-rose-400">
                        <ShieldAlert className="h-6 w-6" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* MOCK CHARTS */}
                    <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                      <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">Departmental Spend Allocation</h3>
                      
                      {/* Simple CSS simulated chart bars */}
                      <div className="space-y-4 py-4">
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-slate-300">IT &amp; Telecommunications</span>
                            <span className="text-slate-450 font-bold">₹1.80 Crore (39%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-500" style={{ width: '39%' }} />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-slate-300">Operations &amp; Logistics</span>
                            <span className="text-slate-450 font-bold">₹1.42 Crore (31%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500" style={{ width: '31%' }} />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-slate-300">Facility Maintenance</span>
                            <span className="text-slate-450 font-bold">₹82 Lakhs (18%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-pink-500" style={{ width: '18%' }} />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-slate-300">Travel &amp; Administration</span>
                            <span className="text-slate-450 font-bold">₹54 Lakhs (12%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-amber-500" style={{ width: '12%' }} />
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* FRAUD logs */}
                    <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                      <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">AI Audit Trail &amp; Flags</h3>
                      
                      <div className="space-y-3 text-[11px] overflow-y-auto max-h-[220px]">
                        <div className="p-2.5 bg-rose-950/20 border border-rose-900/40 rounded-lg flex items-start space-x-2 text-rose-400">
                          <ShieldAlert className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-bold">Split-Invoice Attempt Blocked</span>
                            <p className="mt-0.5 text-slate-400">User attempted to split 30 laptops into 3 requests to bypass CFO limit check.</p>
                          </div>
                        </div>
                        
                        <div className="p-2.5 bg-rose-950/20 border border-rose-900/40 rounded-lg flex items-start space-x-2 text-rose-400">
                          <ShieldAlert className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-bold">Price Variance Mapped</span>
                            <p className="mt-0.5 text-slate-400">Supplier quoted ₹74,000 which exceeded our market baseline of ₹69,000.</p>
                          </div>
                        </div>
                        
                        <div className="p-2.5 bg-emerald-950/20 border border-emerald-900/40 rounded-lg flex items-start space-x-2 text-emerald-400">
                          <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                          <div>
                            <span className="font-bold">SLA Health OK</span>
                            <p className="mt-0.5 text-slate-400">Verified Primus Technologies delivery reliability rating at 98.4%.</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
            </div>
            
            {/* FOOTER */}
            <footer className={`h-12 border-t px-6 flex items-center justify-between text-xs ${darkMode ? 'bg-[#0f1422] border-slate-800 text-slate-500' : 'bg-white border-slate-200 text-slate-450'}`}>
              <span>SmartSpend AI Procurement Demo Portal</span>
              <span>Backed by Odoo 15 compliance</span>
            </footer>
          </main>
          
          {/* RIGHT PERSISTENT COPILOT SIDEBAR PANEL */}
          <aside className={`w-80 border-l flex-shrink-0 flex flex-col justify-between overflow-y-auto ${darkMode ? 'bg-[#0f1422] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="p-6 space-y-6">
              <div className="flex items-center space-x-2 pb-4 border-b border-slate-800">
                <Sparkles className="h-5 w-5 text-indigo-400 animate-pulse" />
                <h3 className="font-outfit font-extrabold text-sm text-white">SmartSpend AI Copilot</h3>
              </div>
              
              {/* Dynamic explanations matching each scene state */}
              <div className="space-y-4 text-xs">
                
                <div className="p-4 bg-indigo-950/20 border border-indigo-900/40 rounded-xl space-y-2">
                  <span className="font-bold text-indigo-400 block uppercase tracking-wider text-[10px]">Copilot Operations</span>
                  
                  {activeScene === 2 && (
                    <p className="text-slate-300 leading-relaxed">
                      "Welcome. You can create a request via voice, text, or file upload. The voice portal uses real-time NLP keyword mapping to bypass complex forms."
                    </p>
                  )}
                  {activeScene === 3 && (
                    <p className="text-slate-300 leading-relaxed">
                      "I'm listening to your voice input. I will parse keywords like '20 Dell Laptops', '₹70k', and 'Bangalore Office' to resolve the item, budget limit, and branch address mappings."
                    </p>
                  )}
                  {activeScene === 4 && (
                    <p className="text-slate-300 leading-relaxed">
                      "I've successfully mapped your voice data. I resolved Kochi as the billing entity and Bangalore as the shipping office using the corporate branch matrix."
                    </p>
                  )}
                  {activeScene === 5 && (
                    <p className="text-slate-300 leading-relaxed">
                      "I am checking Q3 budget allocations. If there is a breach, I can route budget transfers or split the purchase order across quotas."
                    </p>
                  )}
                  {activeScene === 6 && (
                    <p className="text-slate-300 leading-relaxed">
                      "I am scanning for Odoo Rate Contracts. If found, we bypass sourcing completely. If not, SCM auto-assignment takes over."
                    </p>
                  )}
                  {activeScene === 7 && (
                    <p className="text-slate-300 leading-relaxed">
                      "No active agreement exists. I've auto-registered a draft partner card and sent a secure magic bidding link to Primus Technologies."
                    </p>
                  )}
                  {activeScene === 8 && (
                    <p className="text-slate-300 leading-relaxed">
                      "The vendors uploaded quotes via magic links. I extracted all details side-by-side. Primus is recommended based on pricing and delivery SLA."
                    </p>
                  )}
                  {activeScene === 9 && (
                    <p className="text-slate-300 leading-relaxed">
                      "I am negotiating price and support terms directly with the Primus sales bot to maximize Q3 hardware savings."
                    </p>
                  )}
                  {activeScene === 10 && (
                    <p className="text-slate-300 leading-relaxed">
                      "I've compiled a 1-tap summary card for your manager. It focuses on cost center status, risk assessment, and total savings."
                    </p>
                  )}
                  {activeScene === 11 && (
                    <p className="text-slate-300 leading-relaxed">
                      "Your request is approved! I generated and confirmed the Purchase Order (PO-2026-004) in Odoo, sending it directly to the vendor."
                    </p>
                  )}
                  {activeScene === 12 && (
                    <p className="text-slate-300 leading-relaxed">
                      "Providing top-level spend auditing for executive management. Fraud checks monitor invoice splitting and pricing manipulation."
                    </p>
                  )}
                </div>
                
                {/* Visual Checklist */}
                <div className="space-y-2 pt-2">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Audits Completed</span>
                  <div className="space-y-1.5 font-medium text-slate-400">
                    <div className="flex items-center space-x-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${activeScene >= 4 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                      <span>Natural Language Mapped</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${activeScene >= 5 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                      <span>Budget Availability Checked</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${activeScene >= 6 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                      <span>Odoo Contract Checked</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${activeScene >= 9 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                      <span>AI Negotiation Checked</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${activeScene >= 11 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                      <span>Compliance PO Registered</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="p-6 bg-slate-900/40 border-t border-slate-800 text-center">
              <span className="text-[10px] text-slate-500 font-bold tracking-widest block uppercase">SmartSpend Orchestration</span>
            </div>
          </aside>
          
        </div>
      )}
      
    </div>
  );
}
