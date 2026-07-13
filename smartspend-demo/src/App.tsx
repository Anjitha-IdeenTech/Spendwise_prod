import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Mic, FileText, Keyboard, LayoutDashboard, Send, 
  TrendingUp, DollarSign, ShieldAlert, Award, FileSpreadsheet, 
  ArrowRight, User, Settings, CheckCircle2, ChevronRight, 
  Play, RefreshCw, X, AlertTriangle, AlertCircle, Check, 
  HelpCircle, Volume2, ShieldCheck, Landmark, Briefcase, FileInput, 
  Calendar, Layers, Clock, Users, ArrowUpRight, ArrowDownRight, Menu,
  Paperclip, MessageSquare, History, Search, Eye, Filter,
  Truck, Package, Receipt, CreditCard
} from 'lucide-react';

// Define the Scene IDs and names
const SCENES = [
  { id: 1, name: "Scene 1: Microsoft SSO Login & Portal Selector" },
  { id: 2, name: "Scene 2: Employee Portal (Consolidated Chat & Tabs)" },
  { id: 3, name: "Scene 3: Voice Assistant Simulation" },
  { id: 4, name: "Scene 4: AI Requisition Extraction Form" },
  { id: 5, name: "Scene 5: Active Rate Contract Search" },
  { id: 6, name: "Scene 6: SCM Sourcing & External Sourcing Bids" },
  { id: 7, name: "Scene 7: RFQ Value Scorecard" },
  { id: 8, name: "Scene 8: AI Autonomous Negotiation Lounge" },
  { id: 9, name: "Scene 9: Smart Budget Verification & Allocation" },
  { id: 10, name: "Scene 10: Manager Approval Dashboard" },
  { id: 11, name: "Scene 11: Request Tracking Timeline" },
  { id: 12, name: "Scene 12: Product Receiving & Inspection (GRN)" },
  { id: 13, name: "Scene 13: Vendor Bill 3-Way Matching" },
  { id: 14, name: "Scene 14: Payment Processing & Reconciliation" },
  { id: 15, name: "Scene 15: Spend Intelligence Analytics" }
];

interface ChatMessage {
  sender: 'ai' | 'vendor';
  text: string;
  timestamp: string;
}

interface RequestItem {
  id: string;
  productName: string;
  productQty: number;
  targetPrice: number;
  totalCost: number;
  location: string;
  expenseCategory: string;
  status: 'Draft' | 'Pending Approval' | 'Needs Clarification' | 'Sourcing' | 'Approved' | 'PO Confirmed' | 'Rejected' | 'Paid';
  urgency: 'High' | 'Medium' | 'Low';
  createdDate: string;
  buyer: string;
  vendor: string;
  savings: number;
  history: Array<{ title: string; date: string; desc?: string }>;
  clarificationComments: Array<{ role: 'manager' | 'employee'; text: string; date: string }>;
  vendorBids: Array<{ vendorName: string; price: number; leadTime: string; warranty: string; status: string }>;
  selectedSourcingMethod: 'Direct' | 'RFQ' | 'Auction';
  attachments: string[];
}

const getContractPrice = (name: string) => {
  const lower = name.toLowerCase();
  if (lower.includes("laptop") || lower.includes("dell")) return 70000;
  if (lower.includes("chair") || lower.includes("furniture")) return 8000;
  if (lower.includes("server") || lower.includes("rack")) return 120000;
  return 50000;
};

const getNegotiationBaselinePrice = (name: string) => {
  const lower = name.toLowerCase();
  if (lower.includes("laptop") || lower.includes("dell")) return 72000;
  if (lower.includes("chair") || lower.includes("furniture")) return 9000;
  if (lower.includes("server") || lower.includes("rack")) return 130000;
  return 60000;
};

const getNegotiatedTargetPrice = (name: string) => {
  const lower = name.toLowerCase();
  if (lower.includes("laptop") || lower.includes("dell")) return 67000;
  if (lower.includes("chair") || lower.includes("furniture")) return 7800;
  if (lower.includes("server") || lower.includes("rack")) return 115000;
  return 55000;
};

export default function App() {
  // Global States
  const [activeScene, setActiveScene] = useState<number>(1);
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [userRole, setUserRole] = useState<string>("Employee"); // Employee, Manager, SCM Buyer, Vendor, CEO

  // Post-PO simulation states
  const [grnGenerated, setGrnGenerated] = useState<boolean>(false);
  const [billPosted, setBillPosted] = useState<boolean>(false);
  const [paymentComplete, setPaymentComplete] = useState<boolean>(false);
  const [deliveredQty, setDeliveredQty] = useState<number>(20);
  const [qualityPassed, setQualityPassed] = useState<boolean>(true);
  const [paymentMethod, setPaymentMethod] = useState<string>("Bank Transfer");
  
  // Shared Data Model representing Odoo's live state
  const [requests, setRequests] = useState<RequestItem[]>([
    {
      id: "PR-2026-089",
      productName: "Dell Latitude 5440 Laptops",
      productQty: 20,
      targetPrice: 70000,
      totalCost: 1300000,
      location: "Bangalore Office",
      expenseCategory: "IT Hardware & Laptops",
      status: "Pending Approval",
      urgency: "High",
      createdDate: "July 08, 08:30",
      buyer: "SCM-IT-14",
      vendor: "Primus Technologies",
      savings: 60000,
      history: [
        { title: "Request Submitted", date: "July 08, 08:30", desc: "Initiated by Anjitha V via conversational entry" },
        { title: "Budget Checked", date: "July 08, 08:32", desc: "Verified against Q3 IT Hardware allocation" }
      ],
      clarificationComments: [],
      vendorBids: [
        { vendorName: "Primus Technologies", price: 68000, leadTime: "5 Days", warranty: "3 Years On-Site", status: "Recommended" },
        { vendorName: "Apex Systems", price: 71000, leadTime: "10 Days", warranty: "1 Year Carry-In", status: "Qualified" }
      ],
      selectedSourcingMethod: "RFQ",
      attachments: ["hardware_specifications.pdf"]
    },
    {
      id: "PR-2026-077",
      productName: "Ergonomic Office Chairs",
      productQty: 10,
      targetPrice: 8000,
      totalCost: 80000,
      location: "Kochi Head Office",
      expenseCategory: "Office Furniture",
      status: "PO Confirmed",
      urgency: "Medium",
      createdDate: "July 05, 11:20",
      buyer: "SCM-FUR-03",
      vendor: "Apex Systems",
      savings: 5000,
      history: [
        { title: "Request Submitted", date: "July 05, 11:20", desc: "Submitted by Anjitha V" },
        { title: "Approved by Manager", date: "July 05, 14:15", desc: "Approved by Operations Director" },
        { title: "PO Created: PO-2026-003", date: "July 05, 15:00", desc: "Auto-generated & sent to Apex Systems" }
      ],
      clarificationComments: [],
      vendorBids: [
        { vendorName: "Apex Systems", price: 8000, leadTime: "3 Days", warranty: "2 Years", status: "Selected" }
      ],
      selectedSourcingMethod: "Direct",
      attachments: []
    },
    {
      id: "PR-2026-092",
      productName: "19-Inch Data Server Racks",
      productQty: 2,
      targetPrice: 120000,
      totalCost: 240000,
      location: "Mumbai Office",
      expenseCategory: "Datacenter Equipment",
      status: "Sourcing",
      urgency: "High",
      createdDate: "July 09, 09:15",
      buyer: "SCM-IT-14",
      vendor: "Pending Sourcing",
      savings: 0,
      history: [
        { title: "Request Submitted", date: "July 09, 09:15", desc: "Initiated via search bar" },
        { title: "Budget Checked", date: "July 09, 09:16", desc: "Verified & Reserved in Odoo ERP" },
        { title: "Sourcing Triggered", date: "July 09, 09:18", desc: "No active rate contract found. Rerouted to SCM buyer." }
      ],
      clarificationComments: [],
      vendorBids: [
        { vendorName: "Primus Technologies", price: 125000, leadTime: "7 Days", warranty: "3 Years", status: "Submitted" }
      ],
      selectedSourcingMethod: "RFQ",
      attachments: []
    }
  ]);

  const [selectedRequestId, setSelectedRequestId] = useState<string>("PR-2026-089");
  const currentRequest = requests.find(r => r.id === selectedRequestId) || requests[0];

  useEffect(() => {
    if (currentRequest) {
      setDeliveredQty(currentRequest.productQty);
    }
  }, [selectedRequestId, currentRequest]);

  // Employee Portal Local States
  const [employeeTab, setEmployeeTab] = useState<'chat' | 'list' | 'tracking' | 'clarify'>('chat');
  const [chatInputText, setChatInputText] = useState<string>("");
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const [showFileAttachedAlert, setShowFileAttachedAlert] = useState<boolean>(false);
  
  // Voice Modal States
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'processing' | 'done'>('idle');
  const [voiceSeconds, setVoiceSeconds] = useState<number>(0);
  const [speechText, setSpeechText] = useState<string>("");
  const timerRef = useRef<any>(null);

  // Requisition Form states
  const [editProductName, setEditProductName] = useState<string>("Dell Latitude 5440 Laptops");
  const [editProductQty, setEditProductQty] = useState<number>(20);
  const [editTargetPrice, setEditTargetPrice] = useState<number>(70000);
  const [editLocation, setEditLocation] = useState<string>("Bangalore Office");
  const [editExpenseCategory, setEditExpenseCategory] = useState<string>("IT Hardware & Laptops");

  // Budget validation States
  const [budgetBreach, setBudgetBreach] = useState<boolean>(false);
  const [budgetAction, setBudgetAction] = useState<string>("default");

  // Contract selection State
  const [hasContract, setHasContract] = useState<boolean>(false);

  // SCM Buyer Portal Local States
  const [scmTab, setScmTab] = useState<'requests' | 'bidding' | 'discovery'>('requests');
  const [discoveredVendors, setDiscoveredVendors] = useState<Array<{ name: string; category: string; rating: number; score: number; registered: boolean; id?: string }>>([]);
  const [searchVendorQuery, setSearchVendorQuery] = useState<string>("");
  const [searchingVendors, setSearchingVendors] = useState<boolean>(false);
  const [showDraftOnboardSuccess, setShowDraftOnboardSuccess] = useState<boolean>(false);
  const [lastOnboardedVendor, setLastOnboardedVendor] = useState<string>("");

  // Vendor Portal Local States
  const [vendorBidPrice, setVendorBidPrice] = useState<string>("118000");
  const [vendorLeadTime, setVendorLeadTime] = useState<string>("5 Days");
  const [vendorBidSubmitted, setVendorBidSubmitted] = useState<boolean>(false);

  // Manager Clarification Prompt State
  const [managerQueryText, setManagerQueryText] = useState<string>("");
  const [showManagerQueryBox, setShowManagerQueryBox] = useState<boolean>(false);

  // Employee Clarification Reply State
  const [employeeReplyText, setEmployeeReplyText] = useState<string>("");

  // AI Negotiation State
  const [negotiationStep, setNegotiationStep] = useState<number>(0);
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [currentOfferPrice, setCurrentOfferPrice] = useState<number>(68000);
  const [negotiationComplete, setNegotiationComplete] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Quick navigation helpers
  const nextScene = () => activeScene < 15 && setActiveScene(activeScene + 1);
  const prevScene = () => activeScene > 1 && setActiveScene(activeScene - 1);

  // Simulation timer for voice recording
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
      setSpeechText("I need twenty Dell Latitude laptops for the Bangalore office.");
      setVoiceState('done');
    }, 1500);
  };
  const parseSpeechText = (text: string) => {
    const lower = text.toLowerCase();
    let name = "Dell Latitude 5440 Laptops";
    let qty = 20;
    let price = 0;
    let loc = "Bangalore Office";
    let cat = "IT Hardware & Laptops";

    if (lower.includes("chair") || lower.includes("furniture") || lower.includes("chairs")) {
      name = "Ergonomic Office Chairs";
      qty = 10;
      price = 0;
      loc = "Kochi Head Office";
      cat = "Office Furniture";
    } else if (lower.includes("server") || lower.includes("rack") || lower.includes("racks")) {
      name = "19-Inch Data Server Racks";
      qty = 2;
      price = 0;
      loc = "Mumbai Office";
      cat = "Datacenter Equipment";
    }
    
    setEditProductName(name);
    setEditProductQty(qty);
    setEditTargetPrice(price);
    setEditLocation(loc);
    setEditExpenseCategory(cat);
  };

  const handleSsoLogin = (role: string) => {
    setUserRole(role);
    if (role === "Employee") {
      setEmployeeTab('chat');
      setActiveScene(2);
    } else if (role === "Manager") {
      setActiveScene(10);
    } else if (role === "SCM Buyer") {
      setScmTab('requests');
      setActiveScene(6);
    } else if (role === "Vendor") {
      setActiveScene(6); // Redirect to show bidding/interaction
    } else if (role === "CEO") {
      setActiveScene(15);
    }
  };

  const handleChatSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!chatInputText.trim()) return;

    parseSpeechText(chatInputText);
    setChatInputText("");
    setActiveScene(4); // Go to extraction form
  };

  const handleAttachmentAdd = () => {
    setAttachedFiles(["specification_matrix.pdf"]);
    setShowFileAttachedAlert(true);
    setTimeout(() => setShowFileAttachedAlert(false), 3000);
  };

  // Convert Extraction Form to Live Request
  const createRequisitionFromForm = () => {
    const newId = `PR-2026-0${90 + requests.length}`;
    const newReq: RequestItem = {
      id: newId,
      productName: editProductName,
      productQty: editProductQty,
      targetPrice: 0,
      totalCost: 0,
      location: editLocation,
      expenseCategory: editExpenseCategory,
      status: budgetBreach ? "Needs Clarification" : "Pending Approval",
      urgency: "High",
      createdDate: new Date().toLocaleDateString([], { month: 'short', day: '2-digit' }) + ", " + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      buyer: "SCM-IT-14",
      vendor: "Pending Sourcing",
      savings: 0,
      history: [
        { title: "Request Submitted", date: "Now", desc: "Submitted via extraction panel" }
      ],
      clarificationComments: [],
      vendorBids: [],
      selectedSourcingMethod: "RFQ",
      attachments: attachedFiles
    };

    setRequests(prev => [newReq, ...prev]);
    setSelectedRequestId(newId);
    setAttachedFiles([]);
    
    // Go to next step in demo
    setActiveScene(5);
  };

  // Manager Approval Action
  const handleManagerApprove = (id: string) => {
    setRequests(prev => prev.map(r => {
      if (r.id === id) {
        return {
          ...r,
          status: "Approved",
          history: [...r.history, { title: "Approved by Manager", date: "Now", desc: "Approved by Operational Manager" }]
        };
      }
      return r;
    }));
    setActiveScene(11); // Route to order tracking
  };

  // Manager Request Information Loop
  const handleRequestInfoSubmit = (id: string) => {
    if (!managerQueryText.trim()) return;

    setRequests(prev => prev.map(r => {
      if (r.id === id) {
        return {
          ...r,
          status: "Needs Clarification",
          clarificationComments: [
            ...r.clarificationComments,
            { role: 'manager', text: managerQueryText, date: "Now" }
          ],
          history: [...r.history, { title: "Info Requested", date: "Now", desc: `Query: "${managerQueryText}"` }]
        };
      }
      return r;
    }));

    setManagerQueryText("");
    setShowManagerQueryBox(false);
    alert("Clarification request sent back to the employee.");
  };

  // Employee responds to manager request
  const handleEmployeeReplySubmit = (id: string) => {
    if (!employeeReplyText.trim()) return;

    setRequests(prev => prev.map(r => {
      if (r.id === id) {
        return {
          ...r,
          status: "Pending Approval",
          clarificationComments: [
            ...r.clarificationComments,
            { role: 'employee', text: employeeReplyText, date: "Now" }
          ],
          history: [...r.history, { title: "Clarified by Employee", date: "Now", desc: `Response: "${employeeReplyText}"` }]
        };
      }
      return r;
    }));

    setEmployeeReplyText("");
    alert("Clarification submitted. Re-routed to manager approval queue.");
    setEmployeeTab('list');
  };

  // AI Vendor Discovery simulation
  const handleSearchVendors = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchVendorQuery.trim()) return;

    setSearchingVendors(true);
    setTimeout(() => {
      setSearchingVendors(false);
      setDiscoveredVendors([
        { name: "Global Hardware Integrators", category: "Servers & IT Network", rating: 92, score: 95, registered: false },
        { name: "Apex Sourcing Solutions", category: "Office Equipment & Furniture", rating: 85, score: 88, registered: false },
        { name: "Zenith Business Networks", category: "Datacenter Rack Cabinets", rating: 88, score: 91, registered: false }
      ]);
    }, 1000);
  };

  // Auto-onboard Draft Partner in Odoo
  const handleAutoOnboard = (vendorName: string) => {
    setLastOnboardedVendor(vendorName);
    setShowDraftOnboardSuccess(true);
    
    // Add this vendor to the current request's bids
    setRequests(prev => prev.map(r => {
      if (r.id === selectedRequestId) {
        return {
          ...r,
          vendorBids: [
            ...r.vendorBids,
            { vendorName, price: r.targetPrice - 2000, leadTime: "6 Days", warranty: "2 Years", status: "Qualified" }
          ]
        };
      }
      return r;
    }));

    setTimeout(() => setShowDraftOnboardSuccess(false), 5000);
  };

  // Vendor Portal bids submit
  const handleVendorBidSubmit = () => {
    if (!vendorBidPrice.trim()) return;
    
    const bidAmount = Number(vendorBidPrice);
    setRequests(prev => prev.map(r => {
      if (r.id === selectedRequestId) {
        return {
          ...r,
          vendorBids: [
            ...r.vendorBids,
            { vendorName: "Primus Technologies (Your Portal)", price: bidAmount, leadTime: vendorLeadTime, warranty: "3 Years On-Site", status: "Submitted" }
          ]
        };
      }
      return r;
    }));

    setVendorBidSubmitted(true);
    setTimeout(() => setVendorBidSubmitted(false), 3000);
  };

  // AI Negotiation Simulation Step-by-Step
  const triggerNextNegotiationStep = () => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const baseline = getNegotiationBaselinePrice(currentRequest.productName);
    const negotiated = getNegotiatedTargetPrice(currentRequest.productName);
    const midPoint = Math.round((baseline + negotiated) / 2);
    
    if (negotiationStep === 0) {
      setChatLog([
        { sender: 'ai', text: `Hello Primus Sales Bot. We are looking to place an immediate order for ${currentRequest.productQty} units of ${currentRequest.productName}. Your bid is listed at ₹${baseline.toLocaleString()}. Under our standard volume discount agreement, we request a final target rate of ₹${negotiated.toLocaleString()} with Net-30 payment terms.`, timestamp }
      ]);
      setNegotiationStep(1);
    } else if (negotiationStep === 1) {
      setChatLog(prev => [
        ...prev,
        { sender: 'vendor', text: `Thank you for reaching out. We appreciate the volume request. However, due to recent supply chain margins, our bottom-line rate is ₹${baseline.toLocaleString()} for ${currentRequest.productQty} units. Alternatively, we can offer ₹${midPoint.toLocaleString()} if the company clears invoices on Net-7 terms instead.`, timestamp }
      ]);
      setNegotiationStep(2);
    } else if (negotiationStep === 2) {
      setChatLog(prev => [
        ...prev,
        { sender: 'ai', text: `Our corporate accounting policy mandates Net-30 payment terms for compliance audit lines. Can we lock in at ₹${negotiated.toLocaleString()} per unit under Net-30 terms, and in return, we will mark Primus as our Primary Supplier for Q3 hardware renewals?`, timestamp }
      ]);
      setNegotiationStep(3);
    } else if (negotiationStep === 3) {
      const finalPrice = negotiated;
      setChatLog(prev => [
        ...prev,
        { sender: 'vendor', text: `We accept the volume proposal. Final price locked at ₹${finalPrice.toLocaleString()} per unit, Net-30 payment terms, including 3 Years On-Site Support. Registering the Rate Contract in Odoo.`, timestamp }
      ]);
      setCurrentOfferPrice(finalPrice);
      setNegotiationComplete(true);
      setNegotiationStep(4);

      // Update request state with negotiated details
      setRequests(prev => prev.map(r => {
        if (r.id === selectedRequestId) {
          return {
            ...r,
            vendor: "Primus Technologies",
            savings: (baseline - finalPrice) * r.productQty,
            history: [...r.history, { title: "AI Negotiated", date: "Now", desc: `Final Price: ₹${finalPrice.toLocaleString()} (Net-30)` }]
          };
        }
        return r;
      }));
    }
  };

  const resetNegotiation = () => {
    setChatLog([]);
    setNegotiationStep(0);
    setCurrentOfferPrice(getNegotiationBaselinePrice(currentRequest.productName));
    setNegotiationComplete(false);
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${darkMode ? 'bg-[#0b0f19] text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      
      {/* --- SCENE 1: Microsoft SSO & Role Portal Login --- */}
      {activeScene === 1 && (
        <div className="flex-grow flex flex-col lg:flex-row min-h-screen">
          <div className="lg:w-7/12 bg-gradient-to-tr from-[#0F172A] via-[#1E1B4B] to-[#311042] flex flex-col justify-between p-8 lg:p-16 text-white relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(99,102,241,0.15),transparent)] pointer-events-none" />
            <div className="z-10 flex items-center space-x-2">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
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
            </div>
            
            <div className="z-10 flex items-center justify-between text-xs text-slate-500">
              <span>Powered by Odoo ERP Backend</span>
              <span>CONFIDENTIAL PROTOTYPE V2</span>
            </div>
          </div>
          
          <div className="lg:w-5/12 flex flex-col justify-center px-6 py-12 md:px-16 lg:px-20 bg-slate-900 border-l border-slate-800">
            <div className="max-w-md w-full mx-auto space-y-8">
              <div>
                <h2 className="font-outfit text-3xl font-extrabold text-white tracking-tight">Sign In</h2>
                <p className="mt-3 text-sm text-slate-400">
                  Authenticate via your corporate SSO portal to test each interactive role.
                </p>
              </div>
              
              <div className="space-y-4">
                <button
                  onClick={() => handleSsoLogin("Employee")}
                  className="w-full flex items-center justify-center space-x-3 py-3.5 px-4 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 text-white font-medium shadow-sm transition-all"
                >
                  <svg className="h-5 w-5" viewBox="0 0 23 23" fill="currentColor">
                    <path fill="#f35325" d="M1 1h10v10H1z" />
                    <path fill="#81bc06" d="M12 1h10v10H12z" />
                    <path fill="#05a6f0" d="M1 12h10v10H1z" />
                    <path fill="#ffba08" d="M12 12h10v10H12z" />
                  </svg>
                  <span>Log in with Microsoft SSO</span>
                </button>
                
                <div className="relative flex py-4 items-center">
                  <div className="flex-grow border-t border-slate-850"></div>
                  <span className="flex-shrink mx-4 text-slate-500 text-xs font-semibold uppercase tracking-wider">Select Demo Role Portal</span>
                  <div className="flex-grow border-t border-slate-850"></div>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => handleSsoLogin("Employee")}
                    className="p-3 bg-slate-800/50 hover:bg-indigo-600/20 border border-slate-800 hover:border-indigo-500/30 rounded-xl text-center text-xs text-slate-350 font-medium transition-all"
                  >
                    Employee Portal
                  </button>
                  <button 
                    onClick={() => handleSsoLogin("Manager")}
                    className="p-3 bg-slate-800/50 hover:bg-amber-600/20 border border-slate-800 hover:border-amber-500/30 rounded-xl text-center text-xs text-slate-350 font-medium transition-all"
                  >
                    Manager Inbox
                  </button>
                  <button 
                    onClick={() => handleSsoLogin("SCM Buyer")}
                    className="p-3 bg-slate-800/50 hover:bg-purple-600/20 border border-slate-800 hover:border-purple-500/30 rounded-xl text-center text-xs text-slate-350 font-medium transition-all"
                  >
                    SCM Buyer Portal
                  </button>
                  <button 
                    onClick={() => handleSsoLogin("Vendor")}
                    className="p-3 bg-slate-800/50 hover:bg-emerald-600/20 border border-slate-800 hover:border-emerald-500/30 rounded-xl text-center text-xs text-slate-350 font-medium transition-all"
                  >
                    Vendor Portal
                  </button>
                </div>
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
                <div className="p-6 flex items-center justify-between border-b border-slate-800/40">
                  <div className="flex items-center space-x-2">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center">
                      <Sparkles className="h-4.5 w-4.5 text-white" />
                    </div>
                    <span className="font-outfit font-bold text-lg tracking-tight">SmartSpend</span>
                  </div>
                </div>
                
                {/* Switch Role Quick Dropdown */}
                <div className="p-4 border-b border-slate-850">
                  <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1.5">Switch Interactive Role</label>
                  <select 
                    value={userRole}
                    onChange={(e) => handleSsoLogin(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs text-white font-semibold focus:outline-none"
                  >
                    <option value="Employee">Employee (Requester)</option>
                    <option value="Manager">Manager (Approver)</option>
                    <option value="SCM Buyer">SCM Buyer (Sourcing)</option>
                    <option value="Vendor">Vendor (External Portal)</option>
                    <option value="CEO">CEO (Spend Intel)</option>
                  </select>
                </div>
                
                {/* Navigation Items (Role-Adaptive) */}
                <nav className="p-4 space-y-1.5">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block px-3 mb-2">Portal Navigation</span>
                  
                  {userRole === "Employee" && (
                    <>
                      <button 
                        onClick={() => { setActiveScene(2); setEmployeeTab('chat'); }}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 2 && employeeTab === 'chat' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <MessageSquare className="h-4 w-4" />
                        <span>Conversational Agent</span>
                      </button>
                      <button 
                        onClick={() => { setActiveScene(2); setEmployeeTab('list'); }}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 2 && employeeTab === 'list' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <FileText className="h-4 w-4" />
                        <span>My Requests</span>
                        <span className="ml-auto bg-slate-850 text-slate-350 text-[10px] px-2 py-0.5 rounded-full font-bold">{requests.length}</span>
                      </button>
                      <button 
                        onClick={() => { setActiveScene(2); setEmployeeTab('tracking'); }}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 2 && employeeTab === 'tracking' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <History className="h-4 w-4" />
                        <span>Request Tracking</span>
                      </button>
                      <button 
                        onClick={() => { setActiveScene(2); setEmployeeTab('clarify'); }}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 2 && employeeTab === 'clarify' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <AlertTriangle className="h-4 w-4" />
                        <span>Clarification Inbox</span>
                        {requests.filter(r => r.status === 'Needs Clarification').length > 0 && (
                          <span className="ml-auto bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] px-2 py-0.5 rounded-full font-bold animate-pulse">
                            {requests.filter(r => r.status === 'Needs Clarification').length}
                          </span>
                        )}
                      </button>
                    </>
                  )}

                  {userRole === "Manager" && (
                    <>
                      <button 
                        onClick={() => setActiveScene(10)}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 10 ? 'bg-amber-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Approval Queue</span>
                        <span className="ml-auto bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] px-2 py-0.5 rounded-full font-bold">
                          {requests.filter(r => r.status === 'Pending Approval').length}
                        </span>
                      </button>
                    </>
                  )}

                   {userRole === "SCM Buyer" && (
                    <>
                      <button 
                        onClick={() => { setActiveScene(6); setScmTab('requests'); }}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 6 && scmTab === 'requests' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <Briefcase className="h-4 w-4" />
                        <span>Contract Requests</span>
                        <span className="ml-auto bg-purple-500/20 text-purple-400 border border-purple-500/30 text-[10px] px-2 py-0.5 rounded-full font-bold">
                          {requests.filter(r => r.status === 'Sourcing').length}
                        </span>
                      </button>
                      <button 
                        onClick={() => { setActiveScene(6); setScmTab('discovery'); }}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 6 && scmTab === 'discovery' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <Search className="h-4 w-4" />
                        <span>AI Vendor Discovery</span>
                      </button>
                    </>
                  )}

                  {userRole === "Vendor" && (
                    <>
                      <button 
                        onClick={() => { setActiveScene(6); setScmTab('bidding'); }}
                        className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium text-emerald-400 bg-slate-800 border border-slate-700/60"
                      >
                        <FileSpreadsheet className="h-4 w-4" />
                        <span>Active RFQs to Quote</span>
                      </button>
                    </>
                  )}

                  {userRole === "CEO" && (
                    <>
                      <button 
                        onClick={() => setActiveScene(15)}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${activeScene === 15 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'}`}
                      >
                        <TrendingUp className="h-4 w-4" />
                        <span>Spend Analytics</span>
                      </button>
                    </>
                  )}
                </nav>
              </div>
              
              {/* Bottom Quick Controls */}
              <div className="p-4 space-y-3 border-t border-slate-850">
                <div className="flex items-center justify-between text-[11px] text-slate-500 px-2">
                  <span>Theme Mode:</span>
                  <button 
                    onClick={() => setDarkMode(!darkMode)}
                    className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-350 font-semibold"
                  >
                    {darkMode ? 'Light' : 'Dark'}
                  </button>
                </div>
                
                <button
                  onClick={() => setActiveScene(1)}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg border border-slate-850 bg-slate-850 hover:bg-slate-800 text-[11px] text-slate-400 hover:text-white font-medium transition-all"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Logout / Reset Demo</span>
                </button>
              </div>
            </aside>
          )}
          
          {/* MAIN WORKSPACE CONTENT */}
          <main className="flex-grow flex flex-col min-w-0 overflow-y-auto">
            
            {/* TOP NAVIGATION HEADER WITH SCENE PICKER */}
            <header className={`h-16 px-6 border-b flex items-center justify-between flex-shrink-0 ${darkMode ? 'bg-[#0f1422] border-slate-800' : 'bg-white border-slate-200'}`}>
              <div className="flex items-center space-x-4">
                <button 
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
                >
                  <Menu className="h-5 w-5" />
                </button>
                <div className="h-4 w-[1px] bg-slate-750" />
                
                {/* Scene Selector */}
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-semibold text-indigo-400">DEMO STEP:</span>
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
                  disabled={activeScene === 15}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-30 transition-all flex items-center space-x-1"
                >
                  <span>Next Step</span>
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </header>
            
            {/* WORKSPACE AREA */}
            <div className="p-6 md:p-8 flex-grow">
              
              {/* --- SCENE 2: EMPLOYEE PORTAL (CONSOLIDATED INPUT & TABS) --- */}
              {activeScene === 2 && (
                <div className="space-y-6 animate-fadeIn">
                  
                  {/* Employee Tabs Bar */}
                  <div className="flex border-b border-slate-800">
                    <button 
                      onClick={() => setEmployeeTab('chat')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'chat' ? 'border-indigo-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      Raise Request
                    </button>
                    <button 
                      onClick={() => setEmployeeTab('list')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'list' ? 'border-indigo-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      My Requests
                    </button>
                    <button 
                      onClick={() => setEmployeeTab('tracking')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'tracking' ? 'border-indigo-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      Request Tracking
                    </button>
                    <button 
                      onClick={() => setEmployeeTab('clarify')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'clarify' ? 'border-indigo-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      Clarification Inbox
                    </button>
                  </div>

                  {/* Tab 1: Raise Request (ChatGPT/WhatsApp Consolidated Search Style) */}
                  {employeeTab === 'chat' && (
                    <div className="max-w-3xl mx-auto space-y-12 py-10">
                      <div className="text-center space-y-3">
                        <h2 className="font-outfit text-4xl font-extrabold tracking-tight text-white">What's on the agenda today?</h2>
                        <p className="text-sm text-slate-450">Request any item or service. The AI orchestration layer maps the compliance rules in Odoo.</p>
                      </div>

                      {/* File Attached Success Banner */}
                      {showFileAttachedAlert && (
                        <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl flex items-center justify-between text-xs text-indigo-400 animate-fadeIn">
                          <span className="flex items-center space-x-2">
                            <Paperclip className="h-4 w-4" />
                            <span><strong>1 File Attached:</strong> specification_matrix.pdf</span>
                          </span>
                          <button onClick={() => setAttachedFiles([])} className="text-slate-400 hover:text-white">
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      )}

                      {/* Unified Input Bar (Matching user's attachment screenshot exactly) */}
                      <form onSubmit={handleChatSubmit} className="relative flex items-center bg-slate-900 border border-slate-750/70 rounded-full px-5 py-3.5 focus-within:border-indigo-500/60 shadow-xl transition-all">
                        {/* Attach button */}
                        <button 
                          type="button"
                          onClick={handleAttachmentAdd}
                          className="p-1.5 rounded-full hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-all mr-3"
                          title="Add attachment"
                        >
                          <Paperclip className="h-5 w-5" />
                        </button>

                        {/* Text input area */}
                        <input 
                          type="text"
                          value={chatInputText}
                          onChange={(e) => setChatInputText(e.target.value)}
                          placeholder="Ask anything..."
                          className="flex-grow bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none pr-28"
                        />

                        {/* Integration Logos & Voice Action Group */}
                        <div className="absolute right-3 flex items-center space-x-2">
                          <span className="text-slate-700 font-bold text-lg">|</span>
                          
                          {/* Chatgpt/WhatsApp integration icons */}
                          <div className="hidden sm:flex items-center space-x-1 text-slate-550 mr-1.5">
                            <span className="p-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 rounded-md text-[10px] font-bold">WA</span>
                            <span className="p-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 rounded-md text-[10px] font-bold">GPT</span>
                          </div>

                          {/* Voice Mic Icon */}
                          <button 
                            type="button"
                            onClick={() => setActiveScene(3)}
                            className="p-1.5 rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
                            title="Voice Procurement"
                          >
                            <Mic className="h-4.5 w-4.5" />
                          </button>

                          {/* Black round waveform button */}
                          <button 
                            type="button"
                            onClick={() => setActiveScene(3)}
                            className="h-9 w-9 rounded-full bg-slate-950 hover:bg-slate-850 text-indigo-400 hover:text-indigo-300 flex items-center justify-center transition-all border border-slate-800/80 shadow shadow-indigo-500/10"
                            title="Simulate Voice"
                          >
                            <div className="flex items-center space-x-0.5 h-3">
                              <div className="w-0.5 bg-indigo-400 rounded h-1 animate-pulse" />
                              <div className="w-0.5 bg-indigo-400 rounded h-3 animate-pulse" />
                              <div className="w-0.5 bg-indigo-400 rounded h-2 animate-pulse" />
                            </div>
                          </button>

                          {/* Send Button */}
                          <button 
                            type="submit"
                            className="p-2 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white transition-all"
                          >
                            <Send className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </form>

                      {/* Suggested Prompts */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-6">
                        <div 
                          onClick={() => setChatInputText("I need 20 Dell Latitude laptops for the Bangalore office")}
                          className="cursor-pointer p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all text-left text-xs space-y-1"
                        >
                          <span className="font-semibold text-slate-200 block">💻 Request IT Hardware</span>
                          <span className="text-slate-450">"I need 20 Dell Latitude laptops for the Bangalore office..."</span>
                        </div>
                        <div 
                          onClick={() => setChatInputText("Requesting 10 ergonomic conference chairs for the Mumbai office")}
                          className="cursor-pointer p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all text-left text-xs space-y-1"
                        >
                          <span className="font-semibold text-slate-200 block">🪑 Request Office Furniture</span>
                          <span className="text-slate-450">"Requesting 10 ergonomic conference chairs for Mumbai..."</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: My Requests List (Separated Grid) */}
                  {employeeTab === 'list' && (
                    <div className="space-y-4 animate-fadeIn">
                      <div className="flex items-center justify-between">
                        <h3 className="font-outfit font-extrabold text-xl text-white">Your Procurement Requisitions</h3>
                        <span className="text-xs text-slate-500">Select any request to view its live tracking timeline</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {requests.map(req => (
                          <div 
                            key={req.id} 
                            onClick={() => { setSelectedRequestId(req.id); setEmployeeTab('tracking'); }}
                            className={`cursor-pointer p-5 rounded-2xl border transition-all ${selectedRequestId === req.id ? 'bg-[#0f1422]/90 border-indigo-500 shadow-lg' : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'}`}
                          >
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-xs font-bold text-slate-450">{req.id}</span>
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                req.status === 'PO Confirmed' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                req.status === 'Approved' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                                req.status === 'Needs Clarification' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse' :
                                'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                              }`}>
                                {req.status}
                              </span>
                            </div>
                            
                            <h4 className="font-outfit font-extrabold text-base text-white">{req.productQty}x {req.productName}</h4>
                            
                            <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800/60 text-xs text-slate-400">
                              <div>
                                <span className="block text-[10px] text-slate-550 uppercase">Total budget:</span>
                                <span className="font-bold text-slate-200">₹{req.totalCost.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="block text-[10px] text-slate-550 uppercase">Location:</span>
                                <span className="font-bold text-slate-200">{req.location}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Request Tracking (Selected Requisition Timeline) */}
                  {employeeTab === 'tracking' && (
                    <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6 animate-fadeIn">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
                        <div>
                          <span className="text-xs text-indigo-400 font-bold block">{currentRequest.id} Tracking</span>
                          <h3 className="font-outfit font-extrabold text-xl text-white">{currentRequest.productQty}x {currentRequest.productName}</h3>
                        </div>
                        <span className="px-3 py-1 bg-slate-850 rounded-full border border-slate-800 text-xs font-bold text-slate-350">
                          Status: {currentRequest.status}
                        </span>
                      </div>

                      {/* Timeline Nodes */}
                      <div className="relative flex justify-between items-center max-w-2xl mx-auto py-6">
                        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-slate-800 z-0" />
                        
                        {/* Dynamic Progress indicator */}
                        <div 
                          className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-emerald-500 z-0 transition-all duration-500" 
                          style={{ 
                            width: currentRequest.status === 'PO Confirmed' ? '100%' :
                                   currentRequest.status === 'Approved' ? '75%' :
                                   currentRequest.status === 'Sourcing' ? '50%' : '25%' 
                          }} 
                        />

                        {/* Node 1: Request Submitted */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs">
                            <Check className="h-4 w-4" />
                          </div>
                          <span className="text-[10px] font-bold text-slate-200 block">Submitted</span>
                        </div>

                        {/* Node 2: Sourcing Mapped */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            ['Sourcing', 'Approved', 'PO Confirmed'].includes(currentRequest.status) ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-500 border border-slate-700'
                          }`}>
                            {['Sourcing', 'Approved', 'PO Confirmed'].includes(currentRequest.status) ? <Check className="h-4 w-4" /> : '2'}
                          </div>
                          <span className="text-[10px] font-bold text-slate-250 block">Sourcing</span>
                        </div>

                        {/* Node 3: Manager Approved */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            ['Approved', 'PO Confirmed'].includes(currentRequest.status) ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-500 border border-slate-700'
                          }`}>
                            {['Approved', 'PO Confirmed'].includes(currentRequest.status) ? <Check className="h-4 w-4" /> : '3'}
                          </div>
                          <span className="text-[10px] font-bold text-slate-250 block">Approved</span>
                        </div>

                        {/* Node 4: PO Confirmed */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            currentRequest.status === 'PO Confirmed' ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-500 border border-slate-700'
                          }`}>
                            {currentRequest.status === 'PO Confirmed' ? <Check className="h-4 w-4" /> : '4'}
                          </div>
                          <span className="text-[10px] font-bold text-slate-250 block">PO Sent</span>
                        </div>
                      </div>

                      {/* Audit Log / History */}
                      <div className="border-t border-slate-800/80 pt-6 max-w-xl mx-auto space-y-3">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Odoo Event Log</span>
                        {currentRequest.history.map((h, idx) => (
                          <div key={idx} className="p-3 bg-slate-850/45 border border-slate-800 rounded-xl flex items-start justify-between text-xs">
                            <div>
                              <span className="font-bold text-slate-200 block">{h.title}</span>
                              <span className="text-slate-400 mt-0.5 block">{h.desc}</span>
                            </div>
                            <span className="text-[10px] text-slate-500">{h.date}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 4: Clarification Inbox */}
                  {employeeTab === 'clarify' && (
                    <div className="space-y-6 animate-fadeIn">
                      <h3 className="font-outfit font-extrabold text-xl text-white">Clarification Requests</h3>
                      
                      {requests.filter(r => r.status === 'Needs Clarification').length === 0 ? (
                        <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-2xl text-slate-450">
                          <CheckCircle2 className="h-8 w-8 mx-auto text-emerald-400 mb-2" />
                          <p className="text-sm font-semibold">Your inbox is clear!</p>
                          <p className="text-xs mt-1">No manager queries pending clarification.</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {requests.filter(r => r.status === 'Needs Clarification').map(req => (
                            <div key={req.id} className="p-6 rounded-2xl bg-slate-900 border border-amber-500/30 space-y-4">
                              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                                <div>
                                  <span className="text-xs text-amber-400 font-bold block">{req.id}</span>
                                  <h4 className="font-outfit font-extrabold text-lg text-white">{req.productQty}x {req.productName}</h4>
                                </div>
                                <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/25 rounded-md text-[10px] font-bold">RFI PENDING</span>
                              </div>

                              {/* Manager Comment Display */}
                              <div className="p-4 bg-slate-850 border border-slate-800 rounded-xl">
                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Manager Query:</span>
                                <p className="text-xs text-slate-350 mt-1 font-medium italic">
                                  "{req.clarificationComments[req.clarificationComments.length - 1]?.text || 'Please provide details.'}"
                                </p>
                              </div>

                              {/* Reply form */}
                              <div className="space-y-2">
                                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Your Response / Clarification</label>
                                <textarea 
                                  rows={3}
                                  value={employeeReplyText}
                                  onChange={(e) => setEmployeeReplyText(e.target.value)}
                                  placeholder="Provide the requested details to re-submit for approval..."
                                  className="w-full bg-slate-800 border border-slate-700/60 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                                <div className="flex justify-end pt-2">
                                  <button 
                                    onClick={() => handleEmployeeReplySubmit(req.id)}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all"
                                  >
                                    Submit Response
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

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
                      <p className="text-sm text-slate-400 max-w-md mx-auto font-medium">Click the microphone to simulate recording your purchase request details.</p>
                    </div>
                    
                    {/* Microphone Soundwave Visual Area */}
                    <div className="flex flex-col items-center justify-center py-6 space-y-4">
                      {voiceState === 'idle' && (
                        <button 
                          onClick={() => setVoiceState('listening')}
                          className="h-24 w-24 rounded-full bg-slate-800 hover:bg-indigo-600 text-slate-350 hover:text-white flex items-center justify-center shadow-lg border border-slate-700/50 transition-all duration-300 hover:scale-105"
                        >
                          <Mic className="h-10 w-10" />
                        </button>
                      )}
                      
                      {voiceState === 'listening' && (
                        <div className="flex flex-col items-center space-y-4">
                          <button 
                            onClick={() => setVoiceState('processing')}
                            className="h-24 w-24 rounded-full bg-indigo-600 text-white flex items-center justify-center relative shadow-2xl"
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
                            <div className="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                          </div>
                          <div className="text-center">
                            <span className="text-sm font-semibold text-indigo-400">Transcribing Speech to Text...</span>
                            <span className="text-xs text-slate-505 block mt-1 text-slate-400">Analyzing Intent &amp; Catalog entities</span>
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
                              onClick={() => { setVoiceState('idle'); setVoiceSeconds(0); setSpeechText(""); }}
                              className="px-4 py-2 border border-slate-700 hover:bg-slate-800 text-xs font-semibold rounded-lg text-slate-300 transition-all"
                            >
                              Record Again
                            </button>
                            <button 
                              onClick={() => {
                                parseSpeechText(speechText);
                                setActiveScene(4);
                              }}
                              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                            >
                              <span>Continue</span>
                              <ChevronRight className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 4: PARSED REQUISITION FORM --- */}
              {activeScene === 4 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">AI Parsed Requisition Form</h2>
                      <p className="text-xs text-slate-400">Review and edit the parameters extracted from your conversational request.</p>
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
                            value={editProductName}
                            onChange={(e) => setEditProductName(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Quantity</label>
                          <input 
                            type="number" 
                            value={editProductQty}
                            onChange={(e) => setEditProductQty(Number(e.target.value))}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Target Price (per unit)</label>
                          <span className="w-full bg-slate-800/50 border border-slate-750 rounded-lg p-2 text-sm text-indigo-400 block font-semibold">
                            TBD (Determined Post-Contract / Sourcing)
                          </span>
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Category (Mapped)</label>
                          <input 
                            type="text" 
                            value={editExpenseCategory}
                            onChange={(e) => setEditExpenseCategory(e.target.value)}
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
                        <button onClick={createRequisitionFromForm} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all">Submit for Validation</button>
                      </div>
                    </div>
                    
                    {/* Right Card: Address Resolution Mappings */}
                    <div className="space-y-4">
                      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                        <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">Branch Mapped Addresses</h3>
                        
                        <div className="space-y-3">
                          <div>
                            <span className="text-[10px] text-slate-550 font-bold uppercase tracking-wider block mb-0.5">Input location:</span>
                            <span className="text-xs font-semibold text-slate-300">"{editLocation}"</span>
                          </div>
                          
                          <div className="pt-2 border-t border-slate-800">
                            <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block">Resolved Bill-To Address</span>
                            <span className="text-xs text-slate-300 font-medium block mt-1 font-semibold">Kuttukaran Corporate HQ, Metro Pillar 32, Kochi, KL - 682025</span>
                            <span className="text-[9px] text-slate-500 block mt-0.5">GSTIN: 32AAAAB1234C1Z0</span>
                          </div>
                          
                          <div className="pt-2 border-t border-slate-800">
                            <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block">Resolved Ship-To Address</span>
                            <span className="text-xs text-slate-300 font-medium block mt-1 font-semibold">Kuttukaran Regional Warehouse, IT Park, Bangalore, KA - 560066</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 9: BUDGET VALIDATION --- */}
              {activeScene === 9 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 9: Smart Budget Verification &amp; Allocation</h2>
                      <p className="text-xs text-slate-400">The platform cross-references available cost center funds in real-time after contract pricing is resolved.</p>
                    </div>
                    
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
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                      <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">{currentRequest.expenseCategory} Budget Allocation</h3>
                      
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
                          <span>Current Request ({currentRequest.productQty} units @ ₹{currentRequest.targetPrice.toLocaleString()}):</span>
                          <span className="font-bold text-indigo-400">₹{(currentRequest.productQty * currentRequest.targetPrice).toLocaleString()}</span>
                        </div>
                        
                        <div className="relative pt-2">
                          <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden flex">
                            <div className="h-full bg-slate-500" style={{ width: '40%' }} />
                            <div className={`h-full ${budgetBreach ? 'bg-rose-500' : 'bg-indigo-500'}`} style={{ width: budgetBreach ? '70%' : '20%' }} />
                          </div>
                        </div>
                      </div>
                      
                      {!budgetBreach ? (
                        <div className="p-4 bg-emerald-950/20 border border-emerald-900/40 rounded-xl flex items-start space-x-3 text-emerald-400 text-xs">
                          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0 text-emerald-400" />
                          <div>
                            <p className="font-bold">Budget Verification Passed</p>
                            <p className="mt-1 text-slate-350">Funds are available. Mapped to Cost Center. No pre-approvals required for budget allocation.</p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 bg-rose-950/20 border border-rose-900/40 rounded-xl flex items-start space-x-3 text-rose-400 text-xs">
                          <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0 text-rose-400 animate-pulse" />
                          <div>
                            <p className="font-bold">Budget Limit Exceeded by ₹{(currentRequest.productQty * currentRequest.targetPrice + 1200000 - 3000000).toLocaleString()}</p>
                            <p className="mt-1 text-slate-350">This requisition exceeds the remaining allocated budget threshold.</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="pt-2 flex justify-end space-x-3">
                        <button onClick={() => setActiveScene(4)} className="px-4 py-2 text-xs text-slate-400 font-semibold hover:text-white">Modify Request</button>
                        {hasContract ? (
                          <button onClick={() => {
                            setRequests(prev => prev.map(r => {
                              if (r.id === selectedRequestId) {
                                return {
                                  ...r,
                                  status: "PO Confirmed",
                                  history: [...r.history, { title: "Fast-Track Auto PO Created", date: "Now", desc: "Active Rate Contract bypassed manual sourcing." }]
                                };
                              }
                              return r;
                            }));
                            setActiveScene(11);
                          }} className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                            <span>Auto-Generate Purchase Order</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        ) : (
                          <button onClick={() => {
                            setRequests(prev => prev.map(r => {
                              if (r.id === selectedRequestId) {
                                return {
                                  ...r,
                                  status: "Pending Approval",
                                  history: [...r.history, { title: "Routed for Manager Approval", date: "Now", desc: "Negotiated contract routed for operational sign-off." }]
                                };
                              }
                              return r;
                            }));
                            setUserRole("Manager");
                            setActiveScene(10);
                          }} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                            <span>Route to Manager Approval</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 5: RATE CONTRACT CHECK --- */}
              {activeScene === 5 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 5: Active Contract Search</h2>
                      <p className="text-xs text-slate-400">AI queries the Odoo registry for valid Rate Contracts or pricing agreements.</p>
                    </div>
                    
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
                            <p className="text-sm text-slate-300">
                              Found active agreement registered in Odoo for this product category: 
                              <strong> ₹{getContractPrice(currentRequest.productName).toLocaleString()} / unit</strong>. 
                              Total Allocation: 
                              <strong> ₹{(currentRequest.productQty * getContractPrice(currentRequest.productName)).toLocaleString()}</strong>.
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex justify-end space-x-3 pt-2">
                          <button onClick={() => {
                            const contractRate = getContractPrice(currentRequest.productName);
                            setRequests(prev => prev.map(r => {
                              if (r.id === selectedRequestId) {
                                return {
                                  ...r,
                                  targetPrice: contractRate,
                                  totalCost: r.productQty * contractRate,
                                  vendor: "Primus Technologies"
                                };
                              }
                              return r;
                            }));
                            setActiveScene(9);
                          }} className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                            <span>Proceed to Budget Verification</span>
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
                        
                        <div className="flex justify-end space-x-3 pt-2">
                          <button onClick={() => {
                            setRequests(prev => prev.map(r => {
                              if (r.id === selectedRequestId) {
                                return {
                                  ...r,
                                  status: "Sourcing"
                                };
                              }
                              return r;
                            }));
                            setUserRole("SCM Buyer");
                            setScmTab('requests');
                            setActiveScene(6);
                          }} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                            <span>Launch RFQ Sourcing Portal</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* --- SCENE 6: SCM BUYER PORTAL (RFQ & BIDDING MANAGEMENT) --- */}
              {activeScene === 6 && (
                <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
                  
                  {/* SCM Sourcing Tab Selector */}
                  <div className="flex border-b border-slate-800">
                    <button 
                      onClick={() => setScmTab('requests')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${scmTab === 'requests' ? 'border-purple-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      Active Contract Requests (CR)
                    </button>
                    <button 
                      onClick={() => setScmTab('bidding')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${scmTab === 'bidding' ? 'border-purple-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      Bidding &amp; Live RFQs
                    </button>
                    <button 
                      onClick={() => setScmTab('discovery')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${scmTab === 'discovery' ? 'border-purple-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                    >
                      AI Vendor Sourcing Discovery
                    </button>
                  </div>

                  {/* SCM Tab 1: Contract Requests Queue */}
                  {scmTab === 'requests' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-outfit font-extrabold text-xl text-white">Pending Sourcing Workload</h3>
                          <p className="text-xs text-slate-400">Requisitions flagged by Odoo requiring vendor quotation sourcing.</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 gap-4">
                        {requests.filter(r => r.status === 'Sourcing').map(req => (
                          <div key={req.id} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs font-bold text-slate-500">{req.id}</span>
                                <span className="text-xs px-2.5 py-0.5 rounded bg-purple-550/20 text-purple-400 border border-purple-500/20 font-bold uppercase">SOURCING FALLBACK</span>
                              </div>
                              <h4 className="font-outfit font-extrabold text-lg text-white">{req.productQty}x {req.productName}</h4>
                              <p className="text-xs text-slate-450">Estimated Value: <strong>{req.totalCost > 0 ? `₹${req.totalCost.toLocaleString()}` : "TBD (Pending Sourcing Bids)"}</strong> | Mapped to: {req.expenseCategory}</p>
                            </div>

                            <div className="flex items-center space-x-3">
                              {/* Sourcing strategies selection */}
                              <select 
                                value={req.selectedSourcingMethod}
                                onChange={(e) => {
                                  const method = e.target.value as 'Direct' | 'RFQ' | 'Auction';
                                  setRequests(prev => prev.map(r => r.id === req.id ? { ...r, selectedSourcingMethod: method } : r));
                                }}
                                className="bg-slate-800 border border-slate-700/80 rounded-lg p-2 text-xs text-white focus:outline-none"
                              >
                                <option value="RFQ">Invite Preferred (Multi-RFQ)</option>
                                <option value="Direct">Direct Price Negotiator</option>
                                <option value="Auction">Live Reverse Auction</option>
                              </select>

                              <button 
                                onClick={() => { setSelectedRequestId(req.id); setScmTab('bidding'); }}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all"
                              >
                                Manage RFQ
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* SCM Tab 2: RFQ Bidding Events (Managing RFQs and bidding) */}
                  {scmTab === 'bidding' && (
                    <div className="space-y-6">
                      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-850 pb-4">
                          <div>
                            <span className="text-xs text-indigo-400 font-bold block">{currentRequest.id} Bidding Management</span>
                            <h3 className="font-outfit font-extrabold text-xl text-white">{currentRequest.productQty}x {currentRequest.productName}</h3>
                          </div>

                          <div className="mt-2 sm:mt-0 flex items-center space-x-2">
                            <span className="px-2.5 py-1 bg-purple-500/20 text-purple-400 border border-purple-500/25 rounded-md text-xs font-bold">
                              Sourcing: {currentRequest.selectedSourcingMethod} Mode
                            </span>
                          </div>
                        </div>

                        {/* Bid submissions table */}
                        <div className="space-y-3">
                          <h4 className="text-xs text-slate-500 font-bold uppercase tracking-wider">Active Vendor Bids (Received in real-time)</h4>
                          
                          {currentRequest.vendorBids.length === 0 ? (
                            <div className="p-6 text-center bg-slate-850/40 border border-slate-800 rounded-xl text-slate-400 text-xs">
                              No bids received yet. Invite vendors or click "Trigger Bidding" below to populate quotes.
                            </div>
                          ) : (
                            <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse text-xs">
                                <thead>
                                  <tr className="border-b border-slate-800 text-slate-500 font-bold">
                                    <th className="py-2.5">Supplier Name</th>
                                    <th className="py-2.5">Quote Price</th>
                                    <th className="py-2.5">Warranty SLA</th>
                                    <th className="py-2.5">Lead Time</th>
                                    <th className="py-2.5">Odoo Onboard Status</th>
                                  </tr>
                                </thead>
                                <tbody className="text-slate-300">
                                  {currentRequest.vendorBids.map((bid, idx) => (
                                    <tr key={idx} className="border-b border-slate-850">
                                      <td className="py-3 font-semibold">{bid.vendorName}</td>
                                      <td className="py-3 font-bold text-white">₹{bid.price.toLocaleString()}</td>
                                      <td className="py-3 text-slate-400">{bid.warranty}</td>
                                      <td className="py-3 text-slate-400">{bid.leadTime}</td>
                                      <td className="py-3">
                                        <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold text-[9px] uppercase border border-emerald-500/20">
                                          Approved Partner
                                        </span>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>

                        {/* Interactive simulation action controls */}
                        <div className="flex justify-between items-center pt-4 border-t border-slate-850">
                          <button 
                            onClick={() => {
                              // Simulate adding a bid from Primus Tech
                              setRequests(prev => prev.map(r => {
                                if (r.id === selectedRequestId) {
                                  return {
                                    ...r,
                                    vendorBids: [
                                      ...r.vendorBids,
                                      { vendorName: "Primus Technologies", price: r.targetPrice - 4000, leadTime: "5 Days", warranty: "3 Years On-Site", status: "Recommended" }
                                    ]
                                  };
                                }
                                return r;
                              }));
                              alert("Simulated: Vendor 'Primus Technologies' submitted a new quote.");
                            }}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-xs font-semibold rounded-lg text-slate-200 transition-all border border-slate-750"
                          >
                            Simulate Vendor Bid Submission
                          </button>

                          <div className="flex space-x-3">
                            <button 
                              onClick={() => setActiveScene(7)} 
                              className="px-4 py-2 border border-slate-700 hover:bg-slate-800 text-xs font-semibold rounded-lg text-slate-300"
                            >
                              Open Scorecard Matrix
                            </button>
                            <button 
                              onClick={() => {
                                resetNegotiation();
                                setActiveScene(8);
                              }} 
                              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white"
                            >
                              Launch AI Negotiation
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Mock Vendor Submission Form panel (To show how vendors interact) */}
                      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                        <div className="flex items-center space-x-2 text-indigo-400">
                          <Landmark className="h-4.5 w-4.5" />
                          <h4 className="font-outfit font-extrabold text-base text-white">Vendor Portal Simulation Workspace</h4>
                        </div>
                        <p className="text-xs text-slate-400">This simulates the external vendor's secure magic link. Entering details submits them to Odoo.</p>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs pt-2">
                          <div>
                            <label className="text-slate-500 block mb-1">Quote price per unit (₹):</label>
                            <input 
                              type="number"
                              value={vendorBidPrice}
                              onChange={(e) => setVendorBidPrice(e.target.value)}
                              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
                            />
                          </div>
                          <div>
                            <label className="text-slate-500 block mb-1">Delivery Lead Time:</label>
                            <input 
                              type="text"
                              value={vendorLeadTime}
                              onChange={(e) => setVendorLeadTime(e.target.value)}
                              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
                            />
                          </div>
                          <div className="flex items-end">
                            <button 
                              onClick={handleVendorBidSubmit}
                              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all"
                            >
                              Submit Vendor Bid to Odoo
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SCM Tab 3: AI Vendor Sourcing Discovery (Auto creation of draft vendor) */}
                  {scmTab === 'discovery' && (
                    <div className="space-y-6">
                      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                        <h3 className="font-outfit font-extrabold text-lg text-white">AI Sourcing Directory Discovery</h3>
                        <p className="text-xs text-slate-400">Search external B2B registries to resolve suppliers for non-catalog categories.</p>

                        <form onSubmit={handleSearchVendors} className="flex gap-2 max-w-lg">
                          <input 
                            type="text" 
                            value={searchVendorQuery}
                            onChange={(e) => setSearchVendorQuery(e.target.value)}
                            placeholder="Type product categories (e.g. Server components, desks)..."
                            className="flex-grow bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                          />
                          <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white">
                            Search registries
                          </button>
                        </form>
                      </div>

                      {/* Onboard Success Notification banner */}
                      {showDraftOnboardSuccess && (
                        <div className="p-4 bg-emerald-950/20 border border-emerald-900/40 rounded-xl flex items-start space-x-3 text-emerald-400 text-xs animate-fadeIn">
                          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="font-bold">Odoo Draft Partner Auto-Created!</p>
                            <p className="mt-1 text-slate-350">
                              Successfully registered <strong>{lastOnboardedVendor}</strong> as a draft partner in Odoo (Record ID: `res.partner.draft_092`). Magic link sent for onboard completion.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* SCM Discovery search result lists */}
                      {searchingVendors ? (
                        <div className="p-8 text-center text-xs text-slate-400">Searching B2B databases...</div>
                      ) : discoveredVendors.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {discoveredVendors.map((vendor, idx) => (
                            <div key={idx} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between h-56">
                              <div>
                                <span className="px-2 py-0.5 bg-slate-850 border border-slate-700/60 rounded text-[9px] font-bold text-slate-400 uppercase">
                                  External Discovery Match
                                </span>
                                <h4 className="font-outfit font-extrabold text-lg text-white mt-2">{vendor.name}</h4>
                                <p className="text-xs text-slate-450 mt-1">{vendor.category}</p>

                                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-850 text-xs text-slate-450">
                                  <span>Trust score: <strong>{vendor.rating}/100</strong></span>
                                  <span>AI Index: <strong>{vendor.score}%</strong></span>
                                </div>
                              </div>

                              <div className="flex justify-between items-center pt-2">
                                <span className="text-[10px] text-slate-550">Not in local Odoo Partner DB</span>
                                <button 
                                  onClick={() => handleAutoOnboard(vendor.name)}
                                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white"
                                >
                                  Auto-Create Draft Vendor
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-slate-450 text-xs">
                          Search above to simulate sourcing new suppliers from B2B catalogs.
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )}
              
              {/* --- SCENE 7: RFQ COMPARISON MATRIX --- */}
              {activeScene === 7 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 7: Side-by-Side RFQ Comparison</h2>
                      <p className="text-xs text-slate-400">Value scorecard compiled from active vendor bids in local Odoo database.</p>
                    </div>
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
                          <td className="py-3 px-4 bg-indigo-950/15 font-bold text-white">₹{getNegotiationBaselinePrice(currentRequest.productName).toLocaleString()}</td>
                          <td className="py-3 px-4">₹{(getNegotiationBaselinePrice(currentRequest.productName) + 3000).toLocaleString()}</td>
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
                      <button onClick={() => { setUserRole("SCM Buyer"); setScmTab('bidding'); setActiveScene(6); }} className="px-4 py-2 text-xs text-slate-400 font-semibold hover:text-white">Back to Sourcing</button>
                      <button onClick={() => setActiveScene(8)} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1">
                        <span>Trigger AI Negotiation</span>
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 8: AI NEGOTIATION LOUNGE --- */}
              {activeScene === 8 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 8: AI Autonomous Negotiation</h2>
                      <p className="text-xs text-slate-400">Watch the AI agent negotiate rates and terms directly with the supplier bot.</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="px-3 py-1 bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/25 rounded-full text-xs font-bold">
                        Savings: ₹{((getNegotiationBaselinePrice(currentRequest.productName) - currentOfferPrice) * currentRequest.productQty).toLocaleString()} (₹{(getNegotiationBaselinePrice(currentRequest.productName) - currentOfferPrice).toLocaleString()}/unit)
                      </span>
                      <button 
                        onClick={resetNegotiation}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-350"
                        title="Restart Negotiation"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 flex flex-col h-[400px] rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
                      <div className="p-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
                        <span className="text-xs text-slate-200 font-bold uppercase tracking-wider">Live Agent Log</span>
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                      </div>
                      
                      <div className="flex-grow p-4 overflow-y-auto space-y-4">
                        {chatLog.length === 0 ? (
                          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                            <div className="h-12 w-12 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                              <Sparkles className="h-6 w-6" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-350">Negotiation Lounge Ready</p>
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
                          <span className="text-xs text-emerald-400 font-bold flex items-center space-x-1 animate-fadeIn">
                            <CheckCircle2 className="h-4 w-4" />
                            <span>Agreement Locked &amp; Confirmed</span>
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                        <h3 className="font-outfit text-base font-bold text-slate-200 border-b border-slate-800 pb-2">Deal Tracker</h3>
                        
                        <div className="space-y-3 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Original Bid:</span>
                            <span className="font-semibold text-slate-350">₹{getNegotiationBaselinePrice(currentRequest.productName).toLocaleString()} / unit</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Negotiated Rate:</span>
                            <span className="font-bold text-emerald-400">₹{currentOfferPrice.toLocaleString()} / unit</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Savings ({currentRequest.productQty} units):</span>
                            <span className="font-bold text-emerald-400">₹{((getNegotiationBaselinePrice(currentRequest.productName) - currentOfferPrice) * currentRequest.productQty).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                      
                      {negotiationComplete && (
                        <button 
                          onClick={() => {
                            setRequests(prev => prev.map(r => r.id === selectedRequestId ? { ...r, targetPrice: currentOfferPrice, totalCost: currentOfferPrice * r.productQty, vendor: "Primus Technologies" } : r));
                            setActiveScene(9);
                          }}
                          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-xl text-white transition-all shadow-lg flex items-center justify-center space-x-2"
                        >
                          <span>Proceed to Budget Verification</span>
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
                      <p className="text-xs text-slate-400">Simplifying decision metrics for managers. No complex ERP menus.</p>
                    </div>
                    
                    <span className="px-3 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/25 rounded-full text-xs font-bold">
                      Pending Approvals: {requests.filter(r => r.status === 'Pending Approval').length}
                    </span>
                  </div>
                  
                  {requests.filter(r => r.status === 'Pending Approval').length === 0 ? (
                    <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-2xl text-slate-450">
                      <CheckCircle2 className="h-8 w-8 mx-auto text-emerald-400 mb-2" />
                      <p className="text-sm font-semibold">All caught up!</p>
                      <p className="text-xs mt-1">No requisitions currently require your approval.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {requests.filter(r => r.status === 'Pending Approval').map(req => (
                        <div key={req.id} className="p-6 rounded-2xl bg-slate-900 border border-indigo-500/30 shadow-2xl space-y-6">
                          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                            <div className="flex items-center space-x-3">
                              <div className="h-10 w-10 rounded-full bg-slate-850 flex items-center justify-center text-slate-350 font-bold text-sm">AV</div>
                              <div>
                                <p className="text-xs text-slate-500 font-semibold uppercase">Requisition Initiator:</p>
                                <p className="text-sm font-bold text-white">Anjitha V (IT Ops Specialist)</p>
                              </div>
                            </div>
                            <span className="text-xs text-slate-500 font-bold">{req.id}</span>
                          </div>
                          
                          <div className="space-y-4">
                            <h3 className="font-outfit font-extrabold text-white text-lg">{req.productQty}x {req.productName}</h3>
                            
                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <span className="text-slate-500 block">Total cost:</span>
                                <span className="font-bold text-white">₹{req.totalCost.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="text-slate-550 block text-emerald-400">Negotiated Savings:</span>
                                <span className="font-bold text-emerald-400">₹{req.savings.toLocaleString()} Saved</span>
                              </div>
                              <div>
                                <span className="text-slate-550 block">Budget Mapped:</span>
                                <span className="font-bold text-slate-300">{req.expenseCategory}</span>
                              </div>
                              <div>
                                <span className="text-slate-550 block">Vendor Assigned:</span>
                                <span className="font-bold text-slate-300">{req.vendor}</span>
                              </div>
                            </div>

                            {/* Manager clarification comments history */}
                            {req.clarificationComments.length > 0 && (
                              <div className="p-4 bg-slate-850 rounded-xl space-y-2 border border-slate-800 text-xs">
                                <span className="font-bold text-slate-400 block border-b border-slate-800 pb-1">Clarification Thread</span>
                                {req.clarificationComments.map((c, cidx) => (
                                  <p key={cidx} className="mt-1 text-[11px] leading-relaxed">
                                    <strong className={c.role === 'manager' ? 'text-amber-400' : 'text-indigo-400'}>
                                      {c.role === 'manager' ? 'Manager: ' : 'Anjitha: '}
                                    </strong>
                                    <span className="text-slate-300">"{c.text}"</span>
                                  </p>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Action Buttons group (Approve, Reject, Request Info) */}
                          <div className="flex flex-wrap justify-end gap-2 border-t border-slate-800 pt-4">
                            <button 
                              onClick={() => {
                                setRequests(prev => prev.map(r => r.id === req.id ? { ...r, status: "Rejected", history: [...r.history, { title: "Rejected", date: "Now", desc: "Rejected by Manager" }] } : r));
                              }}
                              className="px-4 py-2 border border-slate-800 hover:bg-rose-950/20 hover:border-rose-500 text-xs font-semibold rounded-lg text-slate-400 hover:text-rose-400 transition-all"
                            >
                              Reject
                            </button>
                            
                            {/* Request Info button triggers dialog */}
                            <button 
                              onClick={() => {
                                setSelectedRequestId(req.id);
                                setShowManagerQueryBox(true);
                              }}
                              className="px-4 py-2 border border-slate-800 hover:bg-amber-950/20 hover:border-amber-500 text-xs font-semibold rounded-lg text-slate-400 hover:text-amber-400 transition-all"
                            >
                              Request Info
                            </button>

                            <button 
                              onClick={() => handleManagerApprove(req.id)}
                              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                            >
                              <Check className="h-4.5 w-4.5" />
                              <span>Approve Request</span>
                            </button>
                          </div>

                          {/* Request Info Dialogue Card */}
                          {showManagerQueryBox && selectedRequestId === req.id && (
                            <div className="p-4 bg-slate-850 rounded-xl border border-amber-500/30 space-y-3 text-xs animate-fadeIn">
                              <label className="font-bold text-slate-200 block">Ask Initiator for clarification:</label>
                              <input 
                                type="text"
                                value={managerQueryText}
                                onChange={(e) => setManagerQueryText(e.target.value)}
                                placeholder="e.g. Please clarify unit requirements and pricing details..."
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none"
                              />
                              <div className="flex justify-end space-x-2">
                                <button onClick={() => setShowManagerQueryBox(false)} className="px-3 py-1.5 text-slate-400 hover:text-white">Cancel</button>
                                <button 
                                  onClick={() => handleRequestInfoSubmit(req.id)} 
                                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded"
                                >
                                  Send Request
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* --- SCENE 11: REQUEST TRACKING TIMELINE --- */}
              {activeScene === 11 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 11: Request Tracking Milestone</h2>
                      <p className="text-xs text-slate-400">Amazon-style simple progress tracker hiding deep transactional ERP states.</p>
                    </div>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-8">
                    <div className="relative flex justify-between items-center max-w-2xl mx-auto py-4">
                      <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-slate-800 z-0" />
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-emerald-500 z-0" style={{ width: '100%' }} />
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-slate-200">Submitted</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-slate-200">Sourcing</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-slate-200">Approved</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-slate-200">PO Sent</span>
                      </div>
                    </div>

                    <div className="flex justify-end pt-4 border-t border-slate-800/60">
                      <button 
                        onClick={() => setActiveScene(12)}
                        className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1 shadow-lg"
                      >
                        <span>Proceed to Product Receiving</span>
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* --- SCENE 12: PRODUCT RECEIVING & INSPECTION (GRN) --- */}
              {activeScene === 12 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 12: Product Receiving &amp; Goods Receipt Note</h2>
                      <p className="text-xs text-slate-400">Simulate warehouse operations. Inspect the delivered items and generate the GRN in Odoo.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                      <div className="flex items-center space-x-3 text-indigo-400">
                        <Truck className="h-5 w-5" />
                        <h3 className="font-outfit text-lg font-bold text-slate-200">Goods Receipt Portal</h3>
                      </div>

                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Source PO</span>
                            <span className="text-sm font-semibold text-slate-350 bg-slate-800/50 border border-slate-750 rounded-lg p-2 block">PO-2026-003</span>
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Vendor</span>
                            <span className="text-sm font-semibold text-slate-350 bg-slate-800/50 border border-slate-750 rounded-lg p-2 block">{currentRequest.vendor || "Primus Technologies"}</span>
                          </div>
                        </div>

                        <div>
                          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Product Details</span>
                          <span className="text-sm font-semibold text-slate-350 bg-slate-800/50 border border-slate-750 rounded-lg p-2 block">{currentRequest.productName}</span>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block mb-1">Ordered Qty</span>
                            <span className="text-sm font-semibold text-slate-350 bg-slate-800/50 border border-slate-750 rounded-lg p-2 block">{currentRequest.productQty} units</span>
                          </div>
                          <div>
                            <label className="text-xs text-indigo-400 font-bold uppercase tracking-wider block mb-1">Delivered Qty</label>
                            <input 
                              type="number" 
                              value={deliveredQty} 
                              onChange={(e) => setDeliveredQty(Number(e.target.value))}
                              className="w-full bg-slate-800 border border-indigo-500/50 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500 font-semibold"
                            />
                          </div>
                        </div>

                        <div className="pt-2">
                          <label className="flex items-center space-x-2.5 cursor-pointer select-none">
                            <input 
                              type="checkbox" 
                              checked={qualityPassed}
                              onChange={(e) => setQualityPassed(e.target.checked)}
                              className="rounded border-slate-755 text-indigo-600 focus:ring-indigo-500 h-4.5 w-4.5 bg-slate-800"
                            />
                            <span className="text-sm text-slate-300 font-medium">Quality Inspection Approved: Items match specs with no defects</span>
                          </label>
                        </div>
                      </div>

                      {grnGenerated ? (
                        <div className="p-4 bg-emerald-950/20 border border-emerald-900/40 rounded-xl space-y-3 animate-fadeIn">
                          <div className="flex items-start space-x-3 text-emerald-400 text-xs">
                            <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <div>
                              <p className="font-bold">Goods Receipt Note (GRN-2026-089) Generated</p>
                              <p className="mt-1 text-slate-350">Successfully posted to Odoo. Stock levels updated at Bangalore Warehouse. Handing off to Accounts Payable.</p>
                            </div>
                          </div>
                          <div className="flex justify-end pt-2">
                            <button 
                              onClick={() => {
                                setRequests(prev => prev.map(r => {
                                  if (r.id === selectedRequestId) {
                                    return {
                                      ...r,
                                      history: [...r.history, { title: "Goods Received (GRN-2026-089)", date: "Now", desc: `Received ${deliveredQty}/${r.productQty} units. Quality inspect: PASSED.` }]
                                    };
                                  }
                                  return r;
                                }));
                                setActiveScene(13);
                              }}
                              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                            >
                              <span>Proceed to 3-Way Match Audit</span>
                              <ArrowRight className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="pt-2 flex justify-end space-x-3">
                          <button 
                            onClick={() => {
                              if (!qualityPassed) {
                                alert("Please perform quality inspection before generating GRN.");
                                return;
                              }
                              setGrnGenerated(true);
                            }}
                            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                          >
                            <span>Validate &amp; Generate GRN</span>
                            <Check className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 h-fit">
                      <div className="flex items-center space-x-2 text-indigo-400">
                        <Package className="h-4.5 w-4.5" />
                        <h4 className="font-outfit font-extrabold text-sm text-white">Odoo Warehouse Status</h4>
                      </div>
                      <div className="space-y-3 text-xs">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Destination:</span>
                          <span className="font-semibold text-slate-350">Bangalore Warehouse</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Carrier:</span>
                          <span className="font-semibold text-slate-350">Blue Dart Express</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Waybill Ref:</span>
                          <span className="font-mono text-indigo-400">AWB-77291024</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* --- SCENE 13: VENDOR BILL 3-WAY MATCHING --- */}
              {activeScene === 13 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 13: Automated 3-Way Match Verification</h2>
                      <p className="text-xs text-slate-400">Audit and reconcile PO details, Goods Receipt note, and Vendor Invoice side-by-side.</p>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                    <div className="flex items-center space-x-3 text-indigo-400">
                      <ShieldCheck className="h-5.5 w-5.5" />
                      <h3 className="font-outfit text-lg font-bold text-slate-200">Reconciliation Matrix</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Column 1: PO */}
                      <div className="p-4 rounded-xl bg-slate-850 border border-slate-750 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-indigo-400 uppercase">1. Purchase Order</span>
                          <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold text-[9px]">PO-2026-003</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Qty Ordered:</span>
                            <span className="font-semibold text-slate-200">{currentRequest.productQty} units</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Rate:</span>
                            <span className="font-semibold text-slate-200">₹{currentRequest.targetPrice.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-slate-800">
                            <span className="text-slate-400">Total amount:</span>
                            <span className="font-bold text-slate-200">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Column 2: GRN */}
                      <div className="p-4 rounded-xl bg-slate-850 border border-slate-750 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-indigo-400 uppercase">2. Goods Receipt</span>
                          <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold text-[9px]">GRN-2026-089</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Qty Received:</span>
                            <span className="font-semibold text-slate-200">{deliveredQty} units</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Quality Check:</span>
                            <span className="font-bold text-emerald-400">PASSED</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-slate-800">
                            <span className="text-slate-400">Stock Status:</span>
                            <span className="font-bold text-emerald-400">Posted</span>
                          </div>
                        </div>
                      </div>

                      {/* Column 3: Invoice */}
                      <div className="p-4 rounded-xl bg-slate-850 border border-slate-750 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-indigo-400 uppercase">3. Vendor Invoice</span>
                          <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 font-bold text-[9px]">BILL-2026-045</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Qty Billed:</span>
                            <span className="font-semibold text-slate-200">{currentRequest.productQty} units</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Rate Billed:</span>
                            <span className="font-semibold text-slate-200">₹{currentRequest.targetPrice.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-slate-800">
                            <span className="text-slate-400">Total Billed:</span>
                            <span className="font-bold text-slate-200">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="p-5 bg-emerald-950/20 border border-emerald-900/40 rounded-xl flex items-start space-x-3 text-emerald-400 text-xs">
                      <CheckCircle2 className="h-5.5 w-5.5 flex-shrink-0 mt-0.5 text-emerald-400" />
                      <div>
                        <p className="font-bold text-sm">3-Way Match Verification Success</p>
                        <p className="mt-1 text-slate-350 text-xs">All comparison checks pass. PO quantities, GRN warehouse receipts, and the PDF extracted vendor invoice details match 100%. Ready for general ledger posting.</p>
                      </div>
                    </div>

                    {billPosted ? (
                      <div className="p-4 bg-slate-850 rounded-xl flex justify-between items-center animate-fadeIn text-xs">
                        <span className="text-slate-400">Vendor Bill successfully posted to accounts payable.</span>
                        <button 
                          onClick={() => {
                            setRequests(prev => prev.map(r => {
                              if (r.id === selectedRequestId) {
                                return {
                                  ...r,
                                  history: [...r.history, { title: "Vendor Bill Posted (BILL-2026-045)", date: "Now", desc: `Posted total AP liability of ₹${r.totalCost.toLocaleString()}.` }]
                                };
                              }
                              return r;
                            }));
                            setActiveScene(14);
                          }}
                          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                        >
                          <span>Proceed to Payment Execution</span>
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex justify-end pt-2">
                        <button 
                          onClick={() => setBillPosted(true)}
                          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1 shadow-lg"
                        >
                          <span>Post Vendor Bill to Ledger</span>
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* --- SCENE 14: PAYMENT PROCESSING & RECONCILIATION --- */}
              {activeScene === 14 && (
                <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 14: Payment Disbursement &amp; Reconciliation</h2>
                      <p className="text-xs text-slate-400">Authorize the cash disbursement and auto-reconcile bank statements in Odoo.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
                      <div className="flex items-center space-x-3 text-indigo-400">
                        <CreditCard className="h-5 w-5" />
                        <h3 className="font-outfit text-lg font-bold text-slate-200">Disbursement Voucher</h3>
                      </div>

                      <div className="space-y-4 text-xs">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-slate-500 font-bold uppercase tracking-wider block mb-1">Beneficiary Vendor</span>
                            <span className="text-sm font-semibold text-slate-200 block bg-slate-850 p-2.5 rounded-lg border border-slate-750">{currentRequest.vendor || "Primus Technologies"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 font-bold uppercase tracking-wider block mb-1">Invoice Reference</span>
                            <span className="text-sm font-semibold text-slate-200 block bg-slate-850 p-2.5 rounded-lg border border-slate-750 font-mono">BILL-2026-045</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-slate-500 font-bold uppercase tracking-wider block mb-1">Paying Bank A/c</span>
                            <span className="text-sm font-semibold text-slate-200 block bg-slate-850 p-2.5 rounded-lg border border-slate-750">HDFC Corporate A/c (*9824)</span>
                          </div>
                          <div>
                            <span className="text-slate-500 font-bold uppercase tracking-wider block mb-1">Settlement Amount</span>
                            <span className="text-sm font-extrabold text-indigo-400 block bg-slate-850 p-2.5 rounded-lg border border-slate-750">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-indigo-400 font-bold uppercase tracking-wider block mb-1">Payment Method</label>
                            <select 
                              value={paymentMethod}
                              onChange={(e) => setPaymentMethod(e.target.value)}
                              className="w-full bg-slate-800 border border-slate-750 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 font-semibold"
                            >
                              <option value="Bank Transfer">Bank Transfer (NEFT/RTGS)</option>
                              <option value="Corporate Card">Corporate Card</option>
                              <option value="UPI Pay">UPI Corporate Pay</option>
                            </select>
                          </div>
                          <div>
                            <span className="text-slate-500 font-bold uppercase tracking-wider block mb-1">Value Date</span>
                            <span className="text-sm font-semibold text-slate-200 block bg-slate-850 p-2.5 rounded-lg border border-slate-750">July 13, 2026</span>
                          </div>
                        </div>
                      </div>

                      {paymentComplete ? (
                        <div className="p-4 bg-emerald-950/20 border border-emerald-900/40 rounded-xl space-y-3 animate-fadeIn">
                          <div className="flex items-start space-x-3 text-emerald-400 text-xs">
                            <CheckCircle2 className="h-5.5 w-5.5 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <div>
                              <p className="font-bold">Payment Completed &amp; Reconciled</p>
                              <p className="mt-1 text-slate-350">Transaction posted successfully. Odoo auto-reconciliation engine verified the bank statement entry against HDFC corporate accounts. Invoice status: PAID.</p>
                            </div>
                          </div>
                          <div className="flex justify-end pt-2">
                            <button 
                              onClick={() => {
                                setRequests(prev => prev.map(r => {
                                  if (r.id === selectedRequestId) {
                                    return {
                                      ...r,
                                      status: "Paid",
                                      history: [...r.history, { title: "Payment Cleared & Reconciled", date: "Now", desc: `Paid ₹${r.totalCost.toLocaleString()} via ${paymentMethod}. Ref: TXN-98402517.` }]
                                    };
                                  }
                                  return r;
                                }));
                                setActiveScene(15);
                              }}
                              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1"
                            >
                              <span>Proceed to Spend Intelligence</span>
                              <ArrowRight className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-end pt-2">
                          <button 
                            onClick={() => setPaymentComplete(true)}
                            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold rounded-lg text-white transition-all flex items-center space-x-1 shadow-lg"
                          >
                            <span>Authorize &amp; Pay Invoice</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 h-fit text-xs">
                      <div className="flex items-center space-x-2 text-indigo-400 mb-2">
                        <Landmark className="h-4.5 w-4.5" />
                        <h4 className="font-outfit font-extrabold text-sm text-white">Bank Statement Audit</h4>
                      </div>
                      <div className="space-y-3">
                        <div className="p-3 bg-slate-850 rounded-lg border border-slate-750 flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-slate-200">HDFC Bank Ledger</p>
                            <p className="text-[10px] text-slate-500 font-mono">STMT-99281-2026</p>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold text-[9px]">Matched</span>
                        </div>
                        <p className="text-slate-400 leading-relaxed text-[11px]">AI matches banking feeds with internal ledgers in real-time, removing manual end-of-month reconciliation tasks.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* --- SCENE 15: spend INTELLIGENCE ANALYTICS --- */}
              {activeScene === 15 && (
                <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-white">Scene 15: Spend Intelligence Dashboard</h2>
                      <p className="text-xs text-slate-400">High-level capital monitoring and automated fraud detection audits.</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block">Total Capital Audited</span>
                        <p className="text-3xl font-outfit font-extrabold text-white mt-1">₹4.58 Crore</p>
                      </div>
                    </div>
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs text-emerald-400 font-bold uppercase tracking-wider block">Autonomous AI Savings</span>
                        <p className="text-3xl font-outfit font-extrabold text-emerald-400 mt-1">₹28.45 Lakhs</p>
                      </div>
                    </div>
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs text-rose-455 font-bold uppercase tracking-wider block text-rose-400">Blocked Anomalies</span>
                        <p className="text-3xl font-outfit font-extrabold text-rose-400 mt-1">4 Breaches</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
            </div>
          </main>
        </div>
      )}
      
    </div>
  );
}
