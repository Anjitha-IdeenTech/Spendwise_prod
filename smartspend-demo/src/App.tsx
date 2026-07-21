import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Mic, FileText, Keyboard, LayoutDashboard, Send, 
  TrendingUp, DollarSign, ShieldAlert, Award, FileSpreadsheet, 
  ArrowRight, User, Settings, CheckCircle2, ChevronRight, 
  Play, RefreshCw, X, AlertTriangle, AlertCircle, Check, 
  HelpCircle, Volume2, ShieldCheck, Landmark, Briefcase, FileInput, 
  Calendar, Layers, Clock, Users, ArrowUpRight, ArrowDownRight, Menu,
  Paperclip, MessageSquare, History, Search, Eye, Filter,
  Truck, Package, Receipt, CreditCard, Moon, Sun, Bell
} from 'lucide-react';

// Define the Scene IDs and names
const SCENES = [
  { id: 1, name: "Scene 1: Login & Portal Selector" },
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
  department: string;
  expenseCategory: string;
  status: 'Draft' | 'Pending Approval' | 'Needs Clarification' | 'Sourcing' | 'Approved' | 'PO Confirmed' | 'Rejected' | 'Paid';
  urgency: 'High' | 'Medium' | 'Low';
  createdDate: string;
  deliveryDate?: string;
  buyer: string;
  vendor: string;
  savings: number;
  history: Array<{ title: string; date: string; desc?: string }>;
  clarificationComments: Array<{ role: 'manager' | 'employee'; text: string; date: string }>;
  vendorBids: Array<{ vendorName: string; price: number; leadTime: string; warranty: string; status: string }>;
  selectedSourcingMethod: 'Direct' | 'RFQ' | 'Auction';
  attachments: string[];
  lineItems?: Array<{ productName: string; productQty: number; targetPrice: number }>;
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

// ---- Lightweight SVG charts (categorical palette validated CVD-safe on light) ----
const CHART_COLORS = ['#6D5AE0', '#0E8F6A', '#C77E00', '#2E7FC7', '#C43D7E', '#8A8F9C'];

// Status colors — theme-blended, used for status tiles / dense request cards.
const STATUS_META: Record<string, { color: string; short: string }> = {
  'Draft': { color: '#8A8F9C', short: 'Draft' },
  'Pending Approval': { color: '#D99A3C', short: 'Pending' },
  'Needs Clarification': { color: '#E06C4E', short: 'Clarify' },
  'Sourcing': { color: '#4F9EE8', short: 'Sourcing' },
  'Approved': { color: '#2FB574', short: 'Approved' },
  'PO Confirmed': { color: '#7C6CF6', short: 'PO Confirmed' },
  'Rejected': { color: '#E5484D', short: 'Rejected' },
  'Paid': { color: '#0E8F6A', short: 'Paid' },
};
const statusColor = (s: string) => STATUS_META[s]?.color ?? '#8A8F9C';

// Compact request lifecycle stages (for inline mini-trackers on tiles).
const STAGE_LABELS = ['Submitted', 'Approved', 'Sourcing', 'PO', 'Received', 'Paid'];
const STATUS_STAGE: Record<string, number> = {
  'Draft': 0, 'Pending Approval': 0, 'Needs Clarification': 0, 'Rejected': 0,
  'Approved': 1, 'Sourcing': 2, 'PO Confirmed': 3, 'Paid': 5,
};
const statusStage = (s: string) => STATUS_STAGE[s] ?? 0;

interface Datum { label: string; value: number; }

// Donut for composition/identity (branch share of spend) + legend with values.
function DonutChart({ data, prefix = '', suffix = '' }: { data: Datum[]; prefix?: string; suffix?: string }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const R = 56, C = 2 * Math.PI * R, GAP = 3;
  let offset = 0;
  return (
    <div className="flex items-center gap-5 flex-wrap">
      <div className="relative flex-shrink-0">
        <svg viewBox="0 0 140 140" className="h-36 w-36 -rotate-90">
          <circle cx="70" cy="70" r={R} fill="none" stroke="rgb(var(--bg-secondary))" strokeWidth="15" />
          {data.map((d, i) => {
            const frac = d.value / total;
            const len = Math.max(frac * C - GAP, 0);
            const el = (
              <circle key={i} cx="70" cy="70" r={R} fill="none" stroke={CHART_COLORS[i % CHART_COLORS.length]}
                strokeWidth="15" strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-offset} />
            );
            offset += frac * C;
            return el;
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] text-textFaint font-semibold uppercase tracking-wider">Total</span>
          <span className="text-lg font-extrabold text-textPrimary font-outfit">{prefix}{total.toFixed(2)}{suffix}</span>
        </div>
      </div>
      <div className="space-y-1.5 min-w-[9rem]">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className="h-2.5 w-2.5 rounded-full flex-shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
            <span className="text-textSecondary font-medium w-24 truncate">{d.label}</span>
            <span className="text-textPrimary font-bold tabular-nums ml-auto">{prefix}{d.value}{suffix}</span>
            <span className="text-textFaint tabular-nums w-8 text-right">{Math.round((d.value / total) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Horizontal magnitude bars — single hue, sorted, direct-labeled.
function BarList({ data, color = '#7C6CF6', prefix = '', suffix = '' }: { data: Datum[]; color?: string; prefix?: string; suffix?: string }) {
  const max = Math.max(...data.map(d => d.value), 1);
  return (
    <div className="space-y-3">
      {[...data].sort((a, b) => b.value - a.value).map((d, i) => (
        <div key={i}>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-textSecondary font-medium truncate pr-2">{d.label}</span>
            <span className="text-textPrimary font-bold tabular-nums">{prefix}{d.value}{suffix}</span>
          </div>
          <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
            <div className="h-full rounded-full transition-all duration-700 ease-out"
              style={{ width: `${(d.value / max) * 100}%`, background: `linear-gradient(90deg, ${color}, ${color}bb)` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

// Company-wide spend analytics for the CEO / consolidated dashboards (₹ Crore).
const spendAnalytics = {
  byBranch: [
    { label: 'Bangalore', value: 1.62 },
    { label: 'Mumbai', value: 1.18 },
    { label: 'Kochi', value: 0.86 },
    { label: 'Delhi', value: 0.58 },
    { label: 'Chennai', value: 0.34 },
  ] as Datum[],
  byDepartment: [
    { label: 'IT & Infrastructure', value: 1.94 },
    { label: 'Operations', value: 1.12 },
    { label: 'Facilities', value: 0.72 },
    { label: 'Marketing', value: 0.48 },
    { label: 'Finance', value: 0.32 },
  ] as Datum[],
  byCategory: [
    { label: 'IT Hardware', value: 1.48 },
    { label: 'Datacenter Equipment', value: 0.92 },
    { label: 'Software Licenses', value: 0.74 },
    { label: 'Office Furniture', value: 0.56 },
    { label: 'Professional Services', value: 0.44 },
    { label: 'MRO Supplies', value: 0.44 },
  ] as Datum[],
  byMonth: [
    { label: 'Feb', value: 0.52 },
    { label: 'Mar', value: 0.61 },
    { label: 'Apr', value: 0.74 },
    { label: 'May', value: 0.69 },
    { label: 'Jun', value: 0.88 },
    { label: 'Jul', value: 1.14 },
  ] as Datum[],
};

export default function App() {
  // Global States
  const params = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
  const [activeScene, setActiveScene] = useState<number>(() => {
    const sc = Number(params?.get('scene'));
    return sc >= 1 && sc <= 15 ? sc : 1;
  });
  // --- Dark theme disabled — light (Aurora) theme only for now. ---
  // To re-enable: restore the stateful darkMode block (see git history) and
  // un-comment the "Appearance" toggle in the sidebar below. The `.dark` rules
  // in index.css stay inert while this is false.
  // const [darkMode, setDarkMode] = useState<boolean>(() => {
  //   const q = params?.get('theme');
  //   if (q === 'light') return false;
  //   if (q === 'dark') return true;
  //   try {
  //     const saved = localStorage.getItem('smartspend-theme-v2');
  //     if (saved) return saved === 'dark';
  //   } catch { /* ignore */ }
  //   return false; // default to the light theme
  // });
  const darkMode = false; // force light theme
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [userRole, setUserRole] = useState<string>("Employee"); // Employee, Manager, SCM Buyer, Vendor, CEO

  // Apply the active theme by toggling the `dark` class on <html>. With dark
  // mode disabled this always resolves to light and also clears any stale
  // `dark` class / preference left in localStorage from a previous session.
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    try { localStorage.setItem('smartspend-theme-v2', darkMode ? 'dark' : 'light'); } catch { /* ignore */ }
  }, [darkMode]);

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
      department: "IT & Infrastructure",
      expenseCategory: "IT Hardware & Laptops",
      status: "Pending Approval",
      urgency: "High",
      createdDate: "July 08, 08:30",
      deliveryDate: "Jul 18, 2026",
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
      department: "Facilities",
      expenseCategory: "Office Furniture",
      status: "PO Confirmed",
      urgency: "Medium",
      createdDate: "July 05, 11:20",
      deliveryDate: "Jul 12, 2026",
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
      department: "IT & Infrastructure",
      expenseCategory: "Datacenter Equipment",
      status: "Sourcing",
      urgency: "High",
      createdDate: "July 09, 09:15",
      deliveryDate: "Jul 20, 2026",
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
    },
    {
      id: "PR-2026-095", productName: "Adobe Creative Cloud Licenses", productQty: 25, targetPrice: 4200,
      totalCost: 105000, location: "Delhi Office", department: "Marketing", expenseCategory: "Software Licenses",
      status: "Approved", urgency: "Medium", createdDate: "Jul 10, 10:05", deliveryDate: "Jul 15, 2026",
      buyer: "SCM-SW-08", vendor: "Adobe India", savings: 12000,
      history: [{ title: "Request Submitted", date: "Jul 10, 10:05" }, { title: "Approved by Manager", date: "Jul 10, 13:20", desc: "Approved by Marketing Head" }],
      clarificationComments: [], vendorBids: [{ vendorName: "Adobe India", price: 4200, leadTime: "Instant", warranty: "1 Year", status: "Selected" }],
      selectedSourcingMethod: "Direct", attachments: ["license_quote.pdf"]
    },
    {
      id: "PR-2026-101", productName: "Industrial UPS Units", productQty: 4, targetPrice: 85000,
      totalCost: 340000, location: "Mumbai Office", department: "Operations", expenseCategory: "Datacenter Equipment",
      status: "Pending Approval", urgency: "High", createdDate: "Jul 11, 09:40", deliveryDate: "Jul 25, 2026",
      buyer: "SCM-IT-14", vendor: "PowerGrid Solutions", savings: 22000,
      history: [{ title: "Request Submitted", date: "Jul 11, 09:40" }, { title: "Budget Checked", date: "Jul 11, 09:42", desc: "Verified against Ops capex" }],
      clarificationComments: [], vendorBids: [{ vendorName: "PowerGrid Solutions", price: 83000, leadTime: "8 Days", warranty: "3 Years", status: "Recommended" }, { vendorName: "VoltEdge", price: 88000, leadTime: "6 Days", warranty: "2 Years", status: "Qualified" }],
      selectedSourcingMethod: "RFQ", attachments: ["ups_specs.pdf", "site_layout.pdf"]
    },
    {
      id: "PR-2026-104", productName: "Marketing Event Booth Setup", productQty: 1, targetPrice: 180000,
      totalCost: 180000, location: "Bangalore Office", department: "Marketing", expenseCategory: "Professional Services",
      status: "Sourcing", urgency: "Medium", createdDate: "Jul 12, 14:20", deliveryDate: "Aug 02, 2026",
      buyer: "SCM-MKT-02", vendor: "Pending Sourcing", savings: 0,
      history: [{ title: "Request Submitted", date: "Jul 12, 14:20" }, { title: "Sourcing Triggered", date: "Jul 12, 14:25", desc: "Routed to SCM buyer for RFQ" }],
      clarificationComments: [], vendorBids: [{ vendorName: "EventCraft", price: 178000, leadTime: "15 Days", warranty: "NA", status: "Submitted" }],
      selectedSourcingMethod: "RFQ", attachments: ["booth_brief.pdf"]
    },
    {
      id: "PR-2026-108", productName: "Pantry & Housekeeping Supplies (Q3)", productQty: 1, targetPrice: 65000,
      totalCost: 65000, location: "Chennai Office", department: "Facilities", expenseCategory: "MRO Supplies",
      status: "PO Confirmed", urgency: "Low", createdDate: "Jul 06, 16:10", deliveryDate: "Jul 14, 2026",
      buyer: "SCM-FUR-03", vendor: "CleanServe", savings: 4000,
      history: [{ title: "Request Submitted", date: "Jul 06, 16:10" }, { title: "PO Created: PO-2026-011", date: "Jul 06, 17:30", desc: "Sent to CleanServe" }],
      clarificationComments: [], vendorBids: [{ vendorName: "CleanServe", price: 65000, leadTime: "4 Days", warranty: "NA", status: "Selected" }],
      selectedSourcingMethod: "Direct", attachments: []
    },
    {
      id: "PR-2026-112", productName: "Standing Desks (Ergonomic)", productQty: 15, targetPrice: 22000,
      totalCost: 330000, location: "Kochi Head Office", department: "Facilities", expenseCategory: "Office Furniture",
      status: "Pending Approval", urgency: "Medium", createdDate: "Jul 13, 11:00", deliveryDate: "Jul 28, 2026",
      buyer: "SCM-FUR-03", vendor: "ErgoWorks", savings: 18000,
      history: [{ title: "Request Submitted", date: "Jul 13, 11:00" }, { title: "Budget Checked", date: "Jul 13, 11:03", desc: "Verified against Facilities budget" }],
      clarificationComments: [], vendorBids: [{ vendorName: "ErgoWorks", price: 21500, leadTime: "12 Days", warranty: "5 Years", status: "Recommended" }, { vendorName: "DeskPro", price: 23000, leadTime: "9 Days", warranty: "3 Years", status: "Qualified" }],
      selectedSourcingMethod: "RFQ", attachments: ["ergo_catalog.pdf"]
    },
    {
      id: "PR-2026-115", productName: "Next-Gen Firewall Appliances", productQty: 3, targetPrice: 145000,
      totalCost: 435000, location: "Bangalore Office", department: "IT & Infrastructure", expenseCategory: "Datacenter Equipment",
      status: "Needs Clarification", urgency: "High", createdDate: "Jul 14, 08:50", deliveryDate: "Jul 30, 2026",
      buyer: "SCM-IT-14", vendor: "SecureNet", savings: 0,
      history: [{ title: "Request Submitted", date: "Jul 14, 08:50" }, { title: "Info Requested", date: "Jul 14, 10:15", desc: "Manager asked for clarification" }],
      clarificationComments: [{ role: "manager", text: "Do these replace the existing units or are they additions to capacity?", date: "Jul 14, 10:15" }],
      vendorBids: [{ vendorName: "SecureNet", price: 143000, leadTime: "10 Days", warranty: "3 Years", status: "Submitted" }],
      selectedSourcingMethod: "RFQ", attachments: ["network_diagram.pdf"]
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

  // Drag-to-reorder role nav; first item = landing screen on login (#5).
  // Role-keyed so Employee, SCM Buyer, Manager and CEO each persist their own order.
  const DEFAULT_NAV_ORDER: Record<string, string[]> = {
    Employee: ['chat', 'list', 'tracking', 'clarify'],
    Manager: ['queue', 'tracking'],
    'SCM Buyer': ['requests', 'discovery'],
    CEO: ['analytics', 'tracking'],
  };
  const [navOrder, setNavOrder] = useState<Record<string, string[]>>(() => {
    try {
      const saved = localStorage.getItem('smartspend-nav-order-v1');
      if (saved) {
        const parsed = JSON.parse(saved) as Record<string, string[]>;
        const merged: Record<string, string[]> = {};
        for (const role of Object.keys(DEFAULT_NAV_ORDER)) {
          const def = DEFAULT_NAV_ORDER[role];
          const s = parsed[role];
          merged[role] = Array.isArray(s) && s.length === def.length && def.every(v => s.includes(v)) ? s : def;
        }
        return merged;
      }
    } catch { /* ignore */ }
    return DEFAULT_NAV_ORDER;
  });
  const [dragKey, setDragKey] = useState<string | null>(null);
  useEffect(() => {
    try { localStorage.setItem('smartspend-nav-order-v1', JSON.stringify(navOrder)); } catch { /* ignore */ }
  }, [navOrder]);
  const reorderNav = (role: string, from: string, to: string) => {
    if (from === to) return;
    setNavOrder(prev => {
      const next = [...(prev[role] || [])];
      const fi = next.indexOf(from), ti = next.indexOf(to);
      if (fi < 0 || ti < 0) return prev;
      next.splice(fi, 1);
      next.splice(ti, 0, from);
      return { ...prev, [role]: next };
    });
  };
  // Navigate to a nav item's screen (shared by click + login landing).
  const applyNav = (role: string, key: string | undefined) => {
    if (!key) return;
    if (role === 'Employee') { setActiveScene(2); setEmployeeTab(key as 'chat' | 'list' | 'tracking' | 'clarify'); }
    else if (role === 'Manager') { setActiveScene(key === 'tracking' ? 11 : 10); }
    else if (role === 'SCM Buyer') { setActiveScene(6); setScmTab(key === 'discovery' ? 'discovery' : 'requests'); }
    else if (role === 'CEO') { setActiveScene(key === 'tracking' ? 11 : 15); }
  };
  const navActive = (role: string, key: string): boolean => {
    if (role === 'Employee') return activeScene === 2 && employeeTab === key;
    if (role === 'Manager') return key === 'tracking' ? activeScene === 11 : activeScene === 10;
    if (role === 'SCM Buyer') return activeScene === 6 && scmTab === (key === 'discovery' ? 'discovery' : 'requests');
    if (role === 'CEO') return key === 'tracking' ? activeScene === 11 : activeScene === 15;
    return false;
  };
  const navMeta = (role: string, key: string): { icon: React.ReactNode; label: string; badge?: React.ReactNode } => {
    const pill = (n: number, cls: string, pulse = false) => n > 0
      ? <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-bold ${cls} ${pulse ? 'animate-pulse' : ''}`}>{n}</span> : undefined;
    const m: Record<string, { icon: React.ReactNode; label: string; badge?: React.ReactNode }> = {
      'Employee/chat': { icon: <MessageSquare className="h-4 w-4" />, label: 'Conversational Agent' },
      'Employee/list': { icon: <FileText className="h-4 w-4" />, label: 'My Requests', badge: <span className="ml-auto bg-secondary text-textSecondary text-[10px] px-2 py-0.5 rounded-full font-bold">{requests.length}</span> },
      'Employee/tracking': { icon: <History className="h-4 w-4" />, label: 'Request Tracking' },
      'Employee/clarify': { icon: <AlertTriangle className="h-4 w-4" />, label: 'Clarification Inbox', badge: pill(requests.filter(r => r.status === 'Needs Clarification').length, 'bg-gold/20 text-gold border border-gold/30', true) },
      'Manager/queue': { icon: <CheckCircle2 className="h-4 w-4" />, label: 'Approval Queue', badge: pill(requests.filter(r => r.status === 'Pending Approval').length, 'bg-gold/20 text-gold border border-gold/30') },
      'Manager/tracking': { icon: <History className="h-4 w-4" />, label: 'Request Tracking' },
      'SCM Buyer/requests': { icon: <Briefcase className="h-4 w-4" />, label: 'Contract Requests', badge: pill(requests.filter(r => r.status === 'Sourcing').length, 'bg-brand/20 text-brand border border-brand/30') },
      'SCM Buyer/discovery': { icon: <Search className="h-4 w-4" />, label: 'AI Vendor Discovery' },
      'CEO/analytics': { icon: <TrendingUp className="h-4 w-4" />, label: 'Spend Analytics' },
      'CEO/tracking': { icon: <History className="h-4 w-4" />, label: 'Request Tracking' },
    };
    return m[`${role}/${key}`] ?? { icon: <FileText className="h-4 w-4" />, label: key };
  };
  const renderNavItem = (role: string, key: string, idx: number) => {
    const meta = navMeta(role, key);
    const active = navActive(role, key);
    return (
      <button
        key={key}
        draggable
        onDragStart={() => setDragKey(key)}
        onDragOver={(e) => e.preventDefault()}
        onDrop={() => { if (dragKey) reorderNav(role, dragKey, key); setDragKey(null); }}
        onDragEnd={() => setDragKey(null)}
        onClick={() => applyNav(role, key)}
        className={`group w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-grab active:cursor-grabbing ${active ? 'bg-brand text-onbrand' : 'text-textSecondary hover:bg-brand/10 hover:text-brand'} ${dragKey === key ? 'opacity-40' : ''}`}
      >
        <span className={`text-[10px] leading-none ${active ? 'text-onbrand/70' : 'text-textFaint'} opacity-60 group-hover:opacity-100`}>⠿</span>
        {meta.icon}
        <span>{meta.label}</span>
        {idx === 0 && <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded ${active ? 'bg-white/20 text-onbrand' : 'bg-brand/10 text-brand'}`}>Home</span>}
        {meta.badge}
      </button>
    );
  };
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
  const [editDepartment, setEditDepartment] = useState<string>("IT & Infrastructure");
  const [editExpenseCategory, setEditExpenseCategory] = useState<string>("IT Hardware & Laptops");
  const [editDeliveryDate, setEditDeliveryDate] = useState<string>("Jul 25, 2026");
  const [editExpenseType, setEditExpenseType] = useState<string>("Capital Expenditure (CapEx)");
  const [extraItems, setExtraItems] = useState<Array<{ productName: string; productQty: number; targetPrice: number }>>([]);

  // Poke / reminders (#10)
  const [pokes, setPokes] = useState<Array<{ to: string; from: string; message: string; reqId: string }>>([
    { to: 'Manager', from: 'Anjitha V', message: 'PR-2026-089 · Dell Latitude Laptops is awaiting your approval.', reqId: 'PR-2026-089' },
  ]);
  const [pokeToast, setPokeToast] = useState<string>('');

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

  // PO Approval & Vendor Acknowledgment States
  const [poApprovedByHead, setPoApprovedByHead] = useState<boolean>(false);
  const [poAcknowledgedByVendor, setPoAcknowledgedByVendor] = useState<boolean>(false);

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
    if (role === "Vendor") {
      setActiveScene(6); // single-function external portal
    } else {
      // Land on the role's first (drag-ordered) nav item.
      applyNav(role, (navOrder[role] || DEFAULT_NAV_ORDER[role])?.[0]);
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
  // Poke: nudge whoever owns the next action for a request.
  const pokeTargetRole = (status: string) => {
    if (status === 'Pending Approval' || status === 'Needs Clarification') return 'Manager';
    if (status === 'Sourcing' || status === 'Approved') return 'SCM Buyer';
    if (status === 'PO Confirmed') return 'Vendor';
    return 'Manager';
  };
  const handlePoke = (req: RequestItem) => {
    const to = pokeTargetRole(req.status);
    setPokes(prev => [...prev, { to, from: userRole, message: `${req.id} · ${req.productName} needs your attention.`, reqId: req.id }]);
    setPokeToast(`🔔 Reminder poked to ${to}`);
    setTimeout(() => setPokeToast(''), 2800);
  };

  const createRequisitionFromForm = () => {
    const newId = `PR-2026-0${90 + requests.length}`;
    const allItems = [{ productName: editProductName, productQty: editProductQty, targetPrice: editTargetPrice }, ...extraItems.filter(it => it.productName.trim())];
    const total = allItems.reduce((s, it) => s + it.productQty * it.targetPrice, 0);
    const newReq: RequestItem = {
      id: newId,
      productName: allItems.length > 1 ? `${editProductName} + ${allItems.length - 1} more` : editProductName,
      productQty: allItems.reduce((s, it) => s + it.productQty, 0),
      targetPrice: editTargetPrice,
      totalCost: total,
      location: editLocation,
      department: editDepartment,
      expenseCategory: editExpenseCategory,
      lineItems: allItems.length > 1 ? allItems : undefined,
      status: budgetBreach ? "Needs Clarification" : "Pending Approval",
      urgency: "High",
      deliveryDate: editDeliveryDate || undefined,
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
    setExtraItems([]);

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
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-300 relative overflow-hidden login-aurora text-textPrimary`}>
      {/* Background ambient decorative glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full ambient-glow-1 filter blur-[120px] pointer-events-none opacity-60 z-0" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full ambient-glow-2 filter blur-[120px] pointer-events-none opacity-60 z-0" />
      {/* Rotating prismatic holographic sweep (same as the login) */}
      <div className="login-sweep absolute inset-[-50%] z-0 pointer-events-none opacity-70" />

      {/* --- SCENE 1: Microsoft SSO & Role Portal Login --- */}
      {activeScene === 1 && (
        <div className="flex-grow flex flex-col lg:flex-row min-h-screen login-aurora relative overflow-hidden">
          {/* Holographic decorative layers span the whole login page */}
          <div className="login-sweep absolute inset-[-50%] z-0 pointer-events-none" />
          <div className="login-wash absolute inset-0 z-0 pointer-events-none" />
          <div className="absolute -top-24 -left-20 w-96 h-96 rounded-full bg-[#FFB6D9]/25 blur-[90px] z-0 pointer-events-none" />
          <div className="absolute top-1/3 right-1/3 w-[34rem] h-[34rem] rounded-full bg-[#8EC9FF]/18 blur-[110px] z-0 pointer-events-none" />
          <div className="absolute bottom-[-6rem] left-1/4 w-[28rem] h-[28rem] rounded-full bg-[#CDBDFF]/20 blur-[100px] z-0 pointer-events-none" />

          <div className="lg:w-7/12 flex flex-col justify-between p-8 lg:p-16 text-textPrimary relative z-10">
            <div className="relative z-10 flex items-center space-x-2">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand to-gold flex items-center justify-center shadow-lg ring-1 ring-white/25">
                <Sparkles className="h-5 w-5 text-onbrand" />
              </div>
              <span className="font-outfit text-2xl font-bold tracking-tight">SmartSpend</span>
            </div>
            
            <div className="relative z-10 my-auto py-12 max-w-xl">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-brand/10 backdrop-blur-md border border-brand/20 text-brand uppercase tracking-widest shadow-sm">
                <span className="mr-2 h-1.5 w-1.5 rounded-full bg-brand shadow-[0_0_8px_2px_rgba(124,108,246,0.45)]" />
                AI Orchestration Gateway
              </span>
              <h1 className="font-outfit text-4xl lg:text-6xl font-extrabold tracking-tight mt-6 leading-tight">
                Request Anything.<br />
                <span className="holo-text">Track Everything.</span>
              </h1>
              <p className="text-textSecondary text-lg mt-6 leading-relaxed">
                Experience corporate procurement simplified. SmartSpend abstracts complex Odoo ERP processes into a single, intelligent workspace. No forms, no jargon, no training required.
              </p>
            </div>
            
            <div className="relative z-10 flex items-center justify-between text-xs text-textFaint">
              <span>Powered by Odoo ERP Backend</span>
              <span>CONFIDENTIAL PROTOTYPE V2</span>
            </div>
          </div>
          
          <div className="lg:w-5/12 flex flex-col justify-center px-6 py-12 md:px-10 lg:px-14 relative z-10">
            <div className="max-w-md w-full mx-auto space-y-8 bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl shadow-xl p-8 lg:p-10">
              <div>
                <h2 className="font-outfit text-3xl font-extrabold text-textPrimary tracking-tight">Sign In</h2>
                <p className="mt-3 text-sm text-textSecondary">
                  Select a role portal below to test each interactive role.
                </p>
              </div>
              
              <div className="space-y-4">
                <div className="relative flex pb-2 items-center">
                  <div className="flex-grow border-t border-borderTheme"></div>
                  <span className="flex-shrink mx-4 text-textFaint text-xs font-semibold uppercase tracking-wider">Select Demo Role Portal</span>
                  <div className="flex-grow border-t border-borderTheme"></div>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => handleSsoLogin("Employee")}
                    className="p-3 bg-secondary/50 hover:bg-brand/20 border border-borderTheme hover:border-brand/30 rounded-xl text-center text-xs text-textSecondary font-medium transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-brand/10"
                  >
                    Employee Portal
                  </button>
                  <button 
                    onClick={() => handleSsoLogin("Manager")}
                    className="p-3 bg-secondary/50 hover:bg-gold/20 border border-borderTheme hover:border-gold/30 rounded-xl text-center text-xs text-textSecondary font-medium transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-brand/10"
                  >
                    Manager Inbox
                  </button>
                  <button 
                    onClick={() => handleSsoLogin("SCM Buyer")}
                    className="p-3 bg-secondary/50 hover:bg-brand/20 border border-borderTheme hover:border-brand/30 rounded-xl text-center text-xs text-textSecondary font-medium transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-brand/10"
                  >
                    SCM Buyer Portal
                  </button>
                  <button 
                    onClick={() => handleSsoLogin("Vendor")}
                    className="p-3 bg-secondary/50 hover:bg-pos/20 border border-borderTheme hover:border-pos/30 rounded-xl text-center text-xs text-textSecondary font-medium transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-brand/10"
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
        <div className="flex-grow flex overflow-hidden h-screen relative z-10">
          
          {/* LEFT SIDEBAR */}
          {sidebarOpen && (
            <aside className={`w-64 flex-shrink-0 flex flex-col justify-between border-r bg-surface border-borderTheme`}>
              <div>
                <div className="p-6 flex items-center justify-between border-b border-borderTheme/40">
                  <div className="flex items-center space-x-2">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-brand to-gold flex items-center justify-center">
                      <Sparkles className="h-4.5 w-4.5 text-onbrand" />
                    </div>
                    <span className="holo-text font-outfit font-bold text-lg tracking-tight">SmartSpend</span>
                  </div>
                </div>
                
                {/* Switch Role Quick Dropdown */}
                <div className="p-4 border-b border-borderTheme">
                  <label className="text-[10px] text-textFaint font-bold uppercase tracking-wider block mb-1.5">Switch Interactive Role</label>
                  <select 
                    value={userRole}
                    onChange={(e) => handleSsoLogin(e.target.value)}
                    className="w-full bg-secondary border border-line2/60 rounded-lg px-2.5 py-1.5 text-xs text-primary font-semibold focus:outline-none"
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
                  <span className="text-[10px] text-textFaint font-bold uppercase tracking-wider block px-3 mb-2">Portal Navigation</span>
                  
                  {/* Role-adaptive nav — drag to reorder; top item is the login landing (#5) */}
                  {userRole !== "Vendor" && (navOrder[userRole]?.length ?? 0) > 1 && (
                    <span className="text-[9px] text-textFaint px-3 flex items-center gap-1 mb-1"><Layers className="h-3 w-3" /> Drag to reorder · top tab loads first on login</span>
                  )}
                  {userRole !== "Vendor" && navOrder[userRole]?.map((key, idx) => renderNavItem(userRole, key, idx))}

                  {userRole === "Vendor" && (
                    <button
                      onClick={() => { setActiveScene(6); setScmTab('bidding'); }}
                      className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium text-pos bg-secondary border border-line2/60"
                    >
                      <FileSpreadsheet className="h-4 w-4" />
                      <span>Active RFQs to Quote</span>
                    </button>
                  )}
                </nav>
              </div>
              
              {/* Bottom Quick Controls */}
              <div className="p-4 space-y-3 border-t border-borderTheme">
                {/* Dark/light theme toggle disabled — light theme only for now.
                    Re-enable together with the darkMode state (App.tsx) above.
                <div className="flex items-center justify-between text-[11px] text-textFaint px-2">
                  <span className="font-semibold uppercase tracking-wider">Appearance</span>
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    aria-label="Toggle color theme"
                    className="relative inline-flex h-7 w-[52px] items-center rounded-full border border-borderTheme bg-secondary transition-colors"
                  >
                    <span
                      className={`absolute flex h-5 w-5 items-center justify-center rounded-full bg-brand text-onbrand shadow transition-transform duration-300 ${darkMode ? 'translate-x-[3px]' : 'translate-x-[27px]'}`}
                    >
                      {darkMode ? <Moon className="h-3 w-3" /> : <Sun className="h-3 w-3" />}
                    </span>
                  </button>
                </div>
                */}

                <button
                  onClick={() => {
                    setActiveScene(1);
                    setPoApprovedByHead(false);
                    setPoAcknowledgedByVendor(false);
                  }}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg border border-borderTheme bg-secondary hover:bg-secondary text-[11px] text-textSecondary hover:text-primary font-medium transition-all"
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
            <header className={`h-16 px-6 border-b flex items-center justify-between flex-shrink-0 bg-surface/80 backdrop-blur-md border-borderTheme`}>
              <div className="flex items-center space-x-4">
                <button 
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-lg hover:bg-secondary text-textSecondary hover:text-primary"
                >
                  <Menu className="h-5 w-5" />
                </button>
                <div className="h-4 w-[1px] bg-raised" />
                
                {/* Scene Selector */}
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-semibold text-brand">DEMO STEP:</span>
                  <select 
                    value={activeScene}
                    onChange={(e) => setActiveScene(Number(e.target.value))}
                    className="bg-secondary border border-line2 rounded-lg px-2.5 py-1 text-primary font-bold"
                  >
                    {SCENES.map(s => (
                      <option key={s.id} value={s.id}>{s.name.replace(/^Scene \d+:\s*/, '')}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <button 
                  onClick={prevScene} 
                  disabled={activeScene === 2}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-secondary hover:bg-raised text-primary disabled:opacity-30 transition-all border border-borderTheme"
                >
                  Back
                </button>
                <button 
                  onClick={nextScene}
                  disabled={activeScene === 15}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-brand hover:bg-brand text-onbrand disabled:opacity-30 transition-all flex items-center space-x-1"
                >
                  <span>Next Step</span>
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </header>
            
            {/* WORKSPACE AREA */}
            <div className="px-4 md:px-6 py-6 flex-grow">
              {/* Poke reminders targeted at the current role (#10) */}
              {pokes.some(p => p.to === userRole) && (
                <div className="mb-6 space-y-2 max-w-6xl mx-auto">
                  {pokes.map((p, i) => p.to !== userRole ? null : (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-xl border shadow-sm animate-fadeIn" style={{ background: '#7C6CF610', borderColor: '#7C6CF640' }}>
                      <span className="h-8 w-8 rounded-full bg-brand/15 flex items-center justify-center flex-shrink-0"><Bell className="h-4 w-4 text-brand" /></span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-textPrimary">Reminder from {p.from}</p>
                        <p className="text-[11px] text-textSecondary truncate">{p.message}</p>
                      </div>
                      <button onClick={() => { setSelectedRequestId(p.reqId); if (userRole === 'Manager') setActiveScene(10); else if (userRole === 'SCM Buyer') setActiveScene(6); }} className="text-[11px] font-semibold text-brand hover:underline flex-shrink-0 px-1">View</button>
                      <button onClick={() => setPokes(prev => prev.filter((_, idx) => idx !== i))} className="text-textFaint hover:text-textPrimary flex-shrink-0"><X className="h-4 w-4" /></button>
                    </div>
                  ))}
                </div>
              )}
              {pokeToast && (
                <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl bg-surface border border-brand/30 shadow-xl text-sm font-semibold text-textPrimary animate-fadeIn">
                  {pokeToast}
                </div>
              )}
              
              {/* --- SCENE 2: EMPLOYEE PORTAL (CONSOLIDATED INPUT & TABS) --- */}
              {activeScene === 2 && (
                <div className="space-y-6 animate-fadeIn">
                  
                  {/* Employee Tabs Bar */}
                  <div className="flex border-b border-borderTheme">
                    <button 
                      onClick={() => setEmployeeTab('chat')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'chat' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      Raise Request
                    </button>
                    <button 
                      onClick={() => setEmployeeTab('list')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'list' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      My Requests
                    </button>
                    <button 
                      onClick={() => setEmployeeTab('tracking')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'tracking' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      Request Tracking
                    </button>
                    <button 
                      onClick={() => setEmployeeTab('clarify')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${employeeTab === 'clarify' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      Clarification Inbox
                    </button>
                  </div>

                  {/* Tab 1: Raise Request (ChatGPT/WhatsApp Consolidated Search Style) */}
                  {employeeTab === 'chat' && (
                    <div className="max-w-6xl mx-auto space-y-12 py-10">
                      <div className="text-center space-y-3">
                        <h2 className="font-outfit text-4xl font-extrabold tracking-tight text-primary">What's on the agenda today?</h2>
                        <p className="text-sm text-textSecondary">Request any item or service. The AI orchestration layer maps the compliance rules in Odoo.</p>
                      </div>

                      {/* File Attached Success Banner */}
                      {showFileAttachedAlert && (
                        <div className="p-3 bg-brand/40 border border-brand/30 rounded-xl flex items-center justify-between text-xs text-brand animate-fadeIn">
                          <span className="flex items-center space-x-2">
                            <Paperclip className="h-4 w-4" />
                            <span><strong>1 File Attached:</strong> specification_matrix.pdf</span>
                          </span>
                          <button onClick={() => setAttachedFiles([])} className="text-textSecondary hover:text-primary">
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      )}

                      {/* Unified Input Bar (Matching user's attachment screenshot exactly) */}
                      <form onSubmit={handleChatSubmit} className="relative flex items-center bg-surface border border-borderTheme/70 rounded-full px-5 py-3.5 focus-within:border-brand/60 shadow-xl transition-all max-w-3xl mx-auto w-full">
                        {/* Attach button */}
                        <button 
                          type="button"
                          onClick={handleAttachmentAdd}
                          className="p-1.5 rounded-full hover:bg-secondary text-textSecondary hover:text-textPrimary transition-all mr-3"
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
                          className="flex-grow bg-transparent text-sm text-primary placeholder-textFaint focus:outline-none pr-28"
                        />

                        {/* Integration Logos & Voice Action Group */}
                        <div className="absolute right-3 flex items-center space-x-2">
                          <span className="text-textFaint font-bold text-lg">|</span>

                          {/* Voice Mic Icon */}
                          <button
                            type="button"
                            onClick={() => setActiveScene(3)}
                            className="p-1.5 rounded-full hover:bg-secondary text-textSecondary hover:text-primary transition-all"
                            title="Voice Procurement"
                          >
                            <Mic className="h-4.5 w-4.5" />
                          </button>

                          {/* Send Button */}
                          <button 
                            type="submit"
                            className="p-2 rounded-full bg-brand hover:bg-brand text-onbrand transition-all"
                          >
                            <Send className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </form>

                      <p className="text-[11px] text-textFaint mt-3 flex items-center gap-1.5 px-1 max-w-3xl mx-auto">
                        <HelpCircle className="h-3.5 w-3.5 flex-shrink-0" />
                        Tip: mention the <span className="text-textSecondary font-semibold">product</span>, <span className="text-textSecondary font-semibold">branch</span>, <span className="text-textSecondary font-semibold">quantity</span> and <span className="text-textSecondary font-semibold">expected delivery date</span> — the AI structures the rest.
                      </p>

                      {/* Suggested Prompts */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-6 max-w-3xl mx-auto">
                        <div 
                          onClick={() => setChatInputText("I need 20 Dell Latitude laptops for the Bangalore office")}
                          className="cursor-pointer p-4 rounded-xl bg-surface/60 border border-borderTheme hover:border-line2 transition-all text-left text-xs space-y-1"
                        >
                          <span className="font-semibold text-textPrimary block">💻 Request IT Hardware</span>
                          <span className="text-textSecondary">"I need 20 Dell Latitude laptops for the Bangalore office..."</span>
                        </div>
                        <div 
                          onClick={() => setChatInputText("Requesting 10 ergonomic conference chairs for the Mumbai office")}
                          className="cursor-pointer p-4 rounded-xl bg-surface/60 border border-borderTheme hover:border-line2 transition-all text-left text-xs space-y-1"
                        >
                          <span className="font-semibold text-textPrimary block">🪑 Request Office Furniture</span>
                          <span className="text-textSecondary">"Requesting 10 ergonomic conference chairs for Mumbai..."</span>
                        </div>
                      </div>

                      {/* My Requests + inline tracking (#2) */}
                      <div className="pt-8">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-outfit font-bold text-textPrimary">My Requests <span className="text-textFaint font-medium">({requests.length})</span></h3>
                          <button onClick={() => setEmployeeTab('list')} className="text-xs font-semibold text-brand hover:underline">View all</button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {requests.map(r => {
                            const last = r.history[r.history.length - 1];
                            const stage = statusStage(r.status);
                            return (
                              <div key={r.id} onClick={() => { setSelectedRequestId(r.id); setEmployeeTab('tracking'); }}
                                className="cursor-pointer p-4 rounded-xl bg-surface border border-borderTheme shadow-sm hover:-translate-y-0.5 transition-all" style={{ borderLeft: `3px solid ${statusColor(r.status)}` }}>
                                <div className="flex items-center justify-between">
                                  <span className="text-[11px] font-bold text-textSecondary tabular-nums">{r.id}</span>
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ color: statusColor(r.status), background: `${statusColor(r.status)}1a` }}>{STATUS_META[r.status]?.short ?? r.status}</span>
                                </div>
                                <p className="text-sm font-bold text-textPrimary mt-1.5 truncate">{r.productQty}× {r.productName}</p>
                                <p className="text-[11px] text-textFaint mt-0.5 truncate">{r.location.replace(' Office', '')} · {r.department} · <span className="font-semibold text-textSecondary">₹{r.totalCost.toLocaleString()}</span></p>
                                <div className="flex items-center gap-1 mt-3">
                                  {STAGE_LABELS.map((lab, si) => (
                                    <React.Fragment key={si}>
                                      {si > 0 && <div className="h-0.5 flex-1 rounded" style={{ background: si <= stage ? statusColor(r.status) : 'rgb(var(--border-color))' }} />}
                                      <div className="h-2 w-2 rounded-full flex-shrink-0" title={lab} style={{ background: si <= stage ? statusColor(r.status) : 'rgb(var(--border-color))' }} />
                                    </React.Fragment>
                                  ))}
                                </div>
                                <div className="flex items-center justify-between mt-2">
                                  <p className="text-[10px] text-textFaint flex items-center gap-1 min-w-0"><Clock className="h-3 w-3 flex-shrink-0" /> <span className="truncate">{last?.title}</span></p>
                                  {r.status !== 'Paid' && r.status !== 'PO Confirmed' && (
                                    <button onClick={(e) => { e.stopPropagation(); handlePoke(r); }} className="text-[10px] font-bold text-brand hover:bg-brand/10 px-2 py-0.5 rounded-md flex items-center gap-1 flex-shrink-0"><Bell className="h-3 w-3" /> Poke</button>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: My Requests List (Separated Grid) */}
                  {employeeTab === 'list' && (
                    <div className="space-y-4 animate-fadeIn">
                      <div className="flex items-center justify-between">
                        <h3 className="font-outfit font-extrabold text-xl text-primary">Your Procurement Requisitions</h3>
                        <span className="text-xs text-textFaint">Select any request to view its live tracking timeline</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {requests.map(req => (
                          <div 
                            key={req.id} 
                            onClick={() => { setSelectedRequestId(req.id); setEmployeeTab('tracking'); }}
                            className={`cursor-pointer p-5 rounded-2xl border transition-all ${selectedRequestId === req.id ? 'bg-surface/90 border-brand shadow-lg' : 'bg-surface/60 border-borderTheme hover:border-line2'}`}
                          >
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-xs font-bold text-textSecondary">{req.id}</span>
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                req.status === 'PO Confirmed' ? 'bg-pos/20 text-pos border border-pos/30' :
                                req.status === 'Approved' ? 'bg-info/20 text-info border border-info/30' :
                                req.status === 'Needs Clarification' ? 'bg-gold/20 text-gold border border-gold/30 animate-pulse' :
                                'bg-brand/20 text-brand border border-brand/30'
                              }`}>
                                {req.status}
                              </span>
                            </div>
                            
                            <h4 className="font-outfit font-extrabold text-base text-primary">{req.productQty}x {req.productName}</h4>
                            
                            <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-borderTheme/60 text-xs text-textSecondary">
                              <div>
                                <span className="block text-[10px] text-textFaint uppercase">Total budget:</span>
                                <span className="font-bold text-textPrimary">₹{req.totalCost.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="block text-[10px] text-textFaint uppercase">Location:</span>
                                <span className="font-bold text-textPrimary">{req.location}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Request Tracking (Selected Requisition Timeline) */}
                  {employeeTab === 'tracking' && (
                    <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-6 animate-fadeIn">
                      <div className="flex justify-between items-center border-b border-borderTheme pb-4">
                        <div>
                          <span className="text-xs text-brand font-bold block">{currentRequest.id} Tracking</span>
                          <h3 className="font-outfit font-extrabold text-xl text-primary">{currentRequest.productQty}x {currentRequest.productName}</h3>
                        </div>
                        <span className="px-3 py-1 bg-secondary rounded-full border border-borderTheme text-xs font-bold text-textSecondary">
                          Status: {currentRequest.status}
                        </span>
                      </div>

                      {/* Timeline Nodes */}
                      <div className="relative flex justify-between items-center max-w-2xl mx-auto py-6">
                        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-secondary z-0" />
                        
                        {/* Dynamic Progress indicator */}
                        <div 
                          className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-pos z-0 transition-all duration-500" 
                          style={{ 
                            width: currentRequest.status === 'PO Confirmed' ? '100%' :
                                   currentRequest.status === 'Approved' ? '75%' :
                                   currentRequest.status === 'Sourcing' ? '50%' : '25%' 
                          }} 
                        />

                        {/* Node 1: Request Submitted */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className="h-8 w-8 rounded-full bg-pos text-onbrand flex items-center justify-center font-bold text-xs">
                            <Check className="h-4 w-4" />
                          </div>
                          <span className="text-[10px] font-bold text-textPrimary block">Submitted</span>
                        </div>

                        {/* Node 2: Sourcing Mapped */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            ['Sourcing', 'Approved', 'PO Confirmed'].includes(currentRequest.status) ? 'bg-pos text-onbrand' : 'bg-secondary text-textFaint border border-line2'
                          }`}>
                            {['Sourcing', 'Approved', 'PO Confirmed'].includes(currentRequest.status) ? <Check className="h-4 w-4" /> : '2'}
                          </div>
                          <span className="text-[10px] font-bold text-textPrimary block">Sourcing</span>
                        </div>

                        {/* Node 3: Manager Approved */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            ['Approved', 'PO Confirmed'].includes(currentRequest.status) ? 'bg-pos text-onbrand' : 'bg-secondary text-textFaint border border-line2'
                          }`}>
                            {['Approved', 'PO Confirmed'].includes(currentRequest.status) ? <Check className="h-4 w-4" /> : '3'}
                          </div>
                          <span className="text-[10px] font-bold text-textPrimary block">Approved</span>
                        </div>

                        {/* Node 4: PO Confirmed */}
                        <div className="flex flex-col items-center z-10 text-center space-y-1.5">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            currentRequest.status === 'PO Confirmed' ? 'bg-pos text-onbrand' : 'bg-secondary text-textFaint border border-line2'
                          }`}>
                            {currentRequest.status === 'PO Confirmed' ? <Check className="h-4 w-4" /> : '4'}
                          </div>
                          <span className="text-[10px] font-bold text-textPrimary block">PO Sent</span>
                        </div>
                      </div>

                      {/* Audit Log / History */}
                      <div className="border-t border-borderTheme/80 pt-6 max-w-xl mx-auto space-y-3">
                        <span className="text-xs font-bold text-textFaint uppercase tracking-wider block">Odoo Event Log</span>
                        {currentRequest.history.map((h, idx) => (
                          <div key={idx} className="p-3 bg-secondary/45 border border-borderTheme rounded-xl flex items-start justify-between text-xs">
                            <div>
                              <span className="font-bold text-textPrimary block">{h.title}</span>
                              <span className="text-textSecondary mt-0.5 block">{h.desc}</span>
                            </div>
                            <span className="text-[10px] text-textFaint">{h.date}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 4: Clarification Inbox */}
                  {employeeTab === 'clarify' && (
                    <div className="space-y-6 animate-fadeIn">
                      <h3 className="font-outfit font-extrabold text-xl text-primary">Clarification Requests</h3>
                      
                      {requests.filter(r => r.status === 'Needs Clarification').length === 0 ? (
                        <div className="p-8 text-center bg-surface/40 border border-borderTheme rounded-2xl text-textSecondary">
                          <CheckCircle2 className="h-8 w-8 mx-auto text-pos mb-2" />
                          <p className="text-sm font-semibold">Your inbox is clear!</p>
                          <p className="text-xs mt-1">No manager queries pending clarification.</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {requests.filter(r => r.status === 'Needs Clarification').map(req => (
                            <div key={req.id} className="p-6 rounded-2xl bg-surface border border-gold/30 space-y-4">
                              <div className="flex items-center justify-between border-b border-borderTheme pb-3">
                                <div>
                                  <span className="text-xs text-gold font-bold block">{req.id}</span>
                                  <h4 className="font-outfit font-extrabold text-lg text-primary">{req.productQty}x {req.productName}</h4>
                                </div>
                                <span className="px-2 py-0.5 bg-gold/10 text-gold border border-gold/25 rounded-md text-[10px] font-bold">RFI PENDING</span>
                              </div>

                              {/* Manager Comment Display */}
                              <div className="p-4 bg-secondary border border-borderTheme rounded-xl">
                                <span className="text-[10px] text-textFaint font-bold uppercase tracking-wider block">Manager Query:</span>
                                <p className="text-xs text-textSecondary mt-1 font-medium italic">
                                  "{req.clarificationComments[req.clarificationComments.length - 1]?.text || 'Please provide details.'}"
                                </p>
                              </div>

                              {/* Reply form */}
                              <div className="space-y-2">
                                <label className="text-[10px] text-textFaint font-bold uppercase tracking-wider block">Your Response / Clarification</label>
                                <textarea 
                                  rows={3}
                                  value={employeeReplyText}
                                  onChange={(e) => setEmployeeReplyText(e.target.value)}
                                  placeholder="Provide the requested details to re-submit for approval..."
                                  className="w-full bg-secondary border border-line2/60 rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-brand"
                                />
                                <div className="flex justify-end pt-2">
                                  <button 
                                    onClick={() => handleEmployeeReplySubmit(req.id)}
                                    className="px-4 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all"
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
                  <div className="p-8 rounded-2xl border border-borderTheme bg-surface/60 backdrop-blur-xl shadow-2xl space-y-8 relative overflow-hidden">
                    <div className="absolute top-4 right-4 flex items-center space-x-2">
                      <Volume2 className="h-4 w-4 text-brand animate-bounce" />
                      <span className="text-xs text-brand font-bold uppercase tracking-wider">Voice Portal</span>
                    </div>
                    
                    <div className="text-center space-y-2">
                      <h2 className="font-outfit text-2xl font-extrabold text-primary">SmartSpend Voice Assistant</h2>
                      <p className="text-sm text-textSecondary max-w-md mx-auto font-medium">Click the microphone to simulate recording your purchase request details.</p>
                    </div>
                    
                    {/* Microphone Soundwave Visual Area */}
                    <div className="flex flex-col items-center justify-center py-6 space-y-4">
                      {voiceState === 'idle' && (
                        <button 
                          onClick={() => setVoiceState('listening')}
                          className="h-24 w-24 rounded-full bg-secondary hover:bg-brand text-textSecondary hover:text-onbrand flex items-center justify-center shadow-lg border border-line2/50 transition-all duration-300 hover:scale-105"
                        >
                          <Mic className="h-10 w-10" />
                        </button>
                      )}
                      
                      {voiceState === 'listening' && (
                        <div className="flex flex-col items-center space-y-4">
                          <button 
                            onClick={() => setVoiceState('processing')}
                            className="h-24 w-24 rounded-full bg-brand text-onbrand flex items-center justify-center relative shadow-2xl"
                          >
                            <span className="absolute inset-0 rounded-full bg-brand/40 animate-ping" />
                            <Mic className="h-10 w-10" />
                          </button>
                          
                          {/* Animated soundwaves */}
                          <div className="flex items-center space-x-1.5 h-10 py-1">
                            <div className="w-1 bg-brand rounded animate-[wave_0.8s_infinite_ease-in-out_delay-100] h-6" />
                            <div className="w-1 bg-brand rounded animate-[wave_0.8s_infinite_ease-in-out_delay-300] h-10" />
                            <div className="w-1 bg-brand rounded animate-[wave_0.8s_infinite_ease-in-out_delay-200] h-8" />
                            <div className="w-1 bg-brand rounded animate-[wave_0.8s_infinite_ease-in-out_delay-400] h-5" />
                            <div className="w-1 bg-brand rounded animate-[wave_0.8s_infinite_ease-in-out_delay-150] h-9" />
                          </div>
                          
                          <div className="text-center">
                            <span className="text-sm font-semibold text-brand">Listening...</span>
                            <span className="text-xs text-textFaint block mt-1">Simulated Duration: 0:0{voiceSeconds}</span>
                          </div>
                        </div>
                      )}
                      
                      {voiceState === 'processing' && (
                        <div className="flex flex-col items-center space-y-4">
                          <div className="h-24 w-24 rounded-full bg-brand/40 border border-brand/30 flex items-center justify-center">
                            <div className="h-8 w-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
                          </div>
                          <div className="text-center">
                            <span className="text-sm font-semibold text-brand">Transcribing Speech to Text...</span>
                            <span className="text-xs text-textFaint block mt-1 text-textSecondary">Analyzing Intent &amp; Catalog entities</span>
                          </div>
                        </div>
                      )}
                      
                      {voiceState === 'done' && (
                        <div className="w-full space-y-4">
                          <div className="p-4 bg-secondary/40 border border-line2/60 rounded-xl">
                            <p className="text-xs text-textFaint font-bold uppercase tracking-wider">Converted Text:</p>
                            <p className="text-sm text-textPrimary mt-2 font-medium italic">"{speechText}"</p>
                          </div>
                          
                          <div className="flex justify-center space-x-3">
                            <button 
                              onClick={() => { setVoiceState('idle'); setVoiceSeconds(0); setSpeechText(""); }}
                              className="px-4 py-2 border border-line2 hover:bg-secondary text-xs font-semibold rounded-lg text-textSecondary transition-all"
                            >
                              Record Again
                            </button>
                            <button 
                              onClick={() => {
                                parseSpeechText(speechText);
                                setActiveScene(4);
                              }}
                              className="px-5 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1"
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
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-primary">AI Parsed Requisition Form</h2>
                      <p className="text-xs text-textSecondary">Review and edit the parameters extracted from your conversational request.</p>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-brand/15 text-brand border border-brand/25 flex items-center space-x-1">
                      <ShieldCheck className="h-3 w-3" />
                      <span>98% Parse Confidence</span>
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Left Form: Editable details */}
                    <div className="md:col-span-2 p-6 rounded-2xl bg-surface border border-borderTheme space-y-4">
                      <div className="flex items-center justify-between border-b border-borderTheme pb-2">
                        <h3 className="font-outfit text-base font-bold text-textPrimary">Extracted Parameters</h3>
                        <span className="text-[11px] text-textFaint">{1 + extraItems.length} line item{extraItems.length ? 's' : ''}</span>
                      </div>

                      {/* Products — multi-line (#9) */}
                      <div className="space-y-2">
                        <div className="grid grid-cols-12 gap-2 text-[10px] text-textFaint font-bold uppercase tracking-wider">
                          <span className="col-span-6">Product</span><span className="col-span-2">Qty</span><span className="col-span-3">Unit ₹</span><span className="col-span-1" />
                        </div>
                        <div className="grid grid-cols-12 gap-2 items-center">
                          <input type="text" value={editProductName} onChange={(e) => setEditProductName(e.target.value)} placeholder="Product description"
                            className="col-span-6 bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                          <input type="number" value={editProductQty} onChange={(e) => setEditProductQty(Number(e.target.value))}
                            className="col-span-2 bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                          <input type="number" value={editTargetPrice} onChange={(e) => setEditTargetPrice(Number(e.target.value))}
                            className="col-span-3 bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                          <span className="col-span-1 text-center text-brand" title="Primary item">★</span>
                        </div>
                        {extraItems.map((it, idx) => (
                          <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                            <input type="text" value={it.productName} onChange={(e) => setExtraItems(prev => prev.map((x, i) => i === idx ? { ...x, productName: e.target.value } : x))} placeholder="Product description"
                              className="col-span-6 bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                            <input type="number" value={it.productQty} onChange={(e) => setExtraItems(prev => prev.map((x, i) => i === idx ? { ...x, productQty: Number(e.target.value) } : x))}
                              className="col-span-2 bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                            <input type="number" value={it.targetPrice} onChange={(e) => setExtraItems(prev => prev.map((x, i) => i === idx ? { ...x, targetPrice: Number(e.target.value) } : x))}
                              className="col-span-3 bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                            <button onClick={() => setExtraItems(prev => prev.filter((_, i) => i !== idx))} className="col-span-1 flex justify-center text-neg" title="Remove line"><X className="h-4 w-4" /></button>
                          </div>
                        ))}
                        <button onClick={() => setExtraItems(prev => [...prev, { productName: '', productQty: 1, targetPrice: 0 }])}
                          className="text-xs font-semibold text-brand hover:underline flex items-center gap-1"><span className="text-base leading-none">+</span> Add another product</button>
                      </div>

                      {/* Editable meta fields (#3, #8) */}
                      <div className="grid grid-cols-2 gap-4 pt-2">
                        <div>
                          <label className="text-xs text-textFaint font-bold uppercase tracking-wider block mb-1">Branch</label>
                          <select value={editLocation} onChange={(e) => setEditLocation(e.target.value)} className="w-full bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand">
                            {['Bangalore Office', 'Kochi Head Office', 'Mumbai Office', 'Delhi Office', 'Chennai Office', 'Hyderabad Office'].map(o => <option key={o} value={o}>{o}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-textFaint font-bold uppercase tracking-wider block mb-1">Department</label>
                          <select value={editDepartment} onChange={(e) => setEditDepartment(e.target.value)} className="w-full bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand">
                            {['IT & Infrastructure', 'Operations', 'Facilities', 'Marketing', 'Finance', 'R&D'].map(o => <option key={o} value={o}>{o}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-textFaint font-bold uppercase tracking-wider block mb-1">Category</label>
                          <input type="text" value={editExpenseCategory} onChange={(e) => setEditExpenseCategory(e.target.value)} className="w-full bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                        </div>
                        <div>
                          <label className="text-xs text-textFaint font-bold uppercase tracking-wider block mb-1">Expected Delivery Date</label>
                          <input type="text" value={editDeliveryDate} onChange={(e) => setEditDeliveryDate(e.target.value)} placeholder="e.g. Jul 25, 2026" className="w-full bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand" />
                        </div>
                        <div>
                          <label className="text-xs text-textFaint font-bold uppercase tracking-wider block mb-1">Expense Type</label>
                          <select value={editExpenseType} onChange={(e) => setEditExpenseType(e.target.value)} className="w-full bg-secondary border border-line2 rounded-lg p-2 text-sm text-primary focus:outline-none focus:border-brand">
                            <option>Capital Expenditure (CapEx)</option>
                            <option>Operating Expenditure (OpEx)</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-textFaint font-bold uppercase tracking-wider block mb-1">Estimated Total</label>
                          <span className="w-full bg-secondary/50 border border-borderTheme rounded-lg p-2 text-sm text-brand block font-bold">₹{[{ productQty: editProductQty, targetPrice: editTargetPrice }, ...extraItems].reduce((s, it) => s + it.productQty * it.targetPrice, 0).toLocaleString()}</span>
                        </div>
                      </div>

                      <div className="pt-4 flex justify-end space-x-3">
                        <button onClick={() => setActiveScene(2)} className="px-4 py-2 text-xs text-textSecondary hover:text-primary transition-all font-semibold">Cancel</button>
                        <button onClick={createRequisitionFromForm} className="px-5 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all">Submit for Validation</button>
                      </div>
                    </div>
                    
                    {/* Right Card: Address Resolution Mappings */}
                    <div className="space-y-4">
                      <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-4">
                        <h3 className="font-outfit text-base font-bold text-textPrimary border-b border-borderTheme pb-2">Branch Mapped Addresses</h3>
                        
                        <div className="space-y-3">
                          <div>
                            <span className="text-[10px] text-textFaint font-bold uppercase tracking-wider block mb-0.5">Input location:</span>
                            <span className="text-xs font-semibold text-textSecondary">"{editLocation}"</span>
                          </div>
                          
                          <div className="pt-2 border-t border-borderTheme">
                            <span className="text-[10px] text-brand font-bold uppercase tracking-wider block">Resolved Bill-To Address</span>
                            <span className="text-xs text-textSecondary font-medium block mt-1 font-semibold">Kuttukaran Corporate HQ, Metro Pillar 32, Kochi, KL - 682025</span>
                            <span className="text-[9px] text-textFaint block mt-0.5">GSTIN: 32AAAAB1234C1Z0</span>
                          </div>
                          
                          <div className="pt-2 border-t border-borderTheme">
                            <span className="text-[10px] text-brand font-bold uppercase tracking-wider block">Resolved Ship-To Address</span>
                            <span className="text-xs text-textSecondary font-medium block mt-1 font-semibold">Kuttukaran Regional Warehouse, IT Park, Bangalore, KA - 560066</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 9: BUDGET VALIDATION --- */}
              {activeScene === 9 && (
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-primary">Smart Budget Verification &amp; Allocation</h2>
                      <p className="text-xs text-textSecondary">The platform cross-references available cost center funds in real-time after contract pricing is resolved.</p>
                    </div>
                    
                    <div className="flex items-center space-x-3 bg-secondary px-3 py-1.5 rounded-lg border border-line2 text-xs">
                      <span className="font-semibold text-textSecondary">Simulate Budget Status:</span>
                      <button 
                        onClick={() => { setBudgetBreach(false); setBudgetAction("default"); }}
                        className={`px-2 py-1 rounded font-bold ${!budgetBreach ? 'bg-brand text-onbrand' : 'bg-raised text-textSecondary'}`}
                      >
                        Within Limit
                      </button>
                      <button 
                        onClick={() => { setBudgetBreach(true); }}
                        className={`px-2 py-1 rounded font-bold ${budgetBreach ? 'bg-neg text-onbrand' : 'bg-raised text-textSecondary'}`}
                      >
                        Limit Exceeded
                      </button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-surface border border-borderTheme space-y-6">
                      <h3 className="font-outfit text-base font-bold text-textPrimary border-b border-borderTheme pb-2">{currentRequest.expenseCategory} Budget Allocation</h3>
                      
                      <div className="space-y-4">
                        <div className="flex justify-between text-xs text-textSecondary">
                          <span>Total Allocated Q3 Budget:</span>
                          <span className="font-bold text-textPrimary">₹30,00,000</span>
                        </div>
                        <div className="flex justify-between text-xs text-textSecondary">
                          <span>Committed Spend:</span>
                          <span className="font-bold text-textPrimary">₹12,00,000</span>
                        </div>
                        <div className="flex justify-between text-xs text-textSecondary">
                          <span>Current Request ({currentRequest.productQty} units @ ₹{currentRequest.targetPrice.toLocaleString()}):</span>
                          <span className="font-bold text-brand">₹{(currentRequest.productQty * currentRequest.targetPrice).toLocaleString()}</span>
                        </div>
                        
                        <div className="relative pt-2">
                          <div className="h-4 w-full bg-secondary rounded-full overflow-hidden flex">
                            <div className="h-full bg-raised" style={{ width: '40%' }} />
                            <div className={`h-full ${budgetBreach ? 'bg-neg' : 'bg-brand'}`} style={{ width: budgetBreach ? '70%' : '20%' }} />
                          </div>
                        </div>
                      </div>
                      
                      {!budgetBreach ? (
                        <div className="p-4 bg-pos/20 border border-pos/40 rounded-xl flex items-start space-x-3 text-pos text-xs">
                          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0 text-pos" />
                          <div>
                            <p className="font-bold">Budget Verification Passed</p>
                            <p className="mt-1 text-textSecondary">Funds are available. Mapped to Cost Center. No pre-approvals required for budget allocation.</p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 bg-neg/20 border border-neg/40 rounded-xl flex items-start space-x-3 text-neg text-xs">
                          <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0 text-neg animate-pulse" />
                          <div>
                            <p className="font-bold">Budget Limit Exceeded by ₹{(currentRequest.productQty * currentRequest.targetPrice + 1200000 - 3000000).toLocaleString()}</p>
                            <p className="mt-1 text-textSecondary">This requisition exceeds the remaining allocated budget threshold.</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="pt-2 flex justify-end space-x-3">
                        <button onClick={() => setActiveScene(4)} className="px-4 py-2 text-xs text-textSecondary font-semibold hover:text-primary">Modify Request</button>
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
                          }} className="px-5 py-2 bg-pos hover:bg-pos text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1">
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
                          }} className="px-5 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1">
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
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-primary">Active Contract Search</h2>
                      <p className="text-xs text-textSecondary">AI queries the Odoo registry for valid Rate Contracts or pricing agreements.</p>
                    </div>
                    
                    <div className="flex items-center space-x-3 bg-secondary px-3 py-1.5 rounded-lg border border-line2 text-xs">
                      <span className="font-semibold text-textSecondary">Active Contract exists?</span>
                      <button 
                        onClick={() => setHasContract(true)}
                        className={`px-2.5 py-1 rounded font-bold ${hasContract ? 'bg-brand text-onbrand' : 'bg-raised text-textSecondary'}`}
                      >
                        Yes
                      </button>
                      <button 
                        onClick={() => setHasContract(false)}
                        className={`px-2.5 py-1 rounded font-bold ${!hasContract ? 'bg-gold text-onbrand' : 'bg-raised text-textSecondary'}`}
                      >
                        No
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-6">
                    {hasContract ? (
                      <div className="space-y-6 animate-fadeIn">
                        <div className="p-5 bg-pos/20 border border-pos/40 rounded-2xl flex items-start space-x-4">
                          <div className="h-12 w-12 rounded-xl bg-pos/10 flex items-center justify-center border border-pos/25 text-pos">
                            <ShieldCheck className="h-6 w-6" />
                          </div>
                          <div className="space-y-1">
                            <h3 className="font-outfit font-extrabold text-lg text-pos">Active Rate Contract Mapped</h3>
                            <p className="text-sm text-textSecondary">
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
                          }} className="px-5 py-2.5 bg-pos hover:bg-pos text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1">
                            <span>Proceed to Budget Verification</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-6 animate-fadeIn">
                        <div className="p-5 bg-gold/25 border border-gold/45 rounded-2xl flex items-start space-x-4">
                          <div className="h-12 w-12 rounded-xl bg-gold/10 flex items-center justify-center border border-gold/25 text-gold">
                            <AlertCircle className="h-6 w-6" />
                          </div>
                          <div className="space-y-1">
                            <h3 className="font-outfit font-extrabold text-lg text-gold">No Active Contract Found</h3>
                            <p className="text-sm text-textSecondary">The product category does not have a pre-negotiated volume contract. Sourcing is required.</p>
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
                          }} className="px-5 py-2.5 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1">
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
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  
                  {/* SCM Sourcing Tab Selector */}
                  <div className="flex border-b border-borderTheme">
                    <button 
                      onClick={() => setScmTab('requests')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${scmTab === 'requests' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      Active Contract Requests (CR)
                    </button>
                    <button 
                      onClick={() => setScmTab('bidding')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${scmTab === 'bidding' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      Bidding &amp; Live RFQs
                    </button>
                    <button 
                      onClick={() => setScmTab('discovery')} 
                      className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${scmTab === 'discovery' ? 'border-brand text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary'}`}
                    >
                      AI Vendor Sourcing Discovery
                    </button>
                  </div>

                  {/* SCM Tab 1: Contract Requests Queue */}
                  {scmTab === 'requests' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-outfit font-extrabold text-xl text-primary">Pending Sourcing Workload</h3>
                          <p className="text-xs text-textSecondary">Requisitions flagged by Odoo requiring vendor quotation sourcing.</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 gap-4">
                        {requests.filter(r => r.status === 'Sourcing').map(req => (
                          <div key={req.id} className="p-6 rounded-2xl bg-surface border border-borderTheme flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs font-bold text-textFaint">{req.id}</span>
                                <span className="text-xs px-2.5 py-0.5 rounded bg-brand/20 text-brand border border-brand/20 font-bold uppercase">SOURCING FALLBACK</span>
                              </div>
                              <h4 className="font-outfit font-extrabold text-lg text-primary">{req.productQty}x {req.productName}</h4>
                              <p className="text-xs text-textSecondary">Estimated Value: <strong>{req.totalCost > 0 ? `₹${req.totalCost.toLocaleString()}` : "TBD (Pending Sourcing Bids)"}</strong> | Mapped to: {req.expenseCategory}</p>
                            </div>

                            <div className="flex items-center space-x-3">
                              {/* Sourcing strategies selection */}
                              <select 
                                value={req.selectedSourcingMethod}
                                onChange={(e) => {
                                  const method = e.target.value as 'Direct' | 'RFQ' | 'Auction';
                                  setRequests(prev => prev.map(r => r.id === req.id ? { ...r, selectedSourcingMethod: method } : r));
                                }}
                                className="bg-secondary border border-line2/80 rounded-lg p-2 text-xs text-primary focus:outline-none"
                              >
                                <option value="RFQ">Invite Preferred (Multi-RFQ)</option>
                                <option value="Direct">Direct Price Negotiator</option>
                                <option value="Auction">Live Reverse Auction</option>
                              </select>

                              <button 
                                onClick={() => { setSelectedRequestId(req.id); setScmTab('bidding'); }}
                                className="px-4 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all"
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
                      <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-borderTheme pb-4">
                          <div>
                            <span className="text-xs text-brand font-bold block">{currentRequest.id} Bidding Management</span>
                            <h3 className="font-outfit font-extrabold text-xl text-primary">{currentRequest.productQty}x {currentRequest.productName}</h3>
                          </div>

                          <div className="mt-2 sm:mt-0 flex items-center space-x-2">
                            <span className="px-2.5 py-1 bg-brand/20 text-brand border border-brand/25 rounded-md text-xs font-bold">
                              Sourcing: {currentRequest.selectedSourcingMethod} Mode
                            </span>
                          </div>
                        </div>

                        {/* Bid submissions table */}
                        <div className="space-y-3">
                          <h4 className="text-xs text-textFaint font-bold uppercase tracking-wider">Active Vendor Bids (Received in real-time)</h4>
                          
                          {currentRequest.vendorBids.length === 0 ? (
                            <div className="p-6 text-center bg-secondary/40 border border-borderTheme rounded-xl text-textSecondary text-xs">
                              No bids received yet. Invite vendors or click "Trigger Bidding" below to populate quotes.
                            </div>
                          ) : (
                            <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse text-xs">
                                <thead>
                                  <tr className="border-b border-borderTheme text-textFaint font-bold">
                                    <th className="py-2.5">Supplier Name</th>
                                    <th className="py-2.5">Quote Price</th>
                                    <th className="py-2.5">Warranty SLA</th>
                                    <th className="py-2.5">Lead Time</th>
                                    <th className="py-2.5">Odoo Onboard Status</th>
                                  </tr>
                                </thead>
                                <tbody className="text-textSecondary">
                                  {currentRequest.vendorBids.map((bid, idx) => (
                                    <tr key={idx} className="border-b border-borderTheme">
                                      <td className="py-3 font-semibold">{bid.vendorName}</td>
                                      <td className="py-3 font-bold text-primary">₹{bid.price.toLocaleString()}</td>
                                      <td className="py-3 text-textSecondary">{bid.warranty}</td>
                                      <td className="py-3 text-textSecondary">{bid.leadTime}</td>
                                      <td className="py-3">
                                        <span className="px-2 py-0.5 rounded bg-pos/15 text-pos font-bold text-[9px] uppercase border border-pos/20">
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
                        <div className="flex justify-between items-center pt-4 border-t border-borderTheme">
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
                            className="px-4 py-2 bg-secondary hover:bg-raised text-xs font-semibold rounded-lg text-textPrimary transition-all border border-borderTheme"
                          >
                            Simulate Vendor Bid Submission
                          </button>

                          <div className="flex space-x-3">
                            <button 
                              onClick={() => setActiveScene(7)} 
                              className="px-4 py-2 border border-line2 hover:bg-secondary text-xs font-semibold rounded-lg text-textSecondary"
                            >
                              Open Scorecard Matrix
                            </button>
                            <button 
                              onClick={() => {
                                resetNegotiation();
                                setActiveScene(8);
                              }} 
                              className="px-5 py-2.5 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand"
                            >
                              Launch AI Negotiation
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Mock Vendor Submission Form panel (To show how vendors interact) */}
                      <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-4">
                        <div className="flex items-center space-x-2 text-brand">
                          <Landmark className="h-4.5 w-4.5" />
                          <h4 className="font-outfit font-extrabold text-base text-primary">Vendor Portal Simulation Workspace</h4>
                        </div>
                        <p className="text-xs text-textSecondary">This simulates the external vendor's secure magic link. Entering details submits them to Odoo.</p>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs pt-2">
                          <div>
                            <label className="text-textFaint block mb-1">Quote price per unit (₹):</label>
                            <input 
                              type="number"
                              value={vendorBidPrice}
                              onChange={(e) => setVendorBidPrice(e.target.value)}
                              className="w-full bg-secondary border border-line2 rounded-lg p-2 text-primary"
                            />
                          </div>
                          <div>
                            <label className="text-textFaint block mb-1">Delivery Lead Time:</label>
                            <input 
                              type="text"
                              value={vendorLeadTime}
                              onChange={(e) => setVendorLeadTime(e.target.value)}
                              className="w-full bg-secondary border border-line2 rounded-lg p-2 text-primary"
                            />
                          </div>
                          <div className="flex items-end">
                            <button 
                              onClick={handleVendorBidSubmit}
                              className="w-full py-2 bg-pos hover:bg-pos text-xs font-bold rounded-lg text-onbrand transition-all"
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
                      <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-4">
                        <h3 className="font-outfit font-extrabold text-lg text-primary">AI Sourcing Directory Discovery</h3>
                        <p className="text-xs text-textSecondary">Search external B2B registries to resolve suppliers for non-catalog categories.</p>

                        <form onSubmit={handleSearchVendors} className="flex gap-2 max-w-lg">
                          <input 
                            type="text" 
                            value={searchVendorQuery}
                            onChange={(e) => setSearchVendorQuery(e.target.value)}
                            placeholder="Type product categories (e.g. Server components, desks)..."
                            className="flex-grow bg-secondary border border-line2 rounded-lg px-3 py-2 text-xs text-primary focus:outline-none"
                          />
                          <button type="submit" className="px-4 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand">
                            Search registries
                          </button>
                        </form>
                      </div>

                      {/* Onboard Success Notification banner */}
                      {showDraftOnboardSuccess && (
                        <div className="p-4 bg-pos/20 border border-pos/40 rounded-xl flex items-start space-x-3 text-pos text-xs animate-fadeIn">
                          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="font-bold">Odoo Draft Partner Auto-Created!</p>
                            <p className="mt-1 text-textSecondary">
                              Successfully registered <strong>{lastOnboardedVendor}</strong> as a draft partner in Odoo (Record ID: `res.partner.draft_092`). Magic link sent for onboard completion.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* SCM Discovery search result lists */}
                      {searchingVendors ? (
                        <div className="p-8 text-center text-xs text-textSecondary">Searching B2B databases...</div>
                      ) : discoveredVendors.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {discoveredVendors.map((vendor, idx) => (
                            <div key={idx} className="p-5 rounded-2xl bg-surface border border-borderTheme flex flex-col justify-between h-56">
                              <div>
                                <span className="px-2 py-0.5 bg-secondary border border-line2/60 rounded text-[9px] font-bold text-textSecondary uppercase">
                                  External Discovery Match
                                </span>
                                <h4 className="font-outfit font-extrabold text-lg text-primary mt-2">{vendor.name}</h4>
                                <p className="text-xs text-textSecondary mt-1">{vendor.category}</p>

                                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-borderTheme text-xs text-textSecondary">
                                  <span>Trust score: <strong>{vendor.rating}/100</strong></span>
                                  <span>AI Index: <strong>{vendor.score}%</strong></span>
                                </div>
                              </div>

                              <div className="flex justify-between items-center pt-2">
                                <span className="text-[10px] text-textFaint">Not in local Odoo Partner DB</span>
                                <button 
                                  onClick={() => handleAutoOnboard(vendor.name)}
                                  className="px-3.5 py-1.5 bg-pos hover:bg-pos text-xs font-bold rounded-lg text-onbrand"
                                >
                                  Auto-Create Draft Vendor
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-8 text-center bg-surface/40 border border-borderTheme rounded-xl text-textSecondary text-xs">
                          Search above to simulate sourcing new suppliers from B2B catalogs.
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )}
              
              {/* --- SCENE 7: RFQ COMPARISON MATRIX --- */}
              {activeScene === 7 && (
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-primary">Side-by-Side RFQ Comparison</h2>
                      <p className="text-xs text-textSecondary">Value scorecard compiled from active vendor bids in local Odoo database.</p>
                    </div>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-surface border border-borderTheme overflow-hidden">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-borderTheme text-xs text-textSecondary uppercase font-bold tracking-wider">
                          <th className="py-3 px-4">Evaluation Criteria</th>
                          <th className="py-3 px-4 bg-brand/20 text-brand">Primus Technologies</th>
                          <th className="py-3 px-4">Apex Systems</th>
                        </tr>
                      </thead>
                      <tbody className="text-xs text-textSecondary">
                        <tr className="border-b border-borderTheme/50">
                          <td className="py-3 px-4 font-semibold">Unit Quote Price</td>
                          <td className="py-3 px-4 bg-brand/15 font-bold text-primary">₹{getNegotiationBaselinePrice(currentRequest.productName).toLocaleString()}</td>
                          <td className="py-3 px-4">₹{(getNegotiationBaselinePrice(currentRequest.productName) + 3000).toLocaleString()}</td>
                        </tr>
                        <tr className="border-b border-borderTheme/50">
                          <td className="py-3 px-4 font-semibold">Warranty Terms</td>
                          <td className="py-3 px-4 bg-brand/15">3 Years On-Site Support</td>
                          <td className="py-3 px-4">1 Year Carry-In Warranty</td>
                        </tr>
                        <tr className="border-b border-borderTheme/50">
                          <td className="py-3 px-4 font-semibold">Delivery Timeframe</td>
                          <td className="py-3 px-4 bg-brand/15 font-bold text-pos">5 Business Days</td>
                          <td className="py-3 px-4">10 Business Days</td>
                        </tr>
                        <tr className="border-b border-borderTheme/50">
                          <td className="py-3 px-4 font-semibold">Payment Milestones</td>
                          <td className="py-3 px-4 bg-brand/15">Net-30 Audited Terms</td>
                          <td className="py-3 px-4">Net-15 Invoice Terms</td>
                        </tr>
                        <tr className="border-b border-borderTheme/50">
                          <td className="py-3 px-4 font-semibold">Risk &amp; Health Score</td>
                          <td className="py-3 px-4 bg-brand/15">Low Risk (Score: 96)</td>
                          <td className="py-3 px-4 text-gold font-medium">Medium Risk (Score: 88)</td>
                        </tr>
                        <tr>
                          <td className="py-3 px-4 font-semibold">AI Recommendation</td>
                          <td className="py-3 px-4 bg-brand/20">
                            <span className="px-2 py-0.5 rounded bg-pos/20 text-pos font-bold text-[10px]">RECOMMENDED FIT</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-textFaint font-medium">Not Recommended</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    
                    <div className="pt-6 flex justify-end space-x-3">
                      <button onClick={() => { setUserRole("SCM Buyer"); setScmTab('bidding'); setActiveScene(6); }} className="px-4 py-2 text-xs text-textSecondary font-semibold hover:text-primary">Back to Sourcing</button>
                      <button onClick={() => setActiveScene(8)} className="px-5 py-2.5 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1">
                        <span>Trigger AI Negotiation</span>
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {/* --- SCENE 8: AI NEGOTIATION LOUNGE --- */}
              {activeScene === 8 && (
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-primary">AI Autonomous Negotiation</h2>
                      <p className="text-xs text-textSecondary">Watch the AI agent negotiate rates and terms directly with the supplier bot.</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="px-3 py-1 bg-brand/15 text-brand border border-brand/25 rounded-full text-xs font-bold">
                        Savings: ₹{((getNegotiationBaselinePrice(currentRequest.productName) - currentOfferPrice) * currentRequest.productQty).toLocaleString()} (₹{(getNegotiationBaselinePrice(currentRequest.productName) - currentOfferPrice).toLocaleString()}/unit)
                      </span>
                      <button 
                        onClick={resetNegotiation}
                        className="p-2 rounded-lg bg-secondary hover:bg-raised text-textSecondary"
                        title="Restart Negotiation"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 flex flex-col h-[400px] rounded-2xl bg-surface border border-borderTheme overflow-hidden">
                      <div className="p-4 bg-secondary border-b border-borderTheme flex items-center justify-between">
                        <span className="text-xs text-textPrimary font-bold uppercase tracking-wider">Live Agent Log</span>
                        <span className="h-2 w-2 rounded-full bg-pos animate-ping" />
                      </div>
                      
                      <div className="flex-grow p-4 overflow-y-auto space-y-4">
                        {chatLog.length === 0 ? (
                          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                            <div className="h-12 w-12 rounded-full bg-brand/10 flex items-center justify-center text-brand border border-brand/20">
                              <Sparkles className="h-6 w-6" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-textSecondary">Negotiation Lounge Ready</p>
                              <p className="text-xs text-textFaint mt-1">Click the button below to simulate the AI autonomous pricing discussion.</p>
                            </div>
                          </div>
                        ) : (
                          chatLog.map((m, idx) => (
                            <div key={idx} className={`flex ${m.sender === 'ai' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                              <div className={`max-w-md p-3.5 rounded-2xl text-xs space-y-1 ${m.sender === 'ai' ? 'bg-brand text-onbrand rounded-tr-none' : 'bg-secondary text-textPrimary rounded-tl-none border border-line2/60'}`}>
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
                      
                      <div className="p-3 bg-secondary/60 border-t border-borderTheme flex justify-between items-center">
                        <span className="text-[10px] text-textFaint">Autonomous API negotiation active</span>
                        {!negotiationComplete ? (
                          <button 
                            onClick={triggerNextNegotiationStep}
                            className="px-4 py-2 bg-brand hover:bg-brand text-xs font-bold rounded-lg text-onbrand transition-all flex items-center space-x-1"
                          >
                            <span>{negotiationStep === 0 ? 'Start Agent Session' : 'Continue Negotiation'}</span>
                            <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        ) : (
                          <span className="text-xs text-pos font-bold flex items-center space-x-1 animate-fadeIn">
                            <CheckCircle2 className="h-4 w-4" />
                            <span>Agreement Locked &amp; Confirmed</span>
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="p-5 rounded-2xl bg-surface border border-borderTheme space-y-4">
                        <h3 className="font-outfit text-base font-bold text-textPrimary border-b border-borderTheme pb-2">Deal Tracker</h3>
                        
                        <div className="space-y-3 text-xs">
                          <div className="flex justify-between">
                            <span className="text-textFaint">Original Bid:</span>
                            <span className="font-semibold text-textSecondary">₹{getNegotiationBaselinePrice(currentRequest.productName).toLocaleString()} / unit</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textFaint">Negotiated Rate:</span>
                            <span className="font-bold text-pos">₹{currentOfferPrice.toLocaleString()} / unit</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textFaint">Savings ({currentRequest.productQty} units):</span>
                            <span className="font-bold text-pos">₹{((getNegotiationBaselinePrice(currentRequest.productName) - currentOfferPrice) * currentRequest.productQty).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                      
                      {negotiationComplete && (
                        <button 
                          onClick={() => {
                            setRequests(prev => prev.map(r => r.id === selectedRequestId ? { ...r, targetPrice: currentOfferPrice, totalCost: currentOfferPrice * r.productQty, vendor: "Primus Technologies" } : r));
                            setActiveScene(9);
                          }}
                          className="w-full py-3 bg-brand hover:bg-brand text-xs font-bold rounded-xl text-onbrand transition-all shadow-lg flex items-center justify-center space-x-2"
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
                <div className="max-w-6xl mx-auto py-8 animate-fadeIn">
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-textPrimary">Unified Approval Panel</h2>
                      <p className="text-xs text-textSecondary">Simplifying decision metrics for managers. No complex ERP menus.</p>
                    </div>
                    <span className="px-3 py-1 bg-accent-approvals/10 text-accent-approvals border border-accent-approvals/20 rounded-full text-xs font-bold font-outfit">
                      Pending Approvals: {requests.filter(r => r.status === 'Pending Approval').length}
                    </span>
                  </div>

                  {/* Status-wise approval counts (#7) */}
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-5">
                    {(['Pending Approval', 'Approved', 'Sourcing', 'PO Confirmed', 'Needs Clarification', 'Rejected']).map(st => {
                      const n = requests.filter(r => r.status === st).length;
                      const c = statusColor(st);
                      return (
                        <div key={st} className="p-3 rounded-xl bg-surface border border-borderTheme shadow-sm" style={{ borderTop: `3px solid ${c}` }}>
                          <p className="text-2xl font-extrabold text-textPrimary font-outfit leading-none">{n}</p>
                          <p className="text-[10px] font-bold uppercase tracking-wider mt-1.5" style={{ color: c }}>{STATUS_META[st].short}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Consolidated snapshot (#4) */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <span className="text-[11px] text-textFaint font-bold uppercase tracking-wider">Awaiting your approval</span>
                      <p className="text-2xl font-extrabold text-textPrimary mt-1 font-outfit">₹{requests.filter(r => r.status === 'Pending Approval').reduce((s, r) => s + r.totalCost, 0).toLocaleString()}</p>
                      <p className="text-[11px] text-accent-savings mt-0.5">₹{requests.filter(r => r.status === 'Pending Approval').reduce((s, r) => s + r.savings, 0).toLocaleString()} AI savings on the table</p>
                    </div>
                    <div className="md:col-span-2 p-5 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <span className="text-[11px] text-textFaint font-bold uppercase tracking-wider">Live request value by department (₹K)</span>
                      <div className="mt-3">
                        {(() => {
                          const agg = requests.reduce((a, r) => { a[r.department] = (a[r.department] || 0) + r.totalCost; return a; }, {} as Record<string, number>);
                          const data = Object.entries(agg).map(([label, value]) => ({ label, value: Math.round(value / 1000) }));
                          return <BarList data={data} color="#7C6CF6" prefix="₹" suffix="K" />;
                        })()}
                      </div>
                    </div>
                  </div>
                  
                  {requests.filter(r => r.status === 'Pending Approval').length === 0 ? (
                    <div className="p-8 text-center bg-surface border border-borderTheme rounded-2xl text-textSecondary shadow-sm">
                      <CheckCircle2 className="h-8 w-8 mx-auto text-accent-savings mb-2" />
                      <p className="text-sm font-bold text-textPrimary font-outfit">All caught up!</p>
                      <p className="text-xs mt-1 text-textSecondary">No requisitions currently require your approval.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {requests.filter(r => r.status === 'Pending Approval').map(req => (
                        <div key={req.id} className="p-6 rounded-2xl bg-surface border border-borderTheme shadow-sm space-y-6">
                          <div className="flex items-center justify-between border-b border-borderTheme pb-4">
                            <div className="flex items-center space-x-3">
                              <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center text-textSecondary font-bold text-sm">AV</div>
                              <div>
                                <p className="text-xs text-textSecondary font-semibold uppercase">Requisition Initiator:</p>
                                <p className="text-sm font-bold text-textPrimary">Anjitha V (IT Ops Specialist)</p>
                              </div>
                            </div>
                            <span className="text-xs text-textSecondary font-bold">{req.id}</span>
                          </div>
                          
                          <div className="space-y-4">
                            <h3 className="font-outfit font-extrabold text-textPrimary text-lg">{req.productQty}x {req.productName}</h3>
                            
                            <div className="grid grid-cols-2 gap-4 text-xs font-outfit">
                              <div>
                                <span className="text-textSecondary block">Total cost:</span>
                                <span className="font-bold text-textPrimary">₹{req.totalCost.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="text-accent-savings block">Negotiated Savings:</span>
                                <span className="font-bold text-accent-savings">₹{req.savings.toLocaleString()} Saved</span>
                              </div>
                              <div>
                                <span className="text-textSecondary block">Budget Mapped:</span>
                                <span className="font-bold text-textPrimary">{req.expenseCategory}</span>
                              </div>
                              <div>
                                <span className="text-textSecondary block">Vendor Assigned:</span>
                                <span className="font-bold text-textPrimary">{req.vendor}</span>
                              </div>
                              <div>
                                <span className="text-textSecondary block">Branch · Department:</span>
                                <span className="font-bold text-textPrimary">{req.location} · {req.department}</span>
                              </div>
                              <div>
                                <span className="text-textSecondary block">Expected Delivery:</span>
                                <span className="font-bold text-textPrimary">{req.deliveryDate || '—'}</span>
                              </div>
                            </div>

                            {/* Attachments viewer (#11) */}
                            {req.attachments.length > 0 && (
                              <details className="text-xs">
                                <summary className="cursor-pointer list-none flex items-center gap-1.5 text-textSecondary hover:text-brand font-semibold w-fit">
                                  <Paperclip className="h-3.5 w-3.5" /> {req.attachments.length} attachment{req.attachments.length > 1 ? 's' : ''}
                                  <ChevronRight className="h-3.5 w-3.5" />
                                </summary>
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {req.attachments.map((f, ai) => (
                                    <a key={ai} href="#" onClick={(e) => e.preventDefault()} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-secondary border border-borderTheme text-[11px] text-textPrimary hover:border-brand transition-all">
                                      <FileText className="h-3.5 w-3.5 text-brand" /> {f}
                                    </a>
                                  ))}
                                </div>
                              </details>
                            )}

                            {/* Manager clarification comments history */}
                            {req.clarificationComments.length > 0 && (
                              <div className="p-4 bg-secondary rounded-xl space-y-2 border border-borderTheme text-xs">
                                <span className="font-bold text-textSecondary block border-b border-borderTheme pb-1">Clarification Thread</span>
                                {req.clarificationComments.map((c, cidx) => (
                                  <p key={cidx} className="mt-1 text-[11px] leading-relaxed">
                                    <strong className={c.role === 'manager' ? 'text-accent-approvals' : 'text-accent-budget'}>
                                      {c.role === 'manager' ? 'Manager: ' : 'Anjitha: '}
                                    </strong>
                                    <span className="text-textPrimary">"{c.text}"</span>
                                  </p>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Action Buttons group (Approve, Reject, Request Info) */}
                          <div className="flex flex-wrap justify-end gap-2 border-t border-borderTheme pt-4">
                            <button 
                              onClick={() => {
                                setRequests(prev => prev.map(r => r.id === req.id ? { ...r, status: "Rejected", history: [...r.history, { title: "Rejected", date: "Now", desc: "Rejected by Manager" }] } : r));
                              }}
                              className="px-4 py-2 border border-borderTheme hover:bg-accent-alerts/10 hover:border-accent-alerts text-xs font-semibold rounded-lg text-textSecondary hover:text-accent-alerts transition-all"
                            >
                              Reject
                            </button>
                            
                            {/* Request Info button triggers dialog */}
                            <button 
                              onClick={() => {
                                setSelectedRequestId(req.id);
                                setShowManagerQueryBox(true);
                              }}
                              className="px-4 py-2 border border-borderTheme hover:bg-accent-approvals/10 hover:border-accent-approvals text-xs font-semibold rounded-lg text-textSecondary hover:text-accent-approvals transition-all"
                            >
                              Request Info
                            </button>

                            <button 
                              onClick={() => handleManagerApprove(req.id)}
                              className="px-5 py-2.5 bg-accent-savings hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
                            >
                              <Check className="h-4.5 w-4.5" />
                              <span>Approve Request</span>
                            </button>
                          </div>

                          {/* Request Info Dialogue Card */}
                          {showManagerQueryBox && selectedRequestId === req.id && (
                            <div className="p-4 bg-secondary rounded-xl border border-accent-approvals/20 space-y-3 text-xs animate-fadeIn">
                              <label className="font-bold text-textPrimary block">Ask Initiator for clarification:</label>
                              <input 
                                type="text"
                                value={managerQueryText}
                                onChange={(e) => setManagerQueryText(e.target.value)}
                                placeholder="e.g. Please clarify unit requirements and pricing details..."
                                className="w-full bg-surface border border-borderTheme rounded-lg p-2.5 text-textPrimary focus:outline-none focus:border-textPrimary"
                              />
                              <div className="flex justify-end space-x-2">
                                <button onClick={() => setShowManagerQueryBox(false)} className="px-3 py-1.5 text-textSecondary hover:text-textPrimary transition-all">Cancel</button>
                                <button 
                                  onClick={() => handleRequestInfoSubmit(req.id)} 
                                  className="px-4 py-1.5 bg-accent-approvals hover:opacity-90 text-surface font-bold rounded transition-all shadow-sm"
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
                  {/* All requests — dense tile grid (#1) */}
                  <div className="mt-8">
                    <h3 className="font-outfit font-bold text-textPrimary mb-3">All Requests <span className="text-textFaint font-medium">({requests.length})</span></h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {requests.map(r => (
                        <div key={r.id} className="p-3.5 rounded-xl bg-surface border border-borderTheme shadow-sm" style={{ borderLeft: `3px solid ${statusColor(r.status)}` }}>
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-textSecondary tabular-nums">{r.id}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ color: statusColor(r.status), background: `${statusColor(r.status)}1a` }}>{STATUS_META[r.status]?.short ?? r.status}</span>
                          </div>
                          <p className="text-sm font-bold text-textPrimary mt-1.5 truncate">{r.productQty}× {r.productName}</p>
                          <div className="flex items-center justify-between mt-2 text-[11px]">
                            <span className="text-textFaint truncate pr-2">{r.location.replace(' Office', '').replace(' Head', '')} · {r.department.split(' ')[0]}</span>
                            <span className="font-bold text-textPrimary tabular-nums">₹{r.totalCost.toLocaleString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* --- SCENE 11: REQUEST TRACKING TIMELINE --- */}
              {activeScene === 11 && (
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-textPrimary">Request Tracking Milestone</h2>
                      <p className="text-xs text-textSecondary">Amazon-style simple progress tracker hiding deep transactional ERP states.</p>
                    </div>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-8 shadow-sm">
                    {/* 5-Step Progress Tracker */}
                    <div className="relative flex justify-between items-center max-w-3xl mx-auto py-4">
                      <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-borderTheme z-0" />
                      <div 
                        className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-accent-savings z-0 transition-all duration-500" 
                        style={{ width: poApprovedByHead ? (poAcknowledgedByVendor ? '100%' : '75%') : '50%' }} 
                      />
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-accent-savings text-surface flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-textPrimary font-outfit">Submitted</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-accent-savings text-surface flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-textPrimary font-outfit">Sourcing</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className="h-8 w-8 rounded-full bg-accent-savings text-surface flex items-center justify-center font-bold text-xs">
                          <Check className="h-4 w-4" />
                        </div>
                        <span className="text-[10px] font-bold text-textPrimary font-outfit">PR Approved</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-300 ${poApprovedByHead ? 'bg-accent-savings text-surface' : 'bg-surface border border-borderTheme text-textSecondary'}`}>
                          {poApprovedByHead ? <Check className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                        </div>
                        <span className="text-[10px] font-bold text-textPrimary font-outfit">PO Approved</span>
                      </div>
                      
                      <div className="flex flex-col items-center z-10 text-center space-y-2">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-300 ${poAcknowledgedByVendor ? 'bg-accent-savings text-surface' : 'bg-surface border border-borderTheme text-textSecondary'}`}>
                          {poAcknowledgedByVendor ? <Check className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                        </div>
                        <span className="text-[10px] font-bold text-textPrimary font-outfit">Acknowledged</span>
                      </div>
                    </div>

                    {/* Interactive workflow cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-borderTheme font-outfit">
                      {/* Left: PO Details card */}
                      <div className="p-5 bg-secondary rounded-xl border border-borderTheme space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-accent-budget uppercase tracking-wider">Purchase Order Status</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            poAcknowledgedByVendor
                              ? 'bg-accent-savings/15 text-accent-savings border-accent-savings/20'
                              : poApprovedByHead
                              ? 'bg-accent-budget/15 text-accent-budget border-accent-budget/20'
                              : 'bg-accent-approvals/15 text-accent-approvals border-accent-approvals/20'
                          }`}>
                            {poAcknowledgedByVendor
                              ? 'PO Confirmed (Acknowledged)'
                              : poApprovedByHead
                              ? 'Pending Vendor Ack'
                              : 'Pending Purchase Head Approval'}
                          </span>
                        </div>

                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-textSecondary">PO Reference:</span>
                            <span className="font-semibold text-textPrimary font-mono">PO-2026-003</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Vendor:</span>
                            <span className="font-semibold text-textPrimary">{currentRequest.vendor || "Apex Systems"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Total value:</span>
                            <span className="font-bold text-textPrimary">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Items:</span>
                            <span className="font-semibold text-textPrimary">{currentRequest.productQty}x {currentRequest.productName}</span>
                          </div>
                        </div>
                      </div>

                      {/* Right: Operational Actions card */}
                      <div className="p-5 bg-secondary rounded-xl border border-borderTheme space-y-4">
                        <span className="text-xs font-bold text-textSecondary uppercase tracking-wider block">ERP Action Control Room</span>
                        
                        <div className="space-y-4">
                          {/* Step 1: Head Approval */}
                          <div className="flex items-start space-x-3 text-xs">
                            <div className={`mt-0.5 p-1 rounded-full ${poApprovedByHead ? 'bg-accent-savings/10 text-accent-savings' : 'bg-accent-approvals/10 text-accent-approvals'}`}>
                              <CheckCircle2 className="h-4.5 w-4.5" />
                            </div>
                            <div className="flex-grow space-y-1">
                              <p className="font-bold text-textPrimary">1. Purchase Head / User Approval</p>
                              <p className="text-[11px] text-textSecondary leading-relaxed">Required to approve standard financial release terms before sending the PO document to the vendor.</p>
                              {!poApprovedByHead ? (
                                <button 
                                  onClick={() => {
                                    setPoApprovedByHead(true);
                                    setRequests(prev => prev.map(r => r.id === selectedRequestId ? {
                                      ...r,
                                      history: [...r.history, { title: "Approved by Purchase Head", date: "Now", desc: "PO-2026-003 approved and released to vendor." }]
                                    } : r));
                                  }}
                                  className="mt-2 px-3 py-1.5 bg-accent-budget hover:opacity-90 text-[10px] font-bold text-surface rounded shadow-sm transition-all"
                                >
                                  Approve &amp; Release PO
                                </button>
                              ) : (
                                <p className="text-[10px] text-accent-savings font-semibold mt-1">✓ Approved and released to vendor</p>
                              )}
                            </div>
                          </div>

                          {/* Step 2: Vendor Acknowledgment */}
                          <div className="flex items-start space-x-3 text-xs border-t border-borderTheme/50 pt-3">
                            <div className={`mt-0.5 p-1 rounded-full ${poAcknowledgedByVendor ? 'bg-accent-savings/10 text-accent-savings' : 'bg-textSecondary/10 text-textSecondary'}`}>
                              <CheckCircle2 className="h-4.5 w-4.5" />
                            </div>
                            <div className="flex-grow space-y-1">
                              <p className="font-bold text-textPrimary">2. Vendor Acknowledgment</p>
                              <p className="text-[11px] text-textSecondary leading-relaxed">Simulate receipt confirmation, delivery date commit, and agreement signature from the vendor portal.</p>
                              {poApprovedByHead && !poAcknowledgedByVendor && (
                                <button 
                                  onClick={() => {
                                    setPoAcknowledgedByVendor(true);
                                    setRequests(prev => prev.map(r => r.id === selectedRequestId ? {
                                      ...r,
                                      history: [...r.history, { title: "Vendor Acknowledged PO", date: "Now", desc: "Vendor confirmed delivery commit date & pricing." }]
                                    } : r));
                                  }}
                                  className="mt-2 px-3 py-1.5 bg-accent-savings hover:opacity-90 text-[10px] font-bold text-surface rounded shadow-sm transition-all"
                                >
                                  Simulate Vendor Acknowledgment
                                </button>
                              )}
                              {poAcknowledgedByVendor && (
                                <p className="text-[10px] text-accent-savings font-semibold mt-1">✓ Vendor Acknowledged (PO Confirmed)</p>
                              )}
                              {!poApprovedByHead && (
                                <p className="text-[10px] text-textSecondary/60 font-semibold mt-1 italic">Locked: Awaiting Purchase Head approval</p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Proceed Button */}
                    <div className="flex justify-between items-center pt-4 border-t border-borderTheme font-outfit">
                      <span className="text-xs text-textSecondary">
                        {!poApprovedByHead && "Awaiting Purchase Head approval..."}
                        {poApprovedByHead && !poAcknowledgedByVendor && "Awaiting Vendor acknowledgment..."}
                        {poApprovedByHead && poAcknowledgedByVendor && "Workflow steps complete."}
                      </span>
                      <button 
                        onClick={() => {
                          if (poApprovedByHead && poAcknowledgedByVendor) {
                            setActiveScene(12);
                          }
                        }}
                        disabled={!(poApprovedByHead && poAcknowledgedByVendor)}
                        className={`px-5 py-2.5 text-xs font-bold rounded-lg transition-all flex items-center space-x-1 shadow-sm ${
                          (poApprovedByHead && poAcknowledgedByVendor)
                            ? 'bg-textPrimary hover:opacity-90 text-surface cursor-pointer'
                            : 'bg-secondary text-textSecondary/50 border border-borderTheme cursor-not-allowed'
                        }`}
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
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-textPrimary">Product Receiving &amp; Goods Receipt Note</h2>
                      <p className="text-xs text-textSecondary">Simulate warehouse operations. Inspect the delivered items and generate the GRN in Odoo.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-surface border border-borderTheme space-y-6 shadow-sm">
                      <div className="flex items-center space-x-3 text-accent-budget">
                        <Truck className="h-5 w-5" />
                        <h3 className="font-outfit text-lg font-bold text-textPrimary">Goods Receipt Portal</h3>
                      </div>

                      <div className="space-y-4 font-outfit">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block mb-1">Source PO</span>
                            <span className="text-sm font-semibold text-textPrimary bg-secondary border border-borderTheme rounded-lg p-2 block">PO-2026-003</span>
                          </div>
                          <div>
                            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block mb-1">Vendor</span>
                            <span className="text-sm font-semibold text-textPrimary bg-secondary border border-borderTheme rounded-lg p-2 block">{currentRequest.vendor || "Primus Technologies"}</span>
                          </div>
                        </div>

                        <div>
                          <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block mb-1">Product Details</span>
                          <span className="text-sm font-semibold text-textPrimary bg-secondary border border-borderTheme rounded-lg p-2 block">{currentRequest.productName}</span>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block mb-1">Ordered Qty</span>
                            <span className="text-sm font-semibold text-textPrimary bg-secondary border border-borderTheme rounded-lg p-2 block">{currentRequest.productQty} units</span>
                          </div>
                          <div>
                            <label className="text-xs text-accent-budget font-bold uppercase tracking-wider block mb-1">Delivered Qty</label>
                            <input 
                              type="number" 
                              value={deliveredQty} 
                              onChange={(e) => setDeliveredQty(Number(e.target.value))}
                              className="w-full bg-secondary border border-accent-budget/50 rounded-lg p-2 text-sm text-textPrimary focus:outline-none focus:border-textPrimary font-semibold"
                            />
                          </div>
                        </div>

                        <div className="pt-2">
                          <label className="flex items-center space-x-2.5 cursor-pointer select-none">
                            <input 
                              type="checkbox" 
                              checked={qualityPassed}
                              onChange={(e) => setQualityPassed(e.target.checked)}
                              className="rounded border-borderTheme text-accent-savings focus:ring-accent-savings h-4.5 w-4.5 bg-secondary"
                            />
                            <span className="text-sm text-textSecondary font-medium">Quality Inspection Approved: Items match specs with no defects</span>
                          </label>
                        </div>
                      </div>

                      {grnGenerated ? (
                        <div className="p-4 bg-accent-savings/10 border border-accent-savings/20 rounded-xl space-y-3 animate-fadeIn shadow-sm">
                          <div className="flex items-start space-x-3 text-accent-savings text-xs">
                            <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="font-bold text-textPrimary">Goods Receipt Note (GRN-2026-089) Generated</p>
                              <p className="mt-1 text-textSecondary">Successfully posted to Odoo. Stock levels updated at Bangalore Warehouse. Handing off to Accounts Payable.</p>
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
                              className="px-5 py-2 bg-textPrimary hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
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
                            className="px-5 py-2.5 bg-accent-savings hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
                          >
                            <span>Validate &amp; Generate GRN</span>
                            <Check className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme space-y-4 h-fit shadow-sm">
                      <div className="flex items-center space-x-2 text-accent-budget">
                        <Package className="h-4.5 w-4.5" />
                        <h4 className="font-outfit font-extrabold text-sm text-textPrimary">Odoo Warehouse Status</h4>
                      </div>
                      <div className="space-y-3 text-xs font-outfit">
                        <div className="flex justify-between">
                          <span className="text-textSecondary">Destination:</span>
                          <span className="font-semibold text-textPrimary">Bangalore Warehouse</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-textSecondary">Carrier:</span>
                          <span className="font-semibold text-textPrimary">Blue Dart Express</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-textSecondary">Waybill Ref:</span>
                          <span className="font-mono text-accent-budget">AWB-77291024</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* --- SCENE 13: VENDOR BILL 3-WAY MATCHING --- */}
              {activeScene === 13 && (
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-textPrimary">Automated 3-Way Match Verification</h2>
                      <p className="text-xs text-textSecondary">Audit and reconcile PO details, Goods Receipt note, and Vendor Invoice side-by-side.</p>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-surface border border-borderTheme space-y-6 shadow-sm">
                    <div className="flex items-center space-x-3 text-accent-budget">
                      <ShieldCheck className="h-5.5 w-5.5" />
                      <h3 className="font-outfit text-lg font-bold text-textPrimary">Reconciliation Matrix</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-outfit">
                      {/* Column 1: PO */}
                      <div className="p-4 rounded-xl bg-secondary border border-borderTheme/70 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-accent-budget uppercase">1. Purchase Order</span>
                          <span className="px-2 py-0.5 rounded bg-accent-savings/10 text-accent-savings font-bold text-[9px] border border-accent-savings/20">PO-2026-003</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Qty Ordered:</span>
                            <span className="font-semibold text-textPrimary">{currentRequest.productQty} units</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Rate:</span>
                            <span className="font-semibold text-textPrimary">₹{currentRequest.targetPrice.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-borderTheme">
                            <span className="text-textSecondary">Total amount:</span>
                            <span className="font-bold text-textPrimary">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Column 2: GRN */}
                      <div className="p-4 rounded-xl bg-secondary border border-borderTheme/70 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-accent-budget uppercase">2. Goods Receipt</span>
                          <span className="px-2 py-0.5 rounded bg-accent-savings/10 text-accent-savings font-bold text-[9px] border border-accent-savings/20">GRN-2026-089</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Qty Received:</span>
                            <span className="font-semibold text-textPrimary">{deliveredQty} units</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Quality Check:</span>
                            <span className="font-bold text-accent-savings">PASSED</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-borderTheme">
                            <span className="text-textSecondary">Stock Status:</span>
                            <span className="font-bold text-accent-savings">Posted</span>
                          </div>
                        </div>
                      </div>

                      {/* Column 3: Invoice */}
                      <div className="p-4 rounded-xl bg-secondary border border-borderTheme/70 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-accent-budget uppercase">3. Vendor Invoice</span>
                          <span className="px-2 py-0.5 rounded bg-accent-approvals/10 text-accent-approvals font-bold text-[9px] border border-accent-approvals/20">BILL-2026-045</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Qty Billed:</span>
                            <span className="font-semibold text-textPrimary">{currentRequest.productQty} units</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-textSecondary">Rate Billed:</span>
                            <span className="font-semibold text-textPrimary">₹{currentRequest.targetPrice.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-borderTheme">
                            <span className="text-textSecondary">Total Billed:</span>
                            <span className="font-bold text-textPrimary">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="p-5 bg-accent-savings/10 border border-accent-savings/20 rounded-xl flex items-start space-x-3 text-accent-savings text-xs shadow-sm">
                      <CheckCircle2 className="h-5.5 w-5.5 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold text-sm text-textPrimary font-outfit">3-Way Match Verification Success</p>
                        <p className="mt-1 text-textSecondary text-xs leading-relaxed">All comparison checks pass. PO quantities, GRN warehouse receipts, and the PDF extracted vendor invoice details match 100%. Ready for general ledger posting.</p>
                      </div>
                    </div>

                    {billPosted ? (
                      <div className="p-4 bg-secondary border border-borderTheme rounded-xl flex justify-between items-center animate-fadeIn text-xs shadow-sm">
                        <span className="text-textSecondary">Vendor Bill successfully posted to accounts payable.</span>
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
                          className="px-5 py-2 bg-textPrimary hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
                        >
                          <span>Proceed to Payment Execution</span>
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex justify-end pt-2">
                        <button 
                          onClick={() => setBillPosted(true)}
                          className="px-5 py-2.5 bg-accent-savings hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
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
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-textPrimary">Payment Disbursement &amp; Reconciliation</h2>
                      <p className="text-xs text-textSecondary">Authorize the cash disbursement and auto-reconcile bank statements in Odoo.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 p-6 rounded-2xl bg-surface border border-borderTheme space-y-6 shadow-sm">
                      <div className="flex items-center space-x-3 text-accent-budget">
                        <CreditCard className="h-5 w-5" />
                        <h3 className="font-outfit text-lg font-bold text-textPrimary">Disbursement Voucher</h3>
                      </div>

                      <div className="space-y-4 text-xs font-outfit">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-textSecondary font-bold uppercase tracking-wider block mb-1">Beneficiary Vendor</span>
                            <span className="text-sm font-semibold text-textPrimary block bg-secondary p-2.5 rounded-lg border border-borderTheme">{currentRequest.vendor || "Primus Technologies"}</span>
                          </div>
                          <div>
                            <span className="text-textSecondary font-bold uppercase tracking-wider block mb-1">Invoice Reference</span>
                            <span className="text-sm font-semibold text-textPrimary block bg-secondary p-2.5 rounded-lg border border-borderTheme font-mono">BILL-2026-045</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-textSecondary font-bold uppercase tracking-wider block mb-1">Paying Bank A/c</span>
                            <span className="text-sm font-semibold text-textPrimary block bg-secondary p-2.5 rounded-lg border border-borderTheme">HDFC Corporate A/c (*9824)</span>
                          </div>
                          <div>
                            <span className="text-textSecondary font-bold uppercase tracking-wider block mb-1">Settlement Amount</span>
                            <span className="text-sm font-extrabold text-accent-budget block bg-secondary p-2.5 rounded-lg border border-borderTheme">₹{currentRequest.totalCost.toLocaleString()}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-accent-budget font-bold uppercase tracking-wider block mb-1">Payment Method</label>
                            <select 
                              value={paymentMethod}
                              onChange={(e) => setPaymentMethod(e.target.value)}
                              className="w-full bg-secondary border border-borderTheme rounded-lg p-2.5 text-textPrimary focus:outline-none focus:border-textPrimary font-semibold"
                            >
                              <option value="Bank Transfer" className="bg-surface text-textPrimary">Bank Transfer (NEFT/RTGS)</option>
                              <option value="Corporate Card" className="bg-surface text-textPrimary">Corporate Card</option>
                              <option value="UPI Pay" className="bg-surface text-textPrimary">UPI Corporate Pay</option>
                            </select>
                          </div>
                          <div>
                            <span className="text-textSecondary font-bold uppercase tracking-wider block mb-1">Value Date</span>
                            <span className="text-sm font-semibold text-textPrimary block bg-secondary p-2.5 rounded-lg border border-borderTheme">July 13, 2026</span>
                          </div>
                        </div>
                      </div>

                      {paymentComplete ? (
                        <div className="p-4 bg-accent-savings/10 border border-accent-savings/20 rounded-xl space-y-3 animate-fadeIn shadow-sm">
                          <div className="flex items-start space-x-3 text-accent-savings text-xs">
                            <CheckCircle2 className="h-5.5 w-5.5 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="font-bold text-textPrimary font-outfit">Payment Completed &amp; Reconciled</p>
                              <p className="mt-1 text-textSecondary leading-relaxed">Transaction posted successfully. Odoo auto-reconciliation engine verified the bank statement entry against HDFC corporate accounts. Invoice status: PAID.</p>
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
                              className="px-5 py-2 bg-textPrimary hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
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
                            className="px-5 py-2.5 bg-accent-savings hover:opacity-90 text-xs font-bold rounded-lg text-surface transition-all flex items-center space-x-1 shadow-sm"
                          >
                            <span>Authorize &amp; Pay Invoice</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme space-y-4 h-fit text-xs shadow-sm">
                      <div className="flex items-center space-x-2 text-accent-budget mb-2">
                        <Landmark className="h-4.5 w-4.5" />
                        <h4 className="font-outfit font-extrabold text-sm text-textPrimary">Bank Statement Audit</h4>
                      </div>
                      <div className="space-y-3 font-outfit">
                        <div className="p-3 bg-secondary rounded-lg border border-borderTheme flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-textPrimary">HDFC Bank Ledger</p>
                            <p className="text-[10px] text-textSecondary font-mono">STMT-99281-2026</p>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-accent-savings/10 text-accent-savings font-bold text-[9px] border border-accent-savings/20">Matched</span>
                        </div>
                        <p className="text-textSecondary leading-relaxed text-[11px]">AI matches banking feeds with internal ledgers in real-time, removing manual end-of-month reconciliation tasks.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* --- SCENE 15: spend INTELLIGENCE ANALYTICS --- */}
              {activeScene === 15 && (
                <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-outfit text-2xl font-extrabold text-textPrimary">Spend Intelligence Dashboard</h2>
                      <p className="text-xs text-textSecondary">High-level capital monitoring and automated fraud detection audits.</p>
                    </div>
                  </div>
                  
                  {/* KPI row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-outfit">
                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <div className="flex items-center gap-2 text-brand mb-2"><Landmark className="h-4 w-4" /><span className="text-[11px] font-bold uppercase tracking-wider">Total Audited</span></div>
                      <p className="text-2xl font-extrabold text-textPrimary">₹4.58 Cr</p>
                      <p className="text-[11px] text-textFaint mt-0.5">FY 2026 · 5 branches</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <div className="flex items-center gap-2 text-pos mb-2"><TrendingUp className="h-4 w-4" /><span className="text-[11px] font-bold uppercase tracking-wider">AI Savings</span></div>
                      <p className="text-2xl font-extrabold text-pos">₹28.45 L</p>
                      <p className="text-[11px] text-textFaint mt-0.5">6.2% of total spend</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <div className="flex items-center gap-2 text-info mb-2"><Layers className="h-4 w-4" /><span className="text-[11px] font-bold uppercase tracking-wider">Active Requests</span></div>
                      <p className="text-2xl font-extrabold text-textPrimary">{requests.length}</p>
                      <p className="text-[11px] text-textFaint mt-0.5">{requests.filter(r => r.status === 'Pending Approval').length} awaiting approval</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <div className="flex items-center gap-2 text-neg mb-2"><ShieldAlert className="h-4 w-4" /><span className="text-[11px] font-bold uppercase tracking-wider">Blocked Anomalies</span></div>
                      <p className="text-2xl font-extrabold text-neg">4</p>
                      <p className="text-[11px] text-textFaint mt-0.5">fraud audits this quarter</p>
                    </div>
                  </div>

                  {/* Analytics charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="p-6 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <h3 className="font-outfit font-bold text-textPrimary">Spend by Branch</h3>
                      <p className="text-[11px] text-textFaint mb-4">Where capital is deployed (₹ Crore)</p>
                      <DonutChart data={spendAnalytics.byBranch} prefix="₹" />
                    </div>
                    <div className="p-6 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <h3 className="font-outfit font-bold text-textPrimary">Spend by Department</h3>
                      <p className="text-[11px] text-textFaint mb-4">Cost-center concentration (₹ Crore)</p>
                      <BarList data={spendAnalytics.byDepartment} color="#7C6CF6" prefix="₹" />
                    </div>
                    <div className="p-6 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <h3 className="font-outfit font-bold text-textPrimary">Spend by Category</h3>
                      <p className="text-[11px] text-textFaint mb-4">Procurement categories (₹ Crore)</p>
                      <BarList data={spendAnalytics.byCategory} color="#0E8F6A" prefix="₹" />
                    </div>
                    <div className="p-6 rounded-2xl bg-surface border border-borderTheme shadow-sm">
                      <h3 className="font-outfit font-bold text-textPrimary">Monthly Spend Trend</h3>
                      <p className="text-[11px] text-textFaint mb-4">Rolling 6 months (₹ Crore)</p>
                      <div className="flex items-end gap-2 h-36">
                        {spendAnalytics.byMonth.map((m, i) => (
                          <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                            <span className="text-[10px] font-bold text-textSecondary tabular-nums mb-1">₹{m.value}</span>
                            <div className="w-full rounded-t-lg transition-all duration-700" style={{ height: `${(m.value / Math.max(...spendAnalytics.byMonth.map(x => x.value))) * 74}%`, background: 'linear-gradient(180deg,#8D7DFF,#C9B8FF)' }} />
                            <span className="text-[10px] text-textFaint mt-1.5">{m.label}</span>
                          </div>
                        ))}
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
