"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import EmbeddedMap from "./map/EmbeddedMapLoader";
import { Incident } from "./Sidebar";
import type { PoliceOfficer } from "./map/EmbeddedMap";
import { fetchRouteToIncident } from "./map/EmbeddedMap";

interface DetailPageProps {
	incident: Incident;
	onBack: () => void;
}

type PanelContent = "feed" | "suggestions" | "summary" | "map" | "actions";
type LeftPanelView = "suggestions" | "summary";

type FeedItemType = "alert" | "status" | "media" | "personnel";

interface FeedItem {
	id: string;
	type: FeedItemType;
	time: string;
	title: string;
	summary: string;
	details?: string;
	mediaUrl?: string;
	mediaType?: "image" | "video";
}

interface Call {
	id: string;
	name: string;
	role: string;
	duration: string;
	isMuted: boolean;
	isActive: boolean;
}

const DetailPage: React.FC<DetailPageProps> = ({ incident, onBack }) => {
	const [centerPanel, setCenterPanel] = useState<PanelContent>("feed");
	const [rightTopPanel, setRightTopPanel] = useState<PanelContent>("map");
	const [rightBottomPanel, setRightBottomPanel] =
		useState<PanelContent>("actions");
	const [leftPanelView, setLeftPanelView] =
		useState<LeftPanelView>("suggestions");
	const [isSwapping, setIsSwapping] = useState(false);
	const [expandedFeedItems, setExpandedFeedItems] = useState<Set<string>>(
		new Set()
	);
	const chatMessagesEndRef = useRef<HTMLDivElement>(null);
	const [hoveredOfficerId, setHoveredOfficerId] = useState<string | null>(
		null
	);
	const [dispatchPanelExpanded, setDispatchPanelExpanded] = useState(false);
	const [selectedOfficer, setSelectedOfficer] =
		useState<PoliceOfficer | null>(null);
	const [routeInfo, setRouteInfo] = useState<{
		distance: number;
		duration: number;
	} | null>(null);

	// Example incident location - Bobby Dodd Stadium for demonstration
	// In production, this would come from the incident data
	const incidentLocation: [number, number] = [-84.3933, 33.7726];

	// Example police officers near the incident
	// Positioned on roads around the area, not at the incident location
	const [policeOfficers, setPoliceOfficers] = useState<PoliceOfficer[]>([
		{
			id: "officer-1",
			name: "Officer Martinez",
			role: "Patrol Unit",
			location: [-84.395, 33.774], // Northwest on Techwood Drive
			heading: 45,
			speed: 1.5,
			badge: "B-2847",
			unit: "Unit 12",
			rank: "Officer",
			yearsOfService: 4,
			dispatched: false,
		},
		{
			id: "officer-2",
			name: "Sergeant Williams",
			role: "Supervisor",
			location: [-84.391, 33.771], // Southeast on North Avenue
			heading: 180,
			speed: 1.0,
			badge: "B-1523",
			unit: "Unit 7",
			rank: "Sergeant",
			yearsOfService: 12,
			dispatched: false,
		},
		{
			id: "officer-3",
			name: "Officer Chen",
			role: "K-9 Unit",
			location: [-84.39, 33.774], // Northeast on Spring Street
			heading: 270,
			speed: 2.0,
			badge: "B-3091",
			unit: "K-9 Unit 3",
			rank: "Officer",
			yearsOfService: 7,
			dispatched: false,
		},
		{
			id: "officer-4",
			name: "Officer Davis",
			role: "Traffic Control",
			location: [-84.396, 33.771], // Southwest on Ferst Drive
			heading: 90,
			speed: 0.5,
			badge: "B-2156",
			unit: "Unit 19",
			rank: "Officer",
			yearsOfService: 2,
			dispatched: false,
		},
	]);

	const [calls, setCalls] = useState<Call[]>([
		{
			id: "call-1",
			name: "Paramedic Johnson",
			role: "Field Responder",
			duration: "04:23",
			isMuted: false,
			isActive: true,
		},
		{
			id: "call-2",
			name: "Dispatcher Chen",
			role: "Emergency Dispatch",
			duration: "08:15",
			isMuted: true,
			isActive: true,
		},
		{
			id: "call-3",
			name: "Dr. Martinez",
			role: "Medical Advisor",
			duration: "02:47",
			isMuted: false,
			isActive: true,
		},
	]);
	const [selectedCalls, setSelectedCalls] = useState<Set<string>>(new Set());
	const [showNewCallDialog, setShowNewCallDialog] = useState(false);
	const [expandedCalls, setExpandedCalls] = useState<Set<string>>(new Set());
	const [selectedSuggestion, setSelectedSuggestion] = useState<{
		id: string;
		title: string;
		action: string;
		details: string;
		context: string;
		source: string;
		priority: "high" | "medium" | "low";
	} | null>(null);
	const [chatMessage, setChatMessage] = useState("");
	const [chatMessages, setChatMessages] = useState<
		{
			id: string;
			sender: string;
			message: string;
			time: string;
			isUser: boolean;
		}[]
	>([
		{
			id: "msg-1",
			sender: "Dispatcher Chen",
			message:
				"Units responding to Bobby Dodd Stadium. Multiple reports of disturbance.",
			time: "14:23",
			isUser: false,
		},
		{
			id: "msg-2",
			sender: "You",
			message: "Copy that. What's the status on backup?",
			time: "14:24",
			isUser: true,
		},
		{
			id: "msg-3",
			sender: "Officer Martinez",
			message: "ETA 3 minutes. Traffic is heavy on Techwood Drive.",
			time: "14:25",
			isUser: false,
		},
	]);

	// Pseudo-code: Available contacts relevant to the incident
	const availableContacts = [
		{
			id: "contact-1",
			name: "Fire Chief Williams",
			role: "Fire Department",
			priority: "high",
		},
		{
			id: "contact-2",
			name: "Officer Davis",
			role: "Police Department",
			priority: "medium",
		},
		{
			id: "contact-3",
			name: "Dr. Thompson",
			role: "Trauma Specialist",
			priority: "high",
		},
		{
			id: "contact-4",
			name: "EMT Rodriguez",
			role: "Ambulance Unit 7",
			priority: "medium",
		},
		{
			id: "contact-5",
			name: "Dispatcher Kim",
			role: "Traffic Control",
			priority: "low",
		},
		{
			id: "contact-6",
			name: "Supervisor Hayes",
			role: "EMS Coordinator",
			priority: "medium",
		},
	];

	// Auto-scroll chat to bottom when new messages arrive
	useEffect(() => {
		chatMessagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [chatMessages]);

	const swapWithCenter = (
		panelContent: PanelContent,
		setter: (content: PanelContent) => void
	) => {
		if (isSwapping) return; // Prevent multiple swaps at once
		setIsSwapping(true);

		const currentCenter = centerPanel;
		setCenterPanel(panelContent);
		setter(currentCenter);

		// Reset swap state after animation completes
		setTimeout(() => setIsSwapping(false), 50);
	};

	const toggleMute = (callId: string) => {
		setCalls((prevCalls) =>
			prevCalls.map((call) =>
				call.id === callId ? { ...call, isMuted: !call.isMuted } : call
			)
		);
	};

	const toggleCallSelection = (callId: string) => {
		setSelectedCalls((prev) => {
			const newSet = new Set(prev);
			if (newSet.has(callId)) {
				newSet.delete(callId);
			} else {
				newSet.add(callId);
			}
			return newSet;
		});
	};

	const toggleCallExpansion = (callId: string) => {
		setExpandedCalls((prev) => {
			const newSet = new Set(prev);
			if (newSet.has(callId)) {
				newSet.delete(callId);
			} else {
				newSet.add(callId);
			}
			return newSet;
		});
	};

	const mergeCalls = () => {
		if (selectedCalls.size < 2) return;
		// In a real implementation, this would merge the selected calls
		console.log("Merging calls:", Array.from(selectedCalls));
		setSelectedCalls(new Set());
	};

	const sendChatMessage = () => {
		if (!chatMessage.trim()) return;

		const newMessage = {
			id: `msg-${Date.now()}`,
			sender: "You",
			message: chatMessage,
			time: new Date().toLocaleTimeString("en-US", {
				hour: "2-digit",
				minute: "2-digit",
			}),
			isUser: true,
		};

		setChatMessages((prev) => [...prev, newMessage]);
		setChatMessage("");
	};

	const handleChatKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			sendChatMessage();
		}
	};

	const endCall = (callId: string) => {
		setCalls((prevCalls) => prevCalls.filter((call) => call.id !== callId));
	};

	const initiateCall = (contact: (typeof availableContacts)[0]) => {
		// Pseudo-code: In real implementation, this would:
		// 1. Connect to telephony system
		// 2. Initiate actual call
		// 3. Set up audio stream
		const timestamp = new Date().getTime();
		const newCall: Call = {
			id: `call-${timestamp}`,
			name: contact.name,
			role: contact.role,
			duration: "00:00",
			isMuted: false,
			isActive: true,
		};
		setCalls((prevCalls) => [...prevCalls, newCall]);
		setShowNewCallDialog(false);
		console.log(`Initiating call to ${contact.name} (${contact.role})`);
	};

	const handleOfficerClick = async (
		officer: PoliceOfficer,
		skipToggle: boolean = false
	) => {
		console.log(`Officer clicked on map: ${officer.name}`);

		// Toggle collapse if clicking the same officer (unless skipToggle is true)
		if (!skipToggle && selectedOfficer?.id === officer.id) {
			setSelectedOfficer(null);
			// Don't clear route info - keep the route visible even when collapsed
		} else {
			// Expand the officer details in the panel
			setSelectedOfficer(officer);

			// Fetch route information
			const route = await fetchRouteToIncident(
				officer.location,
				incidentLocation
			);
			if (route) {
				setRouteInfo({
					distance: route.distance,
					duration: route.duration,
				});
			} else {
				setRouteInfo(null);
			}
		}

		// Also make sure the dispatch panel is expanded so user can see the officer details
		setDispatchPanelExpanded(true);

		// Check if already in a call with this officer
		const existingCall = calls.find((call) => call.name === officer.name);
		if (existingCall) {
			console.log(`Already in call with ${officer.name}`);
			return;
		}

		// Initiate call with the officer
		const timestamp = new Date().getTime();
		const newCall: Call = {
			id: `call-${timestamp}`,
			name: officer.name,
			role: officer.role,
			duration: "00:00",
			isMuted: false,
			isActive: true,
		};

		setCalls([...calls, newCall]);
		console.log(`Call initiated with ${officer.name}`);
	};

	const handleOfficerRowClick = async (officer: PoliceOfficer) => {
		// Toggle collapse if clicking the same officer
		if (selectedOfficer?.id === officer.id) {
			setSelectedOfficer(null);
			// Don't clear route info - keep the route visible even when collapsed
			return;
		}

		setSelectedOfficer(officer);

		// Fetch route information
		const route = await fetchRouteToIncident(
			officer.location,
			incidentLocation
		);
		if (route) {
			setRouteInfo({
				distance: route.distance,
				duration: route.duration,
			});
		} else {
			setRouteInfo(null);
		}
	};

	const handleDispatchOfficer = async (
		officer: PoliceOfficer,
		e?: React.MouseEvent
	) => {
		if (e) {
			e.stopPropagation();
		}

		// Update officer's dispatched status
		setPoliceOfficers((prev) =>
			prev.map((o) =>
				o.id === officer.id ? { ...o, dispatched: true } : o
			)
		);

		// Select the officer to show their route
		setSelectedOfficer(officer);

		// Fetch and display route information
		const route = await fetchRouteToIncident(
			officer.location,
			incidentLocation
		);
		if (route) {
			setRouteInfo({
				distance: route.distance,
				duration: route.duration,
			});
		} else {
			setRouteInfo(null);
		}

		// Expand the panel
		setDispatchPanelExpanded(true);

		// Also create a call if not already in one (skip toggle logic)
		handleOfficerClick(officer, true);
	};

	const handleEndDispatch = (
		officer: PoliceOfficer,
		e?: React.MouseEvent
	) => {
		if (e) {
			e.stopPropagation();
		}

		// Update officer's dispatched status back to false
		setPoliceOfficers((prev) =>
			prev.map((o) =>
				o.id === officer.id ? { ...o, dispatched: false } : o
			)
		);

		// End any active call with this officer
		setCalls((prev) => prev.filter((call) => call.name !== officer.name));

		// Clear selection and route info
		if (selectedOfficer?.id === officer.id) {
			setSelectedOfficer(null);
			setRouteInfo(null);
		}
	};

	const getSeverityColor = (severity: string) => {
		switch (severity) {
			case "high":
				return "bg-d-rl";
			case "medium":
				return "bg-d-s";
			case "low":
				return "bg-d-p";
			default:
				return "bg-d-os2";
		}
	};

	const getSeverityLabel = (severity: string) => {
		switch (severity) {
			case "high":
				return "HIGH SEVERITY";
			case "medium":
				return "MEDIUM SEVERITY";
			case "low":
				return "LOW SEVERITY";
			default:
				return "UNKNOWN";
		}
	};

	const feedItems: FeedItem[] = [
		{
			id: "feed-1",
			type: "alert",
			time: "09:42 AM",
			title: "Critical Patient Status Alert",
			summary: "Male, ~45 years old, unresponsive, no pulse detected.",
			details:
				"Patient found collapsed in parking lot. Bystander initiated CPR immediately. AED requested and en route with first responder unit. Estimated arrival 3 minutes. Patient has no visible injuries. Bystander reports patient complained of chest pain moments before collapse.",
		},
		{
			id: "feed-2",
			type: "personnel",
			time: "09:40 AM",
			title: "Unit Dispatched",
			summary: "Ambulance Unit 12 dispatched to scene",
			details:
				"Unit 12 (Paramedics Johnson & Martinez) dispatched from Station 5. ETA 4 minutes. Unit equipped with advanced cardiac life support equipment. Traffic conditions: moderate.",
		},
		{
			id: "feed-3",
			type: "status",
			time: "09:39 AM",
			title: "911 Call Received",
			summary: "Emergency call reporting unconscious person",
			details:
				"Caller: Jane Smith (bystander)\nLocation: 123 Peachtree St, parking lot\nCaller confirms patient is breathing but unresponsive\nCaller training: CPR certified\nAdditional info: Multiple witnesses present",
		},
		{
			id: "feed-4",
			type: "media",
			time: "09:38 AM",
			title: "Scene Photo Uploaded",
			summary: "First responder uploaded scene assessment photo",
			details:
				"Photo shows clear access to patient. No hazards visible. Adequate space for emergency equipment deployment.",
			mediaType: "image",
		},
		{
			id: "feed-5",
			type: "status",
			time: "09:37 AM",
			title: "Traffic Advisory",
			summary: "Route optimization updated",
			details:
				"Alternative route suggested via North Avenue due to construction on Peachtree. Estimated time savings: 2 minutes. Traffic camera confirms clear path.",
		},
	];

	const toggleFeedItem = (itemId: string) => {
		setExpandedFeedItems((prev) => {
			const newSet = new Set(prev);
			if (newSet.has(itemId)) {
				newSet.delete(itemId);
			} else {
				newSet.add(itemId);
			}
			return newSet;
		});
	};

	const getFeedItemIcon = (type: FeedItemType) => {
		switch (type) {
			case "alert":
				return "🚨";
			case "status":
				return "📋";
			case "media":
				return "📷";
			case "personnel":
				return "👥";
			default:
				return "•";
		}
	};

	const getFeedItemColor = (type: FeedItemType) => {
		switch (type) {
			case "alert":
				return "border-d-rl";
			case "status":
				return "border-d-p";
			case "media":
				return "border-d-s";
			case "personnel":
				return "border-d-os2";
			default:
				return "border-d-os2";
		}
	};

	const suggestionItems = [
		{
			id: "sug-1",
			title: "Scene Safety Assessment",
			action: "Assess scene safety immediately",
			details:
				"Ensure the environment is safe for you, your team, and the patient before proceeding with any medical intervention. Look for potential hazards such as traffic, unstable structures, hazardous materials, or aggressive individuals.",
			context:
				"Similar incident at Bobby Dodd Stadium on 09/15/2024 resulted in responder injury due to inadequate scene assessment. Crowd size: 1,200+ attendees. Multiple security concerns identified post-incident.",
			source: "Incident Report #2024-0915-BDS | Safety Protocol Manual Section 3.2",
			priority: "high" as const,
		},
		{
			id: "sug-2",
			title: "Primary Survey (ABCs)",
			action: "Perform systematic primary survey",
			details:
				"Conduct a rapid assessment following the ABC protocol:\n• Airway: Check for obstruction, foreign bodies, or swelling\n• Breathing: Assess respiratory rate (normal: 12-20/min), effort, chest rise, and oxygen saturation\n• Circulation: Check pulse strength and rate, assess for bleeding, and evaluate skin perfusion (color, temperature, capillary refill)",
			context:
				"Historical data from 47 stadium incidents shows that systematic ABC assessment reduced time-to-treatment by 3.2 minutes on average. Protocol adherence correlates with 89% better outcomes in crowd-related emergencies.",
			source: "EMS Best Practices Database | Atlanta Metro Incident Analysis 2023-2024",
			priority: "high" as const,
		},
		{
			id: "sug-3",
			title: "Life-Threatening Stabilization",
			action: "Stabilize critical conditions",
			details:
				"Address immediate life threats in order of priority:\n1. Control severe bleeding using direct pressure, tourniquets if necessary\n2. Initiate CPR if no pulse detected (30:2 compression-ventilation ratio)\n3. Apply AED if available and indicated\n4. Manage airway obstruction with appropriate interventions",
			context:
				"Recent cardiac arrest case at Mercedes-Benz Stadium (08/22/2024) demonstrated importance of early AED deployment. Patient survived due to 4-minute response time. Venue now has 12 AED stations strategically placed.",
			source: "Case Study #2024-0822-MBS | AHA CPR Guidelines 2023",
			priority: "high" as const,
		},
		{
			id: "sug-4",
			title: "Oxygen Administration",
			action: "Provide supplemental oxygen if indicated",
			details:
				"Administer oxygen therapy when:\n• SpO₂ < 94% on room air\n• Patient shows signs of respiratory distress (increased work of breathing, use of accessory muscles)\n• Suspected cardiac or respiratory emergency\n• Altered mental status\nTarget SpO₂: 94-98% for most patients, 88-92% for COPD patients",
			context:
				"Analysis of 156 respiratory distress calls in crowded venues shows oxygen administration within first 5 minutes improved outcomes by 67%. Average SpO₂ improvement: 8-12% within 10 minutes of O₂ therapy.",
			source: "Respiratory Protocol Guidelines | Metro Atlanta EMS Performance Data Q3 2024",
			priority: "medium" as const,
		},
		{
			id: "sug-5",
			title: "Vital Signs Assessment",
			action: "Obtain complete vital signs baseline",
			details:
				"Systematically measure and document:\n• Blood Pressure (normal: 120/80 mmHg)\n• Heart Rate (normal adult: 60-100 bpm)\n• Respiratory Rate (normal: 12-20/min)\n• SpO₂ (target: >94%)\n• Temperature (normal: 97-99°F)\n• Glasgow Coma Scale (normal: 15)\nReassess every 5-15 minutes depending on patient stability.",
			context:
				"Trending vital signs from initial contact proved critical in 23 cases where patient condition deteriorated unexpectedly. Early detection of declining trends allowed for faster escalation and prevented 3 cardiac arrests.",
			source: "Vital Signs Monitoring Study | National Registry of EMTs 2024 Annual Report",
			priority: "medium" as const,
		},
	];

	const renderPanelContent = (
		content: PanelContent,
		showTitle: boolean = true,
		panelKey?: string,
		isCenter: boolean = false
	) => {
		const panelVariants = {
			initial: { opacity: 0, scale: 0.95 },
			animate: {
				opacity: 1,
				scale: 1,
				transition: {
					duration: 0.2,
					ease: [0.4, 0, 0.2, 1] as [number, number, number, number],
				},
			},
			exit: {
				opacity: 0,
				scale: 0.95,
				transition: {
					duration: 0.15,
					ease: [0.4, 0, 0.2, 1] as [number, number, number, number],
				},
			},
		};

		const getContent = () => {
			switch (content) {
				case "feed":
					return (
						<div className="flex flex-col h-full">
							{showTitle && (
								<p className="text-xs text-white/50 tracking-[-0.6px] mb-2.5">
									Feed and Chat
								</p>
							)}
							<div
								className={`border ${
									isCenter ? "border-d-p" : "border-d-os2"
								} rounded-[32px] flex-1 relative min-h-0 flex flex-col`}
							>
								{isCenter ? (
									<>
										{/* Chat Messages Area */}
										<div className="flex-1 overflow-y-auto p-6">
											<div className="flex flex-col gap-4">
												{/* Feed Items as System Messages */}
												{feedItems.map((item) => (
													<div
														key={item.id}
														className="flex gap-3"
													>
														<div className="flex-shrink-0 w-8 h-8 rounded-full bg-d-os2 flex items-center justify-center text-sm">
															{getFeedItemIcon(
																item.type
															)}
														</div>
														<div className="flex-1">
															<div className="flex items-center gap-2 mb-1">
																<p className="text-sm text-white/70 font-semibold tracking-[-0.6px]">
																	System
																</p>
																<span className="text-xs text-white/40 tracking-[-0.6px]">
																	{item.time}
																</span>
															</div>
															<div
																className={`border-l-4 ${getFeedItemColor(
																	item.type
																)} bg-white/5 rounded-lg px-4 py-3`}
															>
																<p className="text-sm text-white font-semibold tracking-[-0.6px] mb-1">
																	{item.title}
																</p>
																<p className="text-xs text-white/80 tracking-[-0.6px]">
																	{
																		item.summary
																	}
																</p>
															</div>
														</div>
													</div>
												))}

												{/* Chat Messages */}
												{chatMessages.map((msg) => (
													<div
														key={msg.id}
														className={`flex gap-3 ${
															msg.isUser
																? "flex-row-reverse"
																: ""
														}`}
													>
														<div className="flex-shrink-0 w-8 h-8 rounded-full bg-d-s flex items-center justify-center text-xs text-white font-semibold">
															{msg.isUser
																? "You"
																: msg.sender
																		.split(
																			" "
																		)[0]
																		.charAt(
																			0
																		)}
														</div>
														<div
															className={`flex-1 max-w-[75%] ${
																msg.isUser
																	? "flex flex-col items-end"
																	: ""
															}`}
														>
															<div className="flex items-center gap-2 mb-1">
																<p className="text-sm text-white/70 font-semibold tracking-[-0.6px]">
																	{msg.sender}
																</p>
																<span className="text-xs text-white/40 tracking-[-0.6px]">
																	{msg.time}
																</span>
															</div>
															<div
																className={`rounded-2xl px-4 py-3 ${
																	msg.isUser
																		? "bg-d-s text-white"
																		: "bg-white/5 text-white"
																}`}
															>
																<p className="text-sm tracking-[-0.6px]">
																	{
																		msg.message
																	}
																</p>
															</div>
														</div>
													</div>
												))}
												{/* Scroll anchor */}
												<div ref={chatMessagesEndRef} />
											</div>
										</div>

										{/* Chat Input */}
										<div className="border-t border-d-os2 p-4 bg-d-bg/50">
											<div className="flex gap-3 items-center">
												<input
													type="text"
													value={chatMessage}
													onChange={(e) =>
														setChatMessage(
															e.target.value
														)
													}
													onKeyPress={
														handleChatKeyPress
													}
													placeholder="Type a message..."
													className="flex-1 bg-white/5 border border-d-os2 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 tracking-[-0.6px] focus:outline-none focus:border-d-p transition-colors"
												/>
												<button
													onClick={sendChatMessage}
													disabled={
														!chatMessage.trim()
													}
													className="px-6 py-3 bg-d-s text-white rounded-xl text-sm font-semibold tracking-[-0.6px] hover:bg-d-s/80 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
												>
													Send
												</button>
											</div>
										</div>
									</>
								) : (
									<div className="absolute inset-0 p-6 flex flex-col">
										<p className="text-base text-white/50 tracking-[-0.8px] mb-4">
											Recent Updates
										</p>
										<div className="flex-1 flex flex-col gap-4 overflow-y-auto">
											{feedItems
												.slice(0, 3)
												.map((item) => (
													<div
														key={item.id}
														className={`border-l-4 ${getFeedItemColor(
															item.type
														)} bg-white/5 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors`}
													>
														<div className="flex items-center gap-2 mb-2">
															<span className="text-sm">
																{getFeedItemIcon(
																	item.type
																)}
															</span>
															<p className="text-sm text-white font-semibold tracking-[-0.8px]">
																{item.title}
															</p>
														</div>
														<p className="text-base text-white tracking-[-0.8px] whitespace-pre-wrap leading-relaxed">
															{item.summary}
														</p>
														<span className="text-xs text-white/40 tracking-[-0.6px] mt-2 block">
															{item.time}
														</span>
													</div>
												))}
										</div>
										<p className="text-xs text-white/30 tracking-[-0.6px] text-center mt-4">
											Click to view full feed
										</p>
									</div>
								)}
							</div>
						</div>
					);
				case "suggestions":
					return (
						<div className="flex flex-col gap-2.5 h-full">
							{showTitle && (
								<p className="text-xs text-white/50 tracking-[-0.6px]">
									Next Suggestions
								</p>
							)}
							<div
								className={`border ${
									isCenter ? "border-d-p" : "border-d-os2"
								} rounded-[32px] flex-1 overflow-hidden flex flex-col`}
							>
								{/* Pinned Header */}
								<div className="flex flex-col gap-2 p-6 pb-4 border-b border-d-os2/20">
									<p className="text-2xl text-white tracking-[-1.2px]">
										Next Suggestions
									</p>
									<p className="text-xs text-white/50 tracking-[-0.6px]">
										Click on any suggestion for detailed
										information and historical context
									</p>
								</div>
								{/* Scrollable Content */}
								<div className="flex-1 overflow-auto p-6">
									<div className="flex flex-col gap-3">
										{suggestionItems.map((suggestion) => (
											<div
												key={suggestion.id}
												onClick={() =>
													setSelectedSuggestion(
														suggestion
													)
												}
												className={`border rounded-2xl p-4 cursor-pointer transition-all hover:border-d-p hover:bg-d-p/5 ${
													suggestion.priority ===
													"high"
														? "border-d-rl/50 bg-d-rl/5"
														: suggestion.priority ===
														  "medium"
														? "border-d-s/50 bg-d-s/5"
														: "border-d-os2 bg-white/5"
												}`}
											>
												<div className="flex items-start justify-between gap-3 mb-2">
													<div className="flex-1">
														<div className="flex items-center gap-2 mb-1">
															<span
																className={`px-2 py-0.5 rounded text-xs font-semibold tracking-[-0.6px] ${
																	suggestion.priority ===
																	"high"
																		? "bg-d-rl/20 text-d-rl"
																		: suggestion.priority ===
																		  "medium"
																		? "bg-d-s/20 text-d-s"
																		: "bg-white/10 text-white/50"
																}`}
															>
																{suggestion.priority.toUpperCase()}
															</span>
														</div>
														<p className="text-base text-white font-semibold tracking-[-0.8px] mb-1">
															{suggestion.title}
														</p>
														<p className="text-sm text-white/70 tracking-[-0.6px]">
															{suggestion.action}
														</p>
													</div>
													<svg
														className="w-5 h-5 text-white/30 flex-shrink-0 mt-1"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															strokeLinecap="round"
															strokeLinejoin="round"
															strokeWidth={2}
															d="M9 5l7 7-7 7"
														/>
													</svg>
												</div>
											</div>
										))}
										<div className="pt-6 mt-6 border-t border-d-os2/20">
											<p className="text-xs text-white/50 tracking-[-0.6px]">
												Last Updated:{" "}
												{incident.lastUpdated}
											</p>
										</div>
									</div>
								</div>
							</div>
						</div>
					);
				case "summary":
					return (
						<div className="flex flex-col gap-2.5 h-full">
							{showTitle && (
								<p className="text-xs text-white/50 tracking-[-0.6px]">
									Summary
								</p>
							)}
							<div
								className={`border ${
									isCenter ? "border-d-p" : "border-d-os2"
								} rounded-[32px] flex-1 overflow-auto p-8 flex flex-col`}
							>
								<div className="flex flex-col gap-2 flex-1">
									<p className="text-2xl text-white tracking-[-1.2px]">
										Summary
									</p>
									<p className="text-sm text-white/80 tracking-[-0.6px] leading-relaxed mb-4">
										Incident overview and key findings based
										on current information.
									</p>
									<div className="space-y-4">
										<div className="border-l-4 border-d-p bg-white/5 rounded-lg p-4">
											<p className="text-xs text-white/50 tracking-[-0.6px] uppercase mb-2">
												Initial Assessment
											</p>
											<p className="text-sm text-white tracking-[-0.6px]">
												Multiple reports of disturbance
												at Bobby Dodd Stadium. Crowd
												estimated at 1,200+ attendees.
												Scene requires immediate safety
												assessment and systematic
												triage.
											</p>
										</div>
										<div className="border-l-4 border-d-s bg-white/5 rounded-lg p-4">
											<p className="text-xs text-white/50 tracking-[-0.6px] uppercase mb-2">
												Current Status
											</p>
											<p className="text-sm text-white tracking-[-0.6px]">
												{suggestionItems.length}{" "}
												priority actions identified.{" "}
												{
													policeOfficers.filter(
														(o) => o.dispatched
													).length
												}{" "}
												officers dispatched.{" "}
												{calls.length} active
												communication channels
												established.
											</p>
										</div>
									</div>
								</div>
								<div className="pt-4 mt-auto border-t border-d-os2/20">
									<p className="text-xs text-white/50 tracking-[-0.6px]">
										Last Updated: {incident.lastUpdated}
									</p>
								</div>
							</div>
						</div>
					);
				case "map":
					return (
						<div className="flex flex-col gap-2.5 h-full">
							{showTitle && (
								<p className="text-xs text-white/50 tracking-[-0.6px]">
									Map
								</p>
							)}
							<div
								className={`border ${
									isCenter ? "border-d-p" : "border-d-os2"
								} rounded-[32px] flex-1 overflow-hidden relative`}
							>
								<EmbeddedMap
									incidentLocation={incidentLocation}
									policeOfficers={policeOfficers}
									onOfficerClick={handleOfficerClick}
									hoveredOfficerId={hoveredOfficerId}
									selectedOfficerId={
										selectedOfficer?.id || null
									}
								/>

								{/* Dispatch Interface Overlay */}
								<div
									className={`absolute top-4 left-4 right-4 bg-d-bg/95 backdrop-blur-sm border border-d-os2 rounded-2xl shadow-xl transition-all duration-300 ${
										dispatchPanelExpanded || selectedOfficer
											? "p-4"
											: "p-3"
									}`}
									onMouseEnter={() =>
										setDispatchPanelExpanded(true)
									}
									onMouseLeave={() => {
										// Collapse the panel when cursor leaves
										setDispatchPanelExpanded(false);
										setSelectedOfficer(null);
										// Don't clear routeInfo - keep the route visible
										setHoveredOfficerId(null);
									}}
								>
									<div className="flex items-center justify-between">
										<p className="text-sm text-white font-semibold tracking-[-0.6px]">
											Available Officers
										</p>
										{!dispatchPanelExpanded &&
											!selectedOfficer && (
												<p className="text-xs text-white/40 tracking-[-0.6px]">
													Hover to expand
												</p>
											)}
									</div>

									{(dispatchPanelExpanded ||
										selectedOfficer) && (
										<div className="flex flex-col gap-2 max-h-96 overflow-y-auto mt-3">
											{policeOfficers
												.filter((officer) =>
													// If an officer is selected, only show that officer
													selectedOfficer
														? officer.id ===
														  selectedOfficer.id
														: true
												)
												.map((officer) => (
													<div
														key={officer.id}
														className={`flex items-start justify-between p-4 rounded-xl border transition-all cursor-pointer ${
															hoveredOfficerId ===
															officer.id
																? "border-d-p bg-d-p/10"
																: "border-d-os2 bg-white/5 hover:bg-white/10 hover:border-d-os2"
														}`}
														onMouseEnter={() =>
															setHoveredOfficerId(
																officer.id
															)
														}
														onMouseLeave={() =>
															setHoveredOfficerId(
																null
															)
														}
														onClick={() =>
															handleOfficerRowClick(
																officer
															)
														}
													>
														<div className="flex-1">
															<p className="text-sm text-white font-semibold tracking-[-0.6px]">
																{officer.name}
															</p>
															<p className="text-xs text-white/50 tracking-[-0.6px]">
																{officer.role}
															</p>
															{selectedOfficer?.id ===
																officer.id && (
																<div className="mt-2 pt-2 border-t border-white/10 space-y-1">
																	<p className="text-xs text-white/70 tracking-[-0.6px]">
																		<span className="text-white/50">
																			Badge:
																		</span>{" "}
																		{
																			officer.badge
																		}
																	</p>
																	<p className="text-xs text-white/70 tracking-[-0.6px]">
																		<span className="text-white/50">
																			Unit:
																		</span>{" "}
																		{
																			officer.unit
																		}
																	</p>
																	<p className="text-xs text-white/70 tracking-[-0.6px]">
																		<span className="text-white/50">
																			Rank:
																		</span>{" "}
																		{
																			officer.rank
																		}
																	</p>
																	<p className="text-xs text-white/70 tracking-[-0.6px]">
																		<span className="text-white/50">
																			Experience:
																		</span>{" "}
																		{
																			officer.yearsOfService
																		}{" "}
																		years
																	</p>
																	{routeInfo && (
																		<div className="mt-2 pt-2 border-t border-white/10 space-y-1">
																			<p className="text-xs text-purple-400 font-semibold tracking-[-0.6px]">
																				Route
																				to
																				Incident
																			</p>
																			<p className="text-xs text-white/70 tracking-[-0.6px]">
																				<span className="text-white/50">
																					Distance:
																				</span>{" "}
																				{(
																					routeInfo.distance /
																					1000
																				).toFixed(
																					2
																				)}{" "}
																				km
																			</p>
																			<p className="text-xs text-white/70 tracking-[-0.6px]">
																				<span className="text-white/50">
																					ETA:
																				</span>{" "}
																				{Math.ceil(
																					routeInfo.duration /
																						60
																				)}{" "}
																				min
																			</p>
																		</div>
																	)}
																</div>
															)}
														</div>
														<div className="flex flex-col gap-2">
															{!officer.dispatched ? (
																<button
																	className="px-3 py-1.5 rounded-lg text-xs font-semibold tracking-[-0.6px] transition-colors bg-d-s text-white hover:bg-d-s/80"
																	onClick={(
																		e
																	) => {
																		e.stopPropagation();
																		handleDispatchOfficer(
																			officer,
																			e
																		);
																	}}
																>
																	Dispatch
																</button>
															) : (
																<>
																	<div className="px-3 py-1.5 rounded-lg text-xs font-semibold tracking-[-0.6px] bg-purple-600 text-white text-center">
																		Dispatched
																	</div>
																	<button
																		className="px-3 py-1.5 rounded-lg text-xs font-semibold tracking-[-0.6px] transition-colors bg-red-600 text-white hover:bg-red-700"
																		onClick={(
																			e
																		) => {
																			e.stopPropagation();
																			handleEndDispatch(
																				officer,
																				e
																			);
																		}}
																	>
																		End
																		Dispatch
																	</button>
																</>
															)}
														</div>
													</div>
												))}
										</div>
									)}
								</div>
							</div>
						</div>
					);
				case "actions":
					return (
						<div className="flex flex-col gap-2.5 h-full">
							{showTitle && (
								<p className="text-xs text-white/50 tracking-[-0.6px]">
									Active Calls
								</p>
							)}
							<div
								className={`border ${
									isCenter ? "border-d-p" : "border-d-os2"
								} rounded-[32px] flex-1 min-h-0 p-4 flex flex-col`}
							>
								{isCenter ? (
									<>
										{/* Full View - Detailed Call Management */}
										<div className="flex items-center justify-between mb-4 flex-shrink-0">
											<p className="text-2xl text-white tracking-[-1.2px]">
												Active Calls ({calls.length})
											</p>
											<div className="flex gap-2">
												{selectedCalls.size > 1 && (
													<button
														onClick={mergeCalls}
														className="px-4 py-2 bg-d-p text-d-bg rounded-lg text-xs font-semibold tracking-[-0.6px] hover:bg-d-p/80 transition-colors"
													>
														Merge{" "}
														{selectedCalls.size}{" "}
														Calls
													</button>
												)}
												<button
													onClick={() =>
														setShowNewCallDialog(
															true
														)
													}
													className="px-4 py-2 bg-d-s text-white rounded-lg text-xs font-semibold tracking-[-0.6px] hover:bg-d-s/80 transition-colors"
												>
													+ New Call
												</button>
											</div>
										</div>
										<div className="flex-1 min-h-0 flex flex-col gap-3 overflow-y-auto">
											{calls.map((call) => {
												const isSelected =
													selectedCalls.has(call.id);
												const isExpanded =
													expandedCalls.has(call.id);
												return (
													<div
														key={call.id}
														className={`border rounded-2xl transition-all cursor-pointer ${
															isSelected
																? "border-d-p bg-d-p/10"
																: "border-d-os2 bg-white/5 hover:bg-white/10"
														} ${
															isExpanded
																? "p-4"
																: "p-3"
														}`}
														onClick={() =>
															toggleCallExpansion(
																call.id
															)
														}
													>
														{isExpanded ? (
															<>
																{/* Expanded View */}
																<div className="flex items-start justify-between mb-3">
																	<div className="flex items-start gap-3 flex-1">
																		<input
																			type="checkbox"
																			checked={
																				isSelected
																			}
																			onChange={() =>
																				toggleCallSelection(
																					call.id
																				)
																			}
																			onClick={(
																				e
																			) =>
																				e.stopPropagation()
																			}
																			className="mt-1 w-4 h-4 rounded border-d-os2 cursor-pointer"
																		/>
																		<div className="flex-1">
																			<div className="flex items-center gap-2 mb-1">
																				<p className="text-base text-white font-semibold tracking-[-0.8px]">
																					{
																						call.name
																					}
																				</p>
																				{policeOfficers.find(
																					(
																						o
																					) =>
																						o.name ===
																							call.name &&
																						o.dispatched
																				) && (
																					<span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs font-semibold tracking-[-0.6px]">
																						DISPATCHED
																					</span>
																				)}
																			</div>
																			<p className="text-xs text-white/50 tracking-[-0.6px]">
																				{
																					call.role
																				}
																			</p>
																		</div>
																	</div>
																	<span className="text-xs text-white/50 tracking-[-0.6px]">
																		{
																			call.duration
																		}
																	</span>
																</div>

																{/* Waveform Visualization */}
																<div className="bg-d-bg/50 rounded-lg p-3 mb-3 h-16 flex items-center gap-1">
																	{[
																		...Array(
																			40
																		),
																	].map(
																		(
																			_,
																			i
																		) => {
																			const height =
																				call.isMuted
																					? 4
																					: Math.random() *
																							60 +
																					  20;
																			return (
																				<div
																					key={
																						i
																					}
																					className={`flex-1 rounded-full transition-all ${
																						call.isMuted
																							? "bg-white/20"
																							: "bg-d-p"
																					}`}
																					style={{
																						height: `${height}%`,
																						animation:
																							call.isMuted
																								? "none"
																								: `pulse ${
																										Math.random() *
																											0.5 +
																										0.3
																								  }s ease-in-out infinite`,
																					}}
																				/>
																			);
																		}
																	)}
																</div>

																{/* Call Controls */}
																<div className="flex gap-2">
																	<button
																		onClick={(
																			e
																		) => {
																			e.stopPropagation();
																			toggleMute(
																				call.id
																			);
																		}}
																		className={`flex-1 px-3 py-2 rounded-lg text-xs font-semibold tracking-[-0.6px] transition-colors ${
																			call.isMuted
																				? "bg-d-rl text-white"
																				: "bg-white/10 text-white hover:bg-white/20"
																		}`}
																	>
																		{call.isMuted
																			? "🔇 Unmute"
																			: "🔊 Mute"}
																	</button>
																	<button
																		onClick={(
																			e
																		) => {
																			e.stopPropagation();
																			endCall(
																				call.id
																			);
																		}}
																		className="px-3 py-2 bg-d-rl/20 text-d-rl rounded-lg text-xs font-semibold tracking-[-0.6px] hover:bg-d-rl/30 transition-colors"
																	>
																		End Call
																	</button>
																</div>
															</>
														) : (
															<>
																{/* Compact View */}
																<div className="flex items-center justify-between">
																	<div className="flex items-center gap-2 flex-1">
																		<input
																			type="checkbox"
																			checked={
																				isSelected
																			}
																			onChange={() =>
																				toggleCallSelection(
																					call.id
																				)
																			}
																			onClick={(
																				e
																			) =>
																				e.stopPropagation()
																			}
																			className="w-4 h-4 rounded border-d-os2 cursor-pointer"
																		/>
																		<div className="flex-1 min-w-0">
																			<div className="flex items-center gap-2 mb-0.5">
																				<p className="text-sm text-white font-semibold tracking-[-0.6px] truncate">
																					{
																						call.name
																					}
																				</p>
																				{policeOfficers.find(
																					(
																						o
																					) =>
																						o.name ===
																							call.name &&
																						o.dispatched
																				) && (
																					<span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded text-[10px] font-semibold tracking-[-0.5px] flex-shrink-0">
																						DISPATCHED
																					</span>
																				)}
																			</div>
																			<p className="text-xs text-white/50 tracking-[-0.6px] truncate">
																				{
																					call.role
																				}
																			</p>
																		</div>
																	</div>
																	<div className="flex items-center gap-2 flex-shrink-0">
																		<span className="text-xs text-white/50">
																			{
																				call.duration
																			}
																		</span>
																		<button
																			onClick={(
																				e
																			) => {
																				e.stopPropagation();
																				toggleMute(
																					call.id
																				);
																			}}
																			className={`text-base px-2 py-1 rounded hover:bg-white/10 transition-colors ${
																				call.isMuted
																					? "opacity-50"
																					: ""
																			}`}
																			title={
																				call.isMuted
																					? "Unmute"
																					: "Mute"
																			}
																		>
																			{call.isMuted
																				? "🔇"
																				: "🔊"}
																		</button>
																	</div>
																</div>
															</>
														)}
													</div>
												);
											})}
										</div>
									</>
								) : (
									<>
										{/* Compact View - Call Status Grid */}
										<p className="text-base text-white/50 tracking-[-0.8px] mb-3 flex-shrink-0">
											Active Calls ({calls.length})
										</p>
										<div className="grid grid-cols-2 gap-2 flex-1 min-h-0 overflow-y-auto">
											{calls.map((call) => (
												<div
													key={call.id}
													className="border border-d-os2 rounded-xl p-3 bg-white/5 hover:bg-white/10 transition-colors flex flex-col justify-between"
												>
													<div>
														<div className="flex items-center gap-1 mb-1">
															<p className="text-sm text-white font-semibold tracking-[-0.6px] truncate">
																{
																	call.name.split(
																		" "
																	)[0]
																}
															</p>
															{policeOfficers.find(
																(o) =>
																	o.name ===
																		call.name &&
																	o.dispatched
															) && (
																<span className="px-1 py-0.5 bg-purple-500/20 text-purple-400 rounded text-[9px] font-semibold tracking-[-0.4px] flex-shrink-0">
																	DISP
																</span>
															)}
														</div>
														<p className="text-xs text-white/50 tracking-[-0.6px] mb-2">
															{call.role}
														</p>
													</div>
													<div className="flex items-center justify-between">
														<span className="text-xs text-white/50">
															{call.duration}
														</span>
														<span
															className={`text-sm ${
																call.isMuted
																	? "opacity-30"
																	: ""
															}`}
														>
															{call.isMuted
																? "🔇"
																: "🔊"}
														</span>
													</div>
												</div>
											))}
										</div>
										<p className="text-xs text-white/30 tracking-[-0.6px] text-center mt-3">
											Click to manage calls
										</p>
									</>
								)}

								{/* New Call Dialog */}
								{showNewCallDialog && isCenter && (
									<div className="absolute inset-0 bg-black/60 backdrop-blur-sm rounded-[32px] flex items-center justify-center animate-fadeIn z-50">
										<div className="bg-d-bg border border-d-p rounded-2xl p-6 w-[500px] max-h-[600px] flex flex-col shadow-2xl">
											<div className="flex items-center justify-between mb-4">
												<p className="text-2xl text-white tracking-[-1.2px]">
													New Call
												</p>
												<button
													onClick={() =>
														setShowNewCallDialog(
															false
														)
													}
													className="w-8 h-8 flex items-center justify-center text-white/50 hover:text-white transition-colors"
												>
													<svg
														width="24"
														height="24"
														viewBox="0 0 24 24"
														fill="none"
													>
														<path
															d="M18 6L6 18M6 6L18 18"
															stroke="currentColor"
															strokeWidth="2"
															strokeLinecap="round"
														/>
													</svg>
												</button>
											</div>

											<p className="text-sm text-white/50 tracking-[-0.6px] mb-4">
												Select a contact to call based
												on incident requirements:
											</p>

											<div className="flex-1 overflow-y-auto min-h-0">
												<div className="flex flex-col gap-2">
													{availableContacts.map(
														(contact) => {
															const getPriorityColor =
																(
																	priority: string
																) => {
																	switch (
																		priority
																	) {
																		case "high":
																			return "border-d-rl bg-d-rl/10";
																		case "medium":
																			return "border-d-p bg-d-p/10";
																		case "low":
																			return "border-d-os2 bg-white/5";
																		default:
																			return "border-d-os2 bg-white/5";
																	}
																};

															const getPriorityBadge =
																(
																	priority: string
																) => {
																	switch (
																		priority
																	) {
																		case "high":
																			return "🔴 High Priority";
																		case "medium":
																			return "🟡 Medium Priority";
																		case "low":
																			return "🟢 Available";
																		default:
																			return "";
																	}
																};

															return (
																<button
																	key={
																		contact.id
																	}
																	onClick={() =>
																		initiateCall(
																			contact
																		)
																	}
																	className={`border ${getPriorityColor(
																		contact.priority
																	)} rounded-xl p-4 text-left hover:bg-white/10 transition-all`}
																>
																	<div className="flex items-center justify-between mb-2">
																		<p className="text-base text-white font-semibold tracking-[-0.8px]">
																			{
																				contact.name
																			}
																		</p>
																		<span className="text-xs tracking-[-0.6px] text-white/70">
																			{getPriorityBadge(
																				contact.priority
																			)}
																		</span>
																	</div>
																	<p className="text-xs text-white/50 tracking-[-0.6px]">
																		{
																			contact.role
																		}
																	</p>
																</button>
															);
														}
													)}
												</div>
											</div>

											<div className="mt-4 pt-4 border-t border-white/10">
												<p className="text-xs text-white/30 tracking-[-0.6px] text-center">
													💡 Contacts are ranked by
													relevance to cardiac arrest
													incident
												</p>
											</div>
										</div>
									</div>
								)}
							</div>
						</div>
					);
			}
		};

		return (
			<AnimatePresence mode="wait">
				<motion.div
					key={panelKey || content}
					variants={panelVariants}
					initial="initial"
					animate="animate"
					exit="exit"
					className="h-full flex flex-col"
				>
					{getContent()}
				</motion.div>
			</AnimatePresence>
		);
	};

	return (
		<div className="h-screen bg-d-bg px-16 py-8 animate-fadeIn">
			<div className="flex flex-col gap-8 h-full">
				{/* Header */}
				<div className="flex items-center justify-between w-full animate-slideIn">
					<div className="flex flex-col gap-2.5">
						<div className="flex gap-2.5 items-center">
							<button
								onClick={onBack}
								className="w-6 h-6 flex items-center justify-center text-white hover:text-d-p transition-colors"
							>
								<svg
									width="24"
									height="24"
									viewBox="0 0 24 24"
									fill="none"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										d="M15 18L9 12L15 6"
										stroke="currentColor"
										strokeWidth="2"
										strokeLinecap="round"
										strokeLinejoin="round"
									/>
								</svg>
							</button>
							<div
								className={`w-2 h-2 rounded-full severity-indicator ${getSeverityColor(
									incident.severity
								)}`}
							/>
							<p className="text-base text-white tracking-[-0.8px]">
								{getSeverityLabel(incident.severity)}
							</p>
						</div>
						<p className="text-[64px] leading-none text-white tracking-[-3.2px] transition-all duration-300">
							PRIORITY: {incident.title}
						</p>
					</div>
					<div className="flex flex-col gap-2.5 items-end">
						<p className="text-base text-white tracking-[-0.8px]">
							Latest Notification
						</p>
						<p className="text-2xl text-d-p text-right tracking-[-1.2px]">
							Summary Updated at 8:54 PM
						</p>
					</div>
				</div>

				{/* Main Content */}
				<div
					className="flex gap-4 flex-1 min-h-0 animate-slideIn"
					style={{ animationDelay: "0.1s" }}
				>
					{/* Left Panel - Fixed (Non-Swappable) */}
					<div className="w-[248px] flex flex-col gap-2.5 h-full">
						{/* Nav Bar */}
						<div className="flex gap-2 items-center">
							<p
								className={`text-xs tracking-[-0.6px] cursor-pointer px-2 py-1 rounded ${
									leftPanelView === "suggestions"
										? "text-white bg-white/10"
										: "text-white/50 hover:text-white/80"
								}`}
								onClick={() => setLeftPanelView("suggestions")}
							>
								Next Suggestions
							</p>
							<p
								className={`text-xs tracking-[-0.6px] cursor-pointer px-2 py-1 rounded ${
									leftPanelView === "summary"
										? "text-white bg-white/10"
										: "text-white/50 hover:text-white/80"
								}`}
								onClick={() => setLeftPanelView("summary")}
							>
								Summary
							</p>
						</div>
						<div className="flex-1 min-h-0">
							{renderPanelContent(
								leftPanelView,
								false,
								`left-${leftPanelView}`,
								false
							)}
						</div>
					</div>

					{/* Center Panel */}
					<div className="flex-1 min-h-0">
						{renderPanelContent(
							centerPanel,
							true,
							`center-${centerPanel}`,
							true
						)}
					</div>

					{/* Right Panel */}
					<div className="flex flex-col gap-4 w-[450px] min-h-0">
						{/* Top */}
						<div
							className="flex-1 cursor-pointer hover:opacity-80 transition-opacity"
							onClick={() =>
								swapWithCenter(rightTopPanel, setRightTopPanel)
							}
						>
							{renderPanelContent(
								rightTopPanel,
								true,
								`right-top-${rightTopPanel}`,
								false
							)}
						</div>

						{/* Bottom */}
						<div
							className="flex-1 cursor-pointer hover:opacity-80 transition-opacity"
							onClick={() =>
								swapWithCenter(
									rightBottomPanel,
									setRightBottomPanel
								)
							}
						>
							{renderPanelContent(
								rightBottomPanel,
								true,
								`right-bottom-${rightBottomPanel}`,
								false
							)}
						</div>
					</div>
				</div>
			</div>

			{/* Suggestion Detail Popup */}
			{selectedSuggestion && (
				<div
					className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn"
					onClick={() => setSelectedSuggestion(null)}
				>
					<div
						className="bg-d-bg border border-d-p rounded-3xl p-8 max-w-3xl max-h-[80vh] overflow-y-auto m-4 shadow-2xl"
						onClick={(e) => e.stopPropagation()}
					>
						{/* Header */}
						<div className="flex items-start justify-between mb-6">
							<div className="flex-1">
								<div className="flex items-center gap-2 mb-2">
									<span
										className={`px-2 py-1 rounded text-xs font-semibold tracking-[-0.6px] ${
											selectedSuggestion.priority ===
											"high"
												? "bg-d-rl/20 text-d-rl"
												: selectedSuggestion.priority ===
												  "medium"
												? "bg-d-s/20 text-d-s"
												: "bg-white/10 text-white/50"
										}`}
									>
										{selectedSuggestion.priority.toUpperCase()}{" "}
										PRIORITY
									</span>
								</div>
								<h2 className="text-3xl text-white font-semibold tracking-[-1.5px] mb-2">
									{selectedSuggestion.title}
								</h2>
								<p className="text-lg text-d-p tracking-[-0.8px]">
									{selectedSuggestion.action}
								</p>
							</div>
							<button
								onClick={() => setSelectedSuggestion(null)}
								className="w-10 h-10 flex items-center justify-center text-white/50 hover:text-white transition-colors flex-shrink-0 ml-4"
							>
								<svg
									width="24"
									height="24"
									viewBox="0 0 24 24"
									fill="none"
								>
									<path
										d="M18 6L6 18M6 6L18 18"
										stroke="currentColor"
										strokeWidth="2"
										strokeLinecap="round"
									/>
								</svg>
							</button>
						</div>

						{/* Details Section */}
						<div className="mb-6">
							<h3 className="text-sm text-white/50 tracking-[-0.6px] uppercase mb-3">
								Detailed Instructions
							</h3>
							<div className="bg-white/5 border border-d-os2 rounded-2xl p-5">
								<p className="text-base text-white tracking-[-0.8px] whitespace-pre-line leading-relaxed">
									{selectedSuggestion.details}
								</p>
							</div>
						</div>

						{/* Context Section */}
						<div className="mb-6">
							<h3 className="text-sm text-white/50 tracking-[-0.6px] uppercase mb-3">
								Historical Context
							</h3>
							<div className="bg-d-s/10 border border-d-s/30 rounded-2xl p-5">
								<div className="flex items-start gap-3 mb-3">
									<svg
										className="w-5 h-5 text-d-s flex-shrink-0 mt-0.5"
										fill="currentColor"
										viewBox="0 0 24 24"
									>
										<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
									</svg>
									<p className="text-sm text-white tracking-[-0.6px] leading-relaxed">
										{selectedSuggestion.context}
									</p>
								</div>
							</div>
						</div>

						{/* Source Section */}
						<div className="border-t border-d-os2 pt-6">
							<h3 className="text-sm text-white/50 tracking-[-0.6px] uppercase mb-2">
								Source & References
							</h3>
							<div className="flex items-center gap-2">
								<svg
									className="w-4 h-4 text-white/30 flex-shrink-0"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										strokeLinecap="round"
										strokeLinejoin="round"
										strokeWidth={2}
										d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
									/>
								</svg>
								<p className="text-xs text-white/70 tracking-[-0.6px]">
									{selectedSuggestion.source}
								</p>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default DetailPage;
