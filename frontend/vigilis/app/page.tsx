"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { IncidentFrontend } from "./lib/types";
import { getAllIncidents } from "./lib/api";
import DetailPage from "./components/DetailPage";
import mapboxgl from "mapbox-gl";

// Mock incident locations in Atlanta area
const incidentLocations: Record<string, [number, number]> = {};

// Map ref declared outside component body scope is not valid; keep inside but before effects using it.
export default function Home() {
	// Map instance (declare first so effects can reference it)
	const [mapInstance, setMapInstance] = useState<mapboxgl.Map | null>(null);
	const [incidents, setIncidents] = useState<IncidentFrontend[]>([]);
	const [incidentsError, setIncidentsError] = useState<string | null>(null);
	const [activeIncidentId, setActiveIncidentId] = useState<string>("");
	const [expandedIncidentId, setExpandedIncidentId] = useState<string | null>(
		null
	);
	const [showDetail, setShowDetail] = useState(false);
	const [transitioningToDetail, setTransitioningToDetail] = useState(false);
	// Ghost cursor position and visibility for fade-out effect
	const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(
		null
	);
	const [showGhostCursor, setShowGhostCursor] = useState(false);

	useEffect(() => {
		if (transitioningToDetail) {
			document.body.style.cursor = "none";
		} else {
			document.body.style.cursor = "";
		}
		return () => {
			document.body.style.cursor = "";
		};
	}, [transitioningToDetail]);

	// Start ghost cursor fade when transition begins and we have a position
	useEffect(() => {
		if (transitioningToDetail && cursorPos) {
			// Schedule on next frame to avoid cascading render warning
			const raf = requestAnimationFrame(() => {
				setShowGhostCursor(true);
				const timeout = setTimeout(
					() => setShowGhostCursor(false),
					450
				); // fade duration + buffer
				// Cleanup timeout if dependencies change early
				return () => clearTimeout(timeout);
			});
			return () => cancelAnimationFrame(raf);
		}
	}, [transitioningToDetail, cursorPos]);

	// Track cursor position while not in transition
	useEffect(() => {
		const handleMove = (e: MouseEvent) => {
			// Avoid updating during detail view (not needed) but keep last position before transition
			if (!transitioningToDetail) {
				setCursorPos({ x: e.clientX, y: e.clientY });
			}
		};
		window.addEventListener("mousemove", handleMove);
		return () => window.removeEventListener("mousemove", handleMove);
	}, [transitioningToDetail]);

	const [hoveredIncidentId, setHoveredIncidentId] = useState<string | null>(
		null
	);

	const handleIncidentClick = useCallback(
		(incidentId: string) => {
			setActiveIncidentId(incidentId);
			setExpandedIncidentId((prev: string | null) =>
				prev === incidentId ? null : incidentId
			);

			// Smoothly fly to the incident's point of interest
			const loc = incidentLocations[incidentId];
			const map = mapInstance;
			if (map && loc) {
				const easeInOut = (t: number) =>
					t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
				map.flyTo({
					center: loc,
					zoom: 14.8,
					duration: 1200,
					easing: easeInOut,
					essential: true,
				});
			}
		},
		[mapInstance]
	);

	const handleBackClick = useCallback(() => {
		setShowDetail(false);
		setTransitioningToDetail(false);
		document.body.style.cursor = "";
	}, []);

	const handleIncidentHover = useCallback((incidentId: string) => {
		setHoveredIncidentId(incidentId);
	}, []);

	const handleIncidentLeave = useCallback(() => {
		setHoveredIncidentId(null);
	}, []);

	const activeIncident = incidents.find(
		(inc: IncidentFrontend) => inc.id === activeIncidentId
	);

	// Initial load of incidents
	useEffect(() => {
		let mounted = true;
		getAllIncidents()
			.then((data) => {
				if (!mounted) return;
				setIncidents(data);
				setIncidentsError(null);
				if (!activeIncidentId && data.length) {
					setActiveIncidentId(data[0].id);
				}
				// Populate location cache
				data.forEach((inc) => {
					const coords = inc.location?.geojson?.coordinates;
					if (Array.isArray(coords) && coords.length >= 2) {
						incidentLocations[inc.id] = [coords[0], coords[1]];
					}
				});
			})
			.catch((err) => {
				if (!mounted) return;
				console.error("Failed to load incidents", err);
				setIncidentsError(err.message || "Failed to load incidents");
			});
		return () => {
			mounted = false;
		};
	}, [activeIncidentId]);

	// Fade-in detail page once loaded
	if (showDetail) {
		// Ensure transition flag is cleared once detail is mounted
		if (transitioningToDetail) setTransitioningToDetail(false);
		return (
			<div className="relative h-screen w-screen bg-black animate-[detailFade_0.6s_ease-out_forwards]">
				<DetailPage
					incident={activeIncident}
					onBack={handleBackClick}
				/>
				<style jsx global>{`
					@keyframes detailFade {
						0% {
							opacity: 0;
							transform: translateY(8px);
						}
						100% {
							opacity: 1;
							transform: translateY(0);
						}
					}
				`}</style>
			</div>
		);
	}

	const getSeverityColor = (severity: string): string => {
		switch (severity) {
			case "high":
				return "#FF4444";
			case "medium":
				return "#FFA500";
			case "low":
				return "#4CAF50";
			default:
				return "#808080";
		}
	};

	const getSeverityLabel = (severity: string): string => {
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

	return (
		<div
			className={`relative h-screen overflow-hidden animate-fadeIn ${
				transitioningToDetail ? "cursor-none" : ""
			}`}
		>
			{/* Transition overlay */}
			{transitioningToDetail && !showDetail && (
				<div className="absolute inset-0 z-50 bg-black/5 cursor-none">
					<div className="absolute inset-0 bg-black animate-[toBlack_0.9s_ease-in_forwards]" />
					{/* No loading text per request */}
					{/* Ghost cursor element */}
					{showGhostCursor && cursorPos && (
						<div
							className="pointer-events-none fixed z-50"
							style={{
								left: cursorPos.x,
								top: cursorPos.y,
								transform: "translate(-50%, -50%)",
							}}
						>
							<div className="w-5 h-5 rounded-full border border-white/80 bg-white/20 backdrop-blur-sm animate-[fadeCursor_0.4s_ease-out_forwards]" />
						</div>
					)}
					<style jsx global>{`
						@keyframes toBlack {
							0% {
								background: rgba(0, 0, 0, 0);
							}
							60% {
								background: rgba(0, 0, 0, 0.85);
							}
							100% {
								background: rgba(0, 0, 0, 1);
							}
						}
						@keyframes fadeText {
							0% {
								opacity: 0;
								transform: translateY(4px);
							}
							100% {
								opacity: 1;
								transform: translateY(0);
							}
						}
						@keyframes fadeCursor {
							0% {
								opacity: 1;
								transform: translate(-50%, -50%) scale(1);
							}
							80% {
								opacity: 0.15;
								transform: translate(-50%, -50%) scale(0.85);
							}
							100% {
								opacity: 0;
								transform: translate(-50%, -50%) scale(0.7);
							}
						}
					`}</style>
				</div>
			)}
			{/* Full-Screen Map Background */}
			<div className="absolute inset-0">
				{incidentsError && incidents.length === 0 && (
					<div className="absolute top-4 left-4 z-20 bg-red-600/80 text-white text-xs px-3 py-2 rounded shadow">
						<span className="font-semibold">Error:</span>{" "}
						{incidentsError}
						<button
							onClick={() => setActiveIncidentId("")}
							className="ml-3 underline"
						>
							Retry
						</button>
					</div>
				)}
				{incidents.length > 0 && (
					<IncidentMapView
						incidents={incidents}
						incidentLocations={incidentLocations}
						activeIncidentId={activeIncidentId}
						hoveredIncidentId={hoveredIncidentId}
						onMapReady={setMapInstance}
						onMarkerClick={handleIncidentClick}
					/>
				)}
			</div>

			{/* Top Gradient Header with Branding */}
			<div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-black via-black/60 to-transparent z-10 pointer-events-none">
				<div className="p-8">
					<div className="flex items-center gap-2">
						{/* Eye icon */}
						<svg
							className="shrink-0"
							width="48"
							height="48"
							viewBox="0 0 800 800"
							fill="none"
							aria-hidden="true"
						>
							<defs>
								<style>
									{`.vigilis-eye-stroke{fill:none;stroke:#fff;stroke-linecap:round;stroke-linejoin:round;stroke-width:48px;}`}
								</style>
							</defs>
							<path
								className="vigilis-eye-stroke"
								d="M384.01,184.03c-128.99-2.18-262.4,87.97-346.27,180.29-8.8,9.77-13.68,22.46-13.68,35.62s4.87,25.84,13.68,35.62c82.05,90.37,215.07,182.59,346.27,180.38,131.2,2.21,264.26-90.02,346.37-180.38,8.8-9.77,13.68-22.46,13.68-35.62s-4.87-25.84-13.68-35.62c-83.97-92.32-217.38-182.46-346.37-180.29Z"
							/>
							<path
								className="vigilis-eye-stroke"
								d="M504,400c0,23.73-7.05,46.93-20.24,66.66-13.19,19.73-31.93,35.11-53.86,44.18-21.93,9.08-46.05,11.45-69.33,6.82-23.28-4.63-44.65-16.06-61.43-32.85-16.78-16.78-28.2-38.17-32.83-61.44-4.63-23.28-2.25-47.4,6.83-69.33,9.08-21.93,24.46-40.66,44.2-53.85,19.73-13.18,42.93-20.22,66.66-20.22,15.76,0,31.37,3.1,45.94,9.13,14.56,6.03,27.79,14.87,38.94,26.02,11.15,11.15,19.98,24.38,26.01,38.95,6.03,14.56,9.13,30.17,9.12,45.94Z"
							/>
						</svg>
						<h1 className="text-5xl leading-none text-white tracking-[-2px] font-light">
							Vigilis
						</h1>
					</div>
				</div>
			</div>

			{/* Floating Incident Cards (Frosted) */}
			<div className="absolute left-6 top-32 bottom-6 w-80 z-10 flex flex-col gap-3">
				<div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent space-y-3">
					{incidents.map((incident: IncidentFrontend) => {
						const isActive = activeIncidentId === incident.id;
						const isHovered = hoveredIncidentId === incident.id;
						const isExpanded = expandedIncidentId === incident.id;
						return (
							<div
								key={incident.id}
								className={`group relative flex flex-col rounded-2xl border backdrop-blur-xl transition-all duration-300 cursor-pointer overflow-hidden ${
									isExpanded
										? "border-white/20 bg-black/40"
										: isActive || isHovered
										? "border-white/15 bg-black/35"
										: "border-white/10 bg-black/30 hover:bg-black/35"
								}`}
								onClick={() => handleIncidentClick(incident.id)}
								onMouseEnter={() =>
									handleIncidentHover(incident.id)
								}
								onMouseLeave={handleIncidentLeave}
							>
								{/* Accent gradient overlay */}
								<div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.25),transparent_60%)]" />
								<div
									className={`relative flex flex-col gap-3 p-4 ${
										isExpanded ? "pb-5" : "pb-4"
									}`}
								>
									{/* Header Row */}
									<div className="flex items-center justify-between">
										<div className="flex items-center gap-2">
											<span
												className="relative inline-flex h-2.5 w-2.5"
												aria-label={getSeverityLabel(
													incident.severity
												)}
											>
												<span
													className="absolute inline-flex h-full w-full rounded-full opacity-70 animate-ping"
													style={{
														backgroundColor:
															getSeverityColor(
																incident.severity
															),
													}}
												/>
												<span
													className="relative inline-flex h-2.5 w-2.5 rounded-full"
													style={{
														backgroundColor:
															getSeverityColor(
																incident.severity
															),
													}}
												/>
											</span>
											<span className="text-[10px] text-white/70 tracking-wider font-medium">
												{getSeverityLabel(
													incident.severity
												)}
											</span>
										</div>
										<span className="text-[10px] text-white/60 font-medium">
											{incident.lastUpdated}
										</span>
									</div>

									{/* Title */}
									<h3 className="text-sm font-semibold text-white tracking-tight line-clamp-2">
										{incident.title}
									</h3>

									{/* Location */}
									<div className="flex items-center gap-2 text-[11px] text-white/60">
										<svg
											width="12"
											height="12"
											viewBox="0 0 24 24"
											fill="none"
											stroke="currentColor"
											strokeWidth="2"
											className="opacity-70"
										>
											<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
											<circle cx="12" cy="10" r="3" />
										</svg>
										<span>Atlanta, GA</span>
									</div>

									{/* Expanded Section */}
									{isExpanded && (
										<div className="mt-2 pt-3 border-t border-white/15 space-y-4 animate-fadeIn">
											{/* Summary */}
											<div className="space-y-1">
												<h4 className="text-[10px] font-semibold text-white/70 tracking-wider uppercase">
													Summary
												</h4>
												<p className="text-xs text-white/65 leading-relaxed">{`An ${getSeverityLabel(
													incident.severity
												).toLowerCase()} severity incident: ${
													incident.title
												}`}</p>
											</div>

											{/* Officers */}
											<div className="space-y-1">
												<h4 className="text-[10px] font-semibold text-white/70 tracking-wider uppercase">
													Officers Dispatched
												</h4>
												<div className="space-y-1.5">
													{[
														"Officer J. Smith - Unit 204",
														"Officer M. Johnson - Unit 156",
													].map((o) => (
														<div
															key={o}
															className="flex items-center gap-2 text-xs text-white/65"
														>
															<div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_0_2px_rgba(255,255,255,0.4)]" />
															<span>{o}</span>
														</div>
													))}
												</div>
											</div>

											{/* Suggestions */}
											<div className="space-y-1">
												<h4 className="text-[10px] font-semibold text-white/70 tracking-wider uppercase">
													Suggested Actions
												</h4>
												<ul className="space-y-1.5">
													{[
														"Request backup from nearby units",
														"Notify emergency medical services",
														"Establish perimeter control",
													].map((s) => (
														<li
															key={s}
															className="flex gap-2 text-xs text-white/65"
														>
															<span className="text-blue-400">
																•
															</span>
															<span>{s}</span>
														</li>
													))}
												</ul>
											</div>

											<button
												onClick={(e) => {
													e.stopPropagation();
													if (transitioningToDetail)
														return; // prevent double click
													setTransitioningToDetail(
														true
													);
													// Dramatic camera focus before switching
													const map = mapInstance;
													const loc =
														incidentLocations[
															incident.id
														];
													if (map && loc) {
														const easeInOut = (
															t: number
														) =>
															t < 0.5
																? 4 * t * t * t
																: 1 -
																  Math.pow(
																		-2 * t +
																			2,
																		3
																  ) /
																		2;
														map.flyTo({
															center: loc,
															zoom: 17.4,
															pitch: 72,
															duration: 900,
															easing: easeInOut,
															essential: true,
														});
													}
													setTimeout(() => {
														setShowDetail(true);
													}, 900); // overlay duration before showing detail
												}}
												className="w-full text-xs font-medium tracking-wide rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white py-2 transition-colors disabled:opacity-50"
												disabled={transitioningToDetail}
											>
												{transitioningToDetail
													? "Loading..."
													: "Open Full Incident"}
											</button>
										</div>
									)}
								</div>
							</div>
						);
					})}
				</div>
			</div>
		</div>
	);
}

// Separate component for the map view
interface IncidentMapViewProps {
	incidents: IncidentFrontend[];
	incidentLocations: Record<string, [number, number]>;
	activeIncidentId: string;
	hoveredIncidentId: string | null;
	onMapReady: (map: mapboxgl.Map) => void;
	onMarkerClick: (incidentId: string) => void;
}

function IncidentMapView({
	incidents,
	incidentLocations,
	activeIncidentId,
	hoveredIncidentId,
	onMapReady,
	onMarkerClick,
}: IncidentMapViewProps) {
	const mapContainerRef = useRef<HTMLDivElement>(null);
	const mapInstanceRef = useRef<mapboxgl.Map | null>(null);
	const markersRef = useRef<Record<string, mapboxgl.Marker>>({});
	const mapInitializedRef = useRef(false);

	// Function to create markers
	const createMarkers = useCallback(() => {
		const map = mapInstanceRef.current;
		if (!map) return;

		// Clear existing markers
		Object.values(markersRef.current).forEach((m) =>
			(m as mapboxgl.Marker).remove()
		);
		markersRef.current = {};

		// Create markers for each incident
		incidents.forEach((incident) => {
			const location = incidentLocations[incident.id];
			if (!location) return;

			// Create custom marker element
			const el = document.createElement("div");
			el.className = "incident-marker";
			el.style.width = "40px";
			el.style.height = "40px";
			el.style.cursor = "pointer";

			const getSeverityColor = (severity: string) => {
				switch (severity) {
					case "high":
						return "#FF4444";
					case "medium":
						return "#FFA500";
					case "low":
						return "#4CAF50";
					default:
						return "#808080";
				}
			};

			el.innerHTML = `
				<div class="marker-inner" style="
					width: 100%;
					height: 100%;
					background: ${getSeverityColor(incident.severity)};
					border: 3px solid white;
					border-radius: 50%;
					box-shadow: 0 0 20px ${getSeverityColor(incident.severity)}80;
					display: flex;
					align-items: center;
					justify-content: center;
					animation: pulse 2s infinite;
					transition: transform 0.3s ease;
				">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="white">
						<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
					</svg>
				</div>
			`;

			// Add hover effect to inner div
			const innerDiv = el.querySelector(".marker-inner") as HTMLElement;
			el.addEventListener("mouseenter", () => {
				if (innerDiv) innerDiv.style.transform = "scale(1.2)";
			});
			el.addEventListener("mouseleave", () => {
				if (innerDiv) innerDiv.style.transform = "scale(1)";
			});

			// Make marker focusable and clickable (mouse + keyboard)
			el.setAttribute("tabindex", "0");
			el.setAttribute("role", "button");
			el.setAttribute("aria-label", `Focus incident ${incident.title}`);
			// Click handler: stop propagation and trigger zoom
			el.addEventListener("click", (e: MouseEvent) => {
				e.stopPropagation();
				onMarkerClick(incident.id);
				const map = mapInstanceRef.current;
				if (map) {
					const easeInOut = (t: number) =>
						t < 0.5
							? 4 * t * t * t
							: 1 - Math.pow(-2 * t + 2, 3) / 2;
					map.flyTo({
						center: location,
						zoom: 14.8,
						duration: 1200,
						easing: easeInOut,
						essential: true,
					});
				}
			});
			// Keyboard handler for accessibility (Enter/Space)
			el.addEventListener("keydown", (e: KeyboardEvent) => {
				if (e.key === "Enter" || e.key === " ") {
					e.preventDefault();
					onMarkerClick(incident.id);
					const map = mapInstanceRef.current;
					if (map) {
						const easeInOut = (t: number) =>
							t < 0.5
								? 4 * t * t * t
								: 1 - Math.pow(-2 * t + 2, 3) / 2;
						map.flyTo({
							center: location,
							zoom: 14.8,
							duration: 1200,
							easing: easeInOut,
							essential: true,
						});
					}
				}
			});

			const marker = new mapboxgl.Marker({ element: el })
				.setLngLat(location)
				.addTo(map);

			markersRef.current[incident.id] = marker;
		});
	}, [incidents, incidentLocations, onMarkerClick]);

	useEffect(() => {
		if (!mapContainerRef.current || mapInitializedRef.current) return;

		const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
		if (!token) {
			console.error("Mapbox token not found");
			return;
		}

		mapboxgl.accessToken = token;
		mapInitializedRef.current = true;

		// Initialize map
		const map = new mapboxgl.Map({
			container: mapContainerRef.current,
			style: "mapbox://styles/mapbox/dark-v11",
			center: [-84.388, 33.76],
			zoom: 12.6,
			pitch: 55,
			bearing: 0,
		});

		map.on("load", () => {
			mapInstanceRef.current = map;
			onMapReady(map);

			// Keep default mapbox dark-v11 styling (no overrides)

			// Add 3D buildings
			if (!map.getLayer("3d-buildings")) {
				map.addLayer({
					id: "3d-buildings",
					source: "composite",
					"source-layer": "building",
					filter: ["==", "extrude", "true"],
					type: "fill-extrusion",
					minzoom: 13,
					paint: {
						"fill-extrusion-color": "#1a1a1a",
						"fill-extrusion-height": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0,
							13.05,
							["get", "height"],
						],
						"fill-extrusion-base": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0,
							13.05,
							["get", "min_height"],
						],
						"fill-extrusion-opacity": 0.6,
					},
				});
			}

			// Create initial markers
			createMarkers();
		});

		// Cleanup
		return () => {
			Object.values(markersRef.current).forEach((m) =>
				(m as mapboxgl.Marker).remove()
			);
			markersRef.current = {};
			mapInitializedRef.current = false;
			map.remove();
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []); // Empty dependency array - only run once

	// Effect to update markers when incidents change
	useEffect(() => {
		const map = mapInstanceRef.current;
		if (!map || !map.loaded()) return;

		createMarkers();
	}, [createMarkers]);

	// Update marker styles based on active/hovered state
	useEffect(() => {
		Object.entries(markersRef.current).forEach(([incidentId, marker]) => {
			const el = (marker as mapboxgl.Marker).getElement();
			const innerDiv = el.querySelector(".marker-inner") as HTMLElement;
			if (!innerDiv) return;

			if (
				incidentId === activeIncidentId ||
				incidentId === hoveredIncidentId
			) {
				innerDiv.style.transform = "scale(1.3)";
				el.style.zIndex = "1000";
			} else {
				innerDiv.style.transform = "scale(1)";
				el.style.zIndex = "1";
			}
		});
	}, [activeIncidentId, hoveredIncidentId]);

	return (
		<>
			<div ref={mapContainerRef} className="w-full h-full" />
			<style jsx global>{`
				@keyframes pulse {
					0%,
					100% {
						opacity: 1;
					}
					50% {
						opacity: 0.7;
					}
				}
			`}</style>
		</>
	);
}
